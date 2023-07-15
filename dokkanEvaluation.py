import pickle
from dokkanUnit import Unit, turnMax
import numpy as np
import pandas as pd
from scipy.stats import truncnorm
from dokkanAccount import User
nSclarAttributes = 3
nAttributes = 9
copiesMax = 5
meanPeakTurn = 3.471591
meanPeakTurnStd = 1.857813
nUnits = len(User)
def logisticMap(x,x_max,L=100,d=1,x_min=-7):
    L = L + d
    x_0=(x_min+x_max)/2
    k = 2*np.log((L-d)/d)/(x_max-x_min)
    return L/(1+np.exp(-k*(x-x_0)))
HP_dupes = ['55%','69%','79%','90%','100%']
HP_builds = [['ATT','ADD','CRT'],['ATT','ADD','DGE'],['ATT','CRT','DGE'],['ATT','CRT','ADD'],['DEF','ADD','CRT'],['DEF','ADD','DGE'],['DEF','CRT','DGE'],['DEF','CRT','ADD'],['DEF','DGE','CRT'],['DEF','DGE','ADD'],['ADD','ADD','CRT'],['ADD','ADD','DGE'],['CRT','CRT','DGE'],['CRT','CRT','ADD'],['DGE','DGE','CRT'],['ATT','DGE','ADD']]
attributes = ['LeaderSkill','SBR','Useability','Healing','Support','APT','normalDefence','saDefence','slot1Ability']
def save_object(obj, filename):
    with open(filename, 'wb') as outp:  # Overwrites any existing file.
        pickle.dump(obj, outp, pickle.HIGHEST_PROTOCOL)
    outp.close()
def getAttributes(unit):
    attributes = np.zeros((turnMax,nAttributes))
    for turn in range(turnMax):
        for j in range(nAttributes):
            if j < 3:
                attributes[turn,j] = unit.attributes[j]
            else:
                attributes[turn,j] = unit.attributes[j][turn]
    return attributes
def summaryStats(attributeValues):
    # Compute means and stds for each attribute
    means = np.zeros((turnMax,nAttributes))
    stds = np.zeros((turnMax,nAttributes))
    for turn in range(turnMax):
        for j in range(nAttributes):
            means[turn,j] = np.mean(attributeValues[:,turn,j])
            stds[turn,j] = np.std(attributeValues[:,turn,j])
    return [means,stds]

def normalizeUnit(unit,means,stds):
    # Normalise attributes and save unit objects in pkl files
    normalisedAttributes = np.zeros((turnMax,nAttributes))
    for j in range(nAttributes):
        normalisedAttributes[:,j] = (unit.attributes[j]-means[:,j])/stds[:,j]
        unit.attributes[j] = normalisedAttributes[:,j]
    save_object(unit,'C:/Users/Tyler/Documents/DokkanAnalysis/DokkanUnits/'+HP_dupes[unit.nCopies-1]+'/unit_'+unit.ID+'.pkl')
    return normalisedAttributes
def writeSummary(units,attributeValues,evaluations):
    # Create Attribute data frame for each turn
    for nCopies in range(1,copiesMax+1):
        df1 = pd.DataFrame(data=[[str(i+1), units[nCopies-1][i].kit.name, units[nCopies-1][i].kit.type, evaluations[i,nCopies-1]] for i in range(nUnits)],columns=['ID','Name','Type','Evaluation'])
        weightedSums = np.zeros((nUnits,nAttributes))
        for turn in range(turnMax):
            weightedSums = np.add(weightedSums,overallTurnWeights[turn]*attributeValues[:,turn,:,nCopies-1])
        with pd.ExcelWriter('DokkanUnits/'+HP_dupes[nCopies-1]+'/unitSummary.xlsx') as writer:
            df = (df1.join(pd.DataFrame(data=weightedSums,columns=attributes)).set_index('ID'))
            df.to_excel(writer, sheet_name='Overall')
            for turn in range(turnMax):
                df = df1.join(pd.DataFrame(data=attributeValues[:,turn,:,nCopies-1],columns=attributes)).set_index('ID')
                df.to_excel(writer, sheet_name='Turn '+str(turn+1))

class Evaluator:
    def __init__(self,turnWeights,attributeWeights):
        self.turnWeights = turnWeights
        self.attributeWeights = attributeWeights
        self.normaliseWeights()
    def normaliseWeights(self):
        self.turnWeights = self.turnWeights/np.sqrt((self.turnWeights**2).sum())
        self.attributeWeights = self.attributeWeights/np.sqrt((self.attributeWeights**2).sum())
    def evaluate(self,unit):
        score = 0.0
        for i,attribute in enumerate(unit.attributes):
            score += self.attributeWeights[i]*np.dot(self.turnWeights,attribute)
        return score
#overallTurnWeights = np.array([0.8,1.3,2.1,2.1,1.3,0.8,0.5,0.3,0.2,0.1])
a, b = (1 - meanPeakTurn) / meanPeakTurnStd, (99 - meanPeakTurn) / meanPeakTurnStd
turnDistribution = truncnorm(a,b,meanPeakTurn,meanPeakTurnStd)
#x = np.linspace(1,turnMax,100)
#y = turnDistribution.pdf(x)
#plt.plot(x,y)
#plt.show()

overallTurnWeights = turnDistribution.cdf(np.arange(2,turnMax+2))-turnDistribution.cdf(np.arange(1,turnMax+1))
# overallAttributeWeights = np.array([7,1,4,1,7,3,8.6,10,8.5,3.6]) Previous version tured weights
#overallAttributeWeights = np.array([8,0.5,7,2,3,12,12,10,7])
overallAttributeWeights = np.array([5,0.5,4,1.5,4,10,8,8,4])
overallEvaluator = Evaluator(overallTurnWeights,overallAttributeWeights)

reCalc = True
analyseHP = False
if reCalc:
    attributeValues = np.zeros((nUnits,turnMax,nAttributes,copiesMax))
    units = [[None]*nUnits for i in range(copiesMax)]
    evaluations = np.zeros((nUnits,copiesMax))
    for ID in range(1,nUnits+1):
        print(ID)
        units[-1][ID-1] = Unit(ID,copiesMax,User[ID-1][0],User[ID-1][1],User[ID-1][2])
        attributeValues[ID-1,:,:,-1] = getAttributes(units[-1][ID-1])
    [rainbowMeans,rainbowStds] = summaryStats(attributeValues[:,:,:,-1])
    for ID in range(1,nUnits+1):
        attributeValues[ID-1,:,:,-1] = normalizeUnit(units[-1][ID-1],rainbowMeans,rainbowStds)
        evaluations[ID-1][-1] = overallEvaluator.evaluate(units[-1][ID-1])
    if analyseHP:
        for ID in range(1,nUnits+1):
            best_HP = None
            best_eval = evaluations[ID-1][-1]
            for i,HP_build in enumerate(HP_builds):
                HP_unit = Unit(ID,copiesMax,HP_build[0],HP_build[1],HP_build[2])
                normalizeUnit(HP_unit,rainbowMeans,rainbowStds)
                HP_evaluation = overallEvaluator.evaluate(HP_unit)
                if HP_evaluation > best_eval:
                    best_HP = i
                    best_eval = HP_evaluation
            if (best_HP == None):
                print(ID,"default HP",HP_unit.kit.name)
            else:
                print(ID,HP_builds[best_HP],HP_unit.kit.name)
    for ID in range(1,nUnits+1):
        print(ID)
        for nCopies in range(1,copiesMax):
            units[nCopies-1][ID-1] = Unit(ID,nCopies,User[ID-1][0],User[ID-1][1],User[ID-1][2])
            attributeValues[ID-1,:,:,nCopies-1] = normalizeUnit(units[nCopies-1][ID-1],rainbowMeans,rainbowStds)
            evaluations[ID-1][nCopies-1] = overallEvaluator.evaluate(units[nCopies-1][ID-1])
    maxEvaluation = max(evaluations[:,-1])
    evaluations = logisticMap(evaluations,maxEvaluation)
    writeSummary(units,attributeValues,evaluations)

scores = [0.0]*nUnits
units = [None]*nUnits
for i in range(nUnits):
    pkl = open('C:/Users/Tyler/Documents/DokkanAnalysis/DokkanUnits/100%/unit_'+str(i+1)+'.pkl','rb')
    units[i] = pickle.load(pkl)
    pkl.close()
    scores[i] = overallEvaluator.evaluate(units[i])
ranking = np.flip(np.argsort(scores))
for rank in ranking:
    print(units[rank].kit.name,units[rank].kit.type)
'''
nDataUnits = len(Units)
weightedSums = np.zeros((nDataUnits,nAttributes))
for turn in range(turnMax):
    dfDict = pd.read_excel('C:/Users/Tyler/Documents/DokkanAnalysis/DokkanUnits/100%/unitSummary.xlsx','Turn '+str(turn+1))
    for i in range(nDataUnits):
        weightedSums[i,:] = np.add(weightedSums[i,:],overallTurnWeights[turn]*dfDict.values[Units[i][4]-1][4:])
X = pd.DataFrame(data=weightedSums,columns=['Leader Skill','SBR','Useability','Healing','Support','APT','normalDefence','saDefence','slot1'])
y = (np.array(Units)[:,3]).astype('float64')

#from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.4, random_state=1)

# Try Linear Model-ALthough most features are highly non-linear seems to be doing ok, since those features have low weights
reg = linear_model.LinearRegression()
cv_results = cross_validate(reg,X,y,cv=5,return_estimator=True)
coeffs = np.array([model.coef_ for model in cv_results['estimator']])
meancoeffs = np.mean(coeffs,axis=0)
print(meancoeffs)
reg.fit(X_train, y_train)

print('Coefficients: ', reg.coef_)
# variance score: 1 means perfect prediction
print('Variance score: {}'.format(reg.score(X_test, y_test)))
  
# plot for residual error
  
## setting plot style
plt.style.use('fivethirtyeight')
  
## plotting residual errors in training data
plt.scatter(reg.predict(X_train), reg.predict(X_train) - y_train,
            color = "green", s = 10, label = 'Train data')
  
## plotting residual errors in test data
plt.scatter(reg.predict(X_test), reg.predict(X_test) - y_test,
            color = "blue", s = 10, label = 'Test data')
  
## plotting legend
plt.legend(loc = 'upper right')
  
## plot title
plt.title("Residual errors")
  
## method call for showing the plot
plt.show()

# Try Decision Tree
regressor = DecisionTreeRegressor(random_state=0)
print(cross_val_score(regressor, X, y, cv=10))

# Try XGBoost

m = XGBRegressor(
    max_depth = 2,
    gamma=2,
    eta=0.8,
    reg_alpha=0.5,
    reg_lambda=0.5
)
m.fit(X_train, y_train)
score = m.score(X_train, y_train)  
print("Training score: ", score)'''