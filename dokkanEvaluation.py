import pickle
import openpyxl
from dokkanUnit import Unit
import numpy as np
import pandas as pd
from sklearn import linear_model, metrics
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import cross_validate
turnMax = 10
nSclarAttributes = 3
nAttributes = 10
nUnits = 48
copiesMax = 5
User = [['A','C','D',16], # TEQLR SS Goku
    ['A','C','D',14], # PHYLR SS4s
    ['A','C','D',15], # TEQLR Gods
    ['A','C','D',13], # INTLR Vegeta & Trunks
    ['A','C','D',7], # PHY Goku Youth
    ['A','C','D',8], # AGLLR SSs
    ['C','A','A',17], # STRLR Final Form Cooler
    ['A','C','D',9], # STR Gamma 1
    ['A','C','A',11], # AGL Gamma 2
    ['C','A','D',12], # PHYLR Metal Cooler
    ['C','A','A',3], # TEQ Androids 17&18
    ['C','A','D',1], # AGLLR Golden Frieza
    ['A','C','A',21], # AGLLR MUI Goku
    ['A','C','D',19], # STR SS Goku/Gohan
    ['C','A','D',18], # TEQ Pan
    ['A','C','D',6], # INTLR Fusion Zamasu
    ['A','D','D',2], # INT Cheelai
    ['A','C','D',20], # STR Cooler
    ['A','C','D',24], # TEQ Ultimate Gohan
    ['A','C','D',26], # AGL Captain Ginyu
    ['C','A','D',22], # PHYLR Super Janemba
    ['A','C','D',30], # STR Namek Goku
    ['C','A','D',29], # INTLR Super Vegito
    ['A','C','D',27], # AGLLR SS4 Goku
    ['C','A','D',28], # STRLR SS4 Vegeta
    ['C','A','D',25], # AGLLR Future Gohan & Trunks
    ['A','C','D',10], # INT 19&20
    ['A','C','D',31], # TEQ Kale & Caulifla
    ['A','C','D',5], # AGL 1st Form Cell
    ['C','A','D',23], # AGL Hacchan
    ['A','C','D',4], # STR Piccolo (Banner)
    ['A','C','D',19], # INT Limit Breaker Goku
    ['C','A','D',18], # PHY Limit Breaker Vegeta
    ['C','A','D',6], # STR Super Hearts
    ['C','D','D',2], # INT SS4 Gohan
    ['A','C','D',20], # STR SS4 Bardock
    ['A','C','D',24], # STR Supreme Kai of Time (Brainwashed)
    ['A','C','D',26], # Robelu
    ['C','A','D',22], # Golden Metal Cooler
    ['A','C','D',30], # Janemba (Reconstructed)
    ['A','C','D',29], # PHY Super Saiyan Cumber
    ['A','D','D',27], # TEQ Supreme Opai of Time
    ['A','C','D',28], # PHY SS3 Vegeta (Xeno)
    ['A','C','D',25], # STR SS3 Goku (Xeno)
    ['A','C','D',10], # INT Super Fu
    ['A','C','D',31], # Golden Cooler
    ['A','C','D',5], # STR Sealas
    ['C','A','D',23], # TEQ Great Saiyaman 3
]
def logisticMap(x,x_max,L=100,d=5,x_min=-9):
    x_0=(x_min+x_max)/2
    k = 2*np.log((L-d)/d)/(x_max-x_min)
    return L/(1+np.exp(-k*(x-x_0)))
HP_dupes = ['55%','69%','79%','90%','100%']
attributes = ['LeaderSkill','SBR','Useability','Healing','Special','Support','APT','normalDefence','saDefence','slot1Ability']
def OverallTurnWeights():
    overallTurnWeights = [0.0]*turnMax
    for turn in range(1,turnMax+1):
        if(turn < 3):
            overallTurnWeights[turn-1] = 2.5-0.3*turn
        elif(turn<7):
            overallTurnWeights[turn-1] = 4.5-0.6*turn
        else:
            overallTurnWeights[turn-1] = 0.05*turn
    return np.array(overallTurnWeights)
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
        with pd.ExcelWriter('DokkanUnits/'+HP_dupes[nCopies-1]+'/unitSummary.xlsx') as writer:
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
#overallTurnWeights = OverallTurnWeights()
overallTurnWeights = np.array([2.2,2,2.7,2.7,2,1.5,1,0.5,0.6,0.7])
overallAttributeWeights = np.array([8,2,4,1,6,4,8,1,9,5])
overallEvaluator = Evaluator(overallTurnWeights,overallAttributeWeights)

reCalc = False
if reCalc:
    attributeValues = np.zeros((nUnits,turnMax,nAttributes,copiesMax))
    units = [[None]*nUnits for i in range(copiesMax)]
    evaluations = np.zeros((nUnits,copiesMax))
    for ID in range(1,nUnits+1):
        units[-1][ID-1] = Unit(ID,copiesMax,User[ID-1][0:2],User[ID-1][2])
        attributeValues[ID-1,:,:,-1] = getAttributes(units[-1][ID-1])
    [rainbowMeans,rainbowStds] = summaryStats(attributeValues[:,:,:,-1])
    for ID in range(1,nUnits+1):
        attributeValues[ID-1,:,:,-1] = normalizeUnit(units[-1][ID-1],rainbowMeans,rainbowStds)
        evaluations[ID-1][-1] = overallEvaluator.evaluate(units[-1][ID-1])
        maxEvaluation = max(evaluations[:,-1])
        for nCopies in range(1,copiesMax):
            units[nCopies-1][ID-1] = Unit(ID,nCopies,User[ID-1][0:2],User[ID-1][2])
            attributeValues[ID-1,:,:,nCopies-1] = normalizeUnit(units[nCopies-1][ID-1],rainbowMeans,rainbowStds)
            evaluations[ID-1][nCopies-1] = overallEvaluator.evaluate(units[nCopies-1][ID-1])
    evaluations = logisticMap(evaluations,maxEvaluation)
    writeSummary(units,attributeValues,evaluations)


# [leaderSkill,SBR,useability,healing,special,support,apt,normalDefence,saDefencePostSuper,slot1Ability]
SBRturnWeights = np.array([5,1,0,0,0,0,0,0,0,0])
SBRattributeWeights = np.array([0,5,0,1,4,2,3,1,5,4])
tunedSBRattributeWeights = np.array([0,5,0,1,1,2,4,0,4,3])
SBREvalutator = Evaluator(SBRturnWeights,tunedSBRattributeWeights)

# 1= Negligible
# 2=
# 3=
# 4= Sometimes useful
# 5=
# 6=
# 7= Usually useful
# 8=
# 9=
# 10= Must have

scores = [0.0]*nUnits
units = [None]*nUnits
for i in range(nUnits):
    pkl = open('C:/Users/Tyler/Documents/DokkanAnalysis/DokkanUnits/100%/unit_'+str(i+1)+'.pkl','rb')
    units[i] = pickle.load(pkl)
    pkl.close()
    scores[i] = overallEvaluator.evaluate(units[i])
ranking = np.flip(np.argsort(scores))
for rank in ranking:
    print(units[rank].kit.name)

# SBR
#  Just use turn 1 to limit features so doesn't overfit (can tell was doing this with two turns as some coefficients were negative)
#  Gives 1+1*7=8 features, tried with 30 instances

# Red Zone
# Use 6 turns -> gives 1+6*7=43 features, assuming linear try ~150 instances

# FL
# Use 10 turns -> gives 0+10*7=70 featues, assuming linear try ~250 instances

# Overall
# Use 10 turns -> gives 3+10*7=73 features, assuming linear try ~275 instances, pretty much whole current excel database

'''
SBRTurns = 1
dfDict = pd.read_excel('unitSummary.xlsx',list(range(SBRTurns)))
dfList = [None]*SBRTurns
for turn in range(1,SBRTurns+1):
    dfList[turn-1] = dfDict[turn-1].rename(columns={"Healing": "Healing_"+str(turn),"Special": "Special_"+str(turn),"Support": "Support_"+str(turn),"APT": "APT_"+str(turn),"normalDefence": "normalDefence_"+str(turn),"saDefence": "saDefence_"+str(turn),"slot1Ability": "slot1Ability_"+str(turn)})
    dfList[turn-1].drop(columns=['Name','Type','LeaderSkill','Useability'],inplace=True)
    if(turn != 1):
        dfList[turn-1].drop(columns=['SBR'],inplace=True)
    dfList[turn-1].set_index('ID',inplace=True)

dfSBR = dfList[0].join(dfList[1:])
X = dfSBR.iloc[0:]
dfSBR['SBR_score'] = [1-(User[i][3]-1)/(nUnits-1) for i in range(nUnits)]
y = dfSBR['SBR_score']
'''
'''
overallTurns = 10
dfDict = pd.read_excel('unitSummary.xlsx',list(range(overallTurns)))
dfList = [None]*overallTurns
for turn in range(1,overallTurns+1):
    dfList[turn-1] = dfDict[turn-1].rename(columns={"Healing": "Healing_"+str(turn),"Special": "Special_"+str(turn),"Support": "Support_"+str(turn),"APT": "APT_"+str(turn),"normalDefence": "normalDefence_"+str(turn),"saDefence": "saDefence_"+str(turn),"slot1Ability": "slot1Ability_"+str(turn)})
    dfList[turn-1].drop(columns=['Name','Type'],inplace=True)
    if(turn != 1):
        dfList[turn-1].drop(columns=['SBR','Useability','LeaderSkill'],inplace=True)
    dfList[turn-1].set_index('ID',inplace=True)

dfOverall = dfList[0].join(dfList[1:])
X = dfSBR.iloc[0:]
dfOverall['Overall_score'] = [1-(User[i][3]-1)/(nUnits-1) for i in range(nUnits)]
y = dfOverall['Overall_score']'''

# Create a scatter matrix from the dataframe, color by y_train- features mostly non-linear with target
#for feature in dfSBR.columns:
#   sns.scatterplot(data = dfSBR, x=feature , y='SBR_score', palette='RdBu')
#   plt.show()

#from sklearn.model_selection import train_test_split
#X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.4, random_state=1)

# Try Linear Model-ALthough most features are highly non-linear seems to be doing ok, since those features have low weights
#reg = linear_model.LinearRegression()
#cv_results = cross_validate(reg,X,y,cv=5,return_estimator=True)
#coeffs = np.array([model.coef_ for model in cv_results['estimator']])
#meancoeffs = np.mean(coeffs,axis=0)
#print(meancoeffs)
'''reg.fit(X_train, y_train)

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
plt.show()'''

# Try Decision Tree
#regressor = DecisionTreeRegressor(random_state=0)
#print(cross_val_score(regressor, X, y, cv=10))

# Try XGBoost

'''m = XGBRegressor(
    max_depth = 2,
    gamma=2,
    eta=0.8,
    reg_alpha=0.5,
    reg_lambda=0.5
)
m.fit(X_train, y_train)
score = m.score(X_train, y_train)  
print("Training score: ", score)''' # Performs really badly