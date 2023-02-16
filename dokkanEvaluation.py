import pickle
import openpyxl
from dokkanUnit import Unit, turnMax
import numpy as np
import pandas as pd
from sklearn import linear_model, metrics
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import cross_validate, cross_val_score, train_test_split
from xgboost import XGBRegressor
from scipy.stats import truncnorm
from dokkanAccount import User
nSclarAttributes = 3
nAttributes = 9
copiesMax = 5
meanPeakTurn = 3.471591
meanPeakTurnStd = 1.857813
Units = [['A','C','D',6,1], # TEQLR SS Goku
    ['A','C','D',9,2], # PHYLR SS4s
    ['A','C','D',8,3], # TEQLR Gods
    ['A','C','D',4,4], # INTLR Vegeta & Trunks
    ['A','C','D',10,5], # PHY Goku Youth
    ['A','C','D',17,6], # AGLLR SSs
    ['C','A','A',12,7], # STRLR Final Form Cooler
    ['A','C','D',7,8], # STR Gamma 1
    ['A','C','A',11,9], # AGL Gamma 2
    ['C','A','D',20,10], # PHYLR Metal Cooler
    ['C','A','A',21,11], # TEQ Androids 17&18
    ['C','A','D',22,12], # AGLLR Golden Frieza
    ['A','C','A',34,13], # AGLLR MUI Goku
    ['A','C','D',15,14], # STR SS Goku/Gohan
    ['C','A','D',24,15], # TEQ Pan
    ['A','D','D',32,17], # INT Cheelai
    ['A','C','D',29,18], # STR Cooler
    ['A','C','D',16,19], # TEQ Ultimate Gohan
    ['A','C','D',19,20], # AGL Captain Ginyu
    ['C','A','D',36,21], # PHYLR Super Janemba
    ['A','C','D',40,22], # STR Namek Goku
    ['C','A','D',50,23], # INTLR Super Vegito
    ['A','C','D',65,24], # AGLLR SS4 Goku
    ['C','A','D',62,25], # STRLR SS4 Vegeta
    ['C','A','D',53,26], # AGLLR Future Gohan & Trunks
    ['A','C','D',38,27], # INT 19&20
    ['A','C','D',46,28], # TEQ Kale & Caulifla
    ['A','C','D',31,29], # AGL 1st Form Cell
    ['C','A','D',35,30], # AGL Hacchan
    ['A','C','D',23,31], # STR Piccolo (Banner)
    ['C','A','D',43,34], # STR Super Hearts
    ['C','D','D',54,35], # INT SS4 Gohan
    ['A','C','D',85,36], # STR SS4 Bardock
    ['A','C','D',94,37], # STR Supreme Kai of Time (Brainwashed)
    ['A','C','D',70,38], # Robelu
    ['C','A','D',88,39], # Golden Metal Cooler
    ['A','C','D',86,40], # Janemba (Reconstructed)
    ['A','C','D',90,41], # PHY Super Saiyan Cumber
    ['A','D','D',81,42], # TEQ Supreme Opai of Time
    ['A','C','D',92,43], # PHY SS3 Vegeta (Xeno)
    ['A','C','D',39,44], # STR SS3 Goku (Xeno)
    ['A','C','D',57,46], # Golden Cooler
    ['A','C','D',72,47], # STR Sealas
    ['C','A','D',79,48], # TEQ Great Saiyaman 3
    ['A','C','D',28,49], # INT Yamcha
    ['A','D','D',27,50], # TEQ Yajirobe
    ['A','D','D',30,51], # TEQ Bardock
    ['C','D','D',41,52], # INT Tora
    ['A','C','D',45,54], # TEQ LR Gogeta
    ['C','A','D',91,56], # TEQ LR SS Gohan & Goten
    ['A','C','D',95,59], # STR SSGSSK Goku
    ['A','D','D',93,60], # INT Goku Black
    ['C','A','D',25,62], # STR Kid Buu
    ['A','D','D',55,63], # PHY Super Saiyan 2 Goku
    ['A','C','D',64,64],  # RoF Blues
    ['A','C','D',80,65], # LR TEQ SS Goku & Gohan
    ['A','C','D',77,66], # LR Goku & Piccolo/Piccolo
    ['C','A','D',42,68], # INT Majin Vegeta
    ['A','C','D',37,69], # LR Goku Black & Zamasu
    ['C','A','D',51,70], # LR INT Boujack
    ['C','A','D',13,71], # LR Beast Gohan
    ['A','C','D',3,72], # LR Orange Piccolo
    ['A','D','D',56,73], # Pan (Kid)
    ['C','A','D',49,75], # LR Vegeta (Great Ape)
    ['A','C','D',73,76], # LR Goku (Kaioken)
    ['A','C','D',47,77], # STR Ultimate Gohan
    ['A','C','D',52,79], # PHY Future Gohan
    ['A','D','D',89,80], # STR Super Vegeta
    ['A','C','D',84,81], # STR Videl
    ['C','A','D',63,82], # LR Full Power Frieza AGL
    ['A','C','D',44,83], # LR Super Saiyan Goku INT
    ['A','C','D',60,84], # INT LSS Broly
    ['A','D','D',69,85], # AGL Paikuhan
    ['D','A','D',66,86], # TEQ Janemba
    ['C','A','D',71,87], # STR UI Goku
    ['A','C','D',74,88], # TEQ VB
    ['A','C','D',78,89], # STR Rose Goku Black
    ['A','C','D',18,90], # AGL Blue Gogeta
    ['C','A','D',33,91], # PHY SS Broly
    ['C','A','D',58,93], # INT SS3 Bardock
    ['A','C','D',67,94], # INT Kid Goku
    ['A','C','D',76,95], # AGL SSGSSE Vegeta
    ['A','C','D',82,96], # AGL Turles
    ['D','A','D',68,97], # AGL Super 17
    ['A','C','D',75,98], # AGL Transforming Goku
    ['A','C','D',87,99], # INT Angel Golden Frieza
    ['A','C','D',61,100], # INT UI Goku
    ['C','A','D',48,101], # TEQ Super FP Saiyan 4 Goku
    ['A','C','D',59,102], # TEQ Super Saiyan 4 Gogeta
    ['A','C','D',14,103], # LR INT Cell
    ['A','C','D',5,104], # LR AGL Gohan
    ['A','C','D',1,105], # LR GoldenBois
    ['C','A','D',2,106], # LR GT Bois
    ['C','D','D',26,107], # SS3 Gotenks & Piccolo
    ['A','D','D',83,108] # Eis & Nouva Shenron
]

nUnits = len(User)
def logisticMap(x,x_max,L=100,d=1,x_min=-7):
    L = L + d
    x_0=(x_min+x_max)/2
    k = 2*np.log((L-d)/d)/(x_max-x_min)
    return L/(1+np.exp(-k*(x-x_0)))
HP_dupes = ['55%','69%','79%','90%','100%']
HP_builds = [['A','C','D'],['A','C','A'],['A','D','D'],['A','D','A'],['C','A','D'],['C','A','A'],['C','D','D'],['C','D','A'],['D','C','D'],['D','A','D']]
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
overallAttributeWeights = np.array([5,0.5,4,2,6,10,8,8,5])
overallEvaluator = Evaluator(overallTurnWeights,overallAttributeWeights)

reCalc = True
analyseHP = False
if reCalc:
    attributeValues = np.zeros((nUnits,turnMax,nAttributes,copiesMax))
    units = [[None]*nUnits for i in range(copiesMax)]
    evaluations = np.zeros((nUnits,copiesMax))
    for ID in range(1,nUnits+1):
        print(ID)
        units[-1][ID-1] = Unit(ID,copiesMax,User[ID-1][0:2],User[ID-1][2])
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
                HP_unit = Unit(ID,copiesMax,HP_build[0:2],HP_build[2])
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
            units[nCopies-1][ID-1] = Unit(ID,nCopies,User[ID-1][0:2],User[ID-1][2])
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