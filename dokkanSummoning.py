import pickle
from dokkanAccount import User
import pandas as pd
import datetime as dt
from dateutil.relativedelta import relativedelta
import numpy as np
copiesMax = 5
HP_dupes = ['55%','69%','79%','90%','100%']
nUnits = len(User)
def SummonRating(ID):
    pkl = open('C:/Users/Tyler/Documents/DokkanAnalysis/DokkanUnits/100%/unit_'+str(ID)+'.pkl','rb')
    unit = pickle.load(pkl)
    pkl.close()
    nCopies = User[ID-1][3]
    evals = [0.0]*copiesMax
    now = dt.datetime.today()
    EZADiscountFactor = 0.5
    scalingPower = 1
    # This number is a fudge factor to get sensible dupe improvement
    match nCopies:
        case 5:
           EZADI = 0
        case 4:
            EZADI = 0.05
        case 3:
            EZADI = 0.05
        case 2:
            EZADI = 0.1
        case 1:
            EZADI = 0.2
        case 0:
            EZADI = 0.8

    if (unit.kit.exclusivity in ['DF LR','DF','Carnival LR','DFLR','DCLR']):
        rarityScore = 50 # These are summonRatings, have to be tuned
    else:
        rarityScore = 25
    if (unit.kit.EZA):
        EZA = 6/7
        futureEZA = 0
        globalEZADate=unit.kit.GLB_releaseDate
    else:
        EZA = 1
        globalEZADate=unit.kit.GLB_releaseDate + relativedelta(months=4*12)
        futureEZA = rarityScore**scalingPower*EZADiscountFactor**(relativedelta(globalEZADate,now).years)*EZADI
    for i in range(copiesMax):
        df = pd.read_excel('DokkanUnits/'+HP_dupes[i]+'/unitSummary.xlsx')
        evals[i] = df.at[ID-1,'Evaluation']
    if nCopies == 5:
        dupeImprovement = 0
    elif nCopies > 0:
        dupeImprovement = max((evals[nCopies]-evals[nCopies-1])/(evals[-1]),0)
    else:
        dupeImprovement = max((evals[nCopies])/(evals[-1]),0)
    summonRating = max(max(evals[-1]**scalingPower,0)*dupeImprovement*EZA,max(0.2,futureEZA),0)
    return summonRating
def SummonRatings():
    ID = np.arange(1,nUnits+1)
    Name = [""]*nUnits
    Type = [""]*nUnits
    nCopies = [0]*nUnits
    summonRatings = [0.0]*nUnits
    for i in range(nUnits):
        pkl = open('C:/Users/Tyler/Documents/DokkanAnalysis/DokkanUnits/100%/unit_'+str(i+1)+'.pkl','rb')
        unit = pickle.load(pkl)
        pkl.close()
        Name[i] = unit.kit.name
        Type[i] = unit.kit.type
        nCopies[i] = User[i][3]
        summonRatings[i] = SummonRating(i+1)
    df = pd.DataFrame(data=np.transpose([ID,Name,Type,nCopies,summonRatings]),columns=['ID','Name','Type','# Copies','Summon Rating'])
    df.set_index('ID',inplace=True)
    with pd.ExcelWriter('SummonRating.xlsx') as writer:
        df.to_excel(writer)
class Banner:
    def __init__(self,units,coin,SSR_rate=0.1,featuredSSR_rate=0.5,tickets=False,discount=1,threePlus1=False,gFeatured=False):
        self.units = np.mean([SummonRating(unit) for unit in units])
        if coin == 'red' or coin == 'cyan':
            self.coin = 1
        else:
            self.coin = 0.8
        if gFeatured:
            self.featuredRate = (1+9*SSR_rate*featuredSSR_rate)/(10*0.1*0.5)
        else:
            self.featuredRate = SSR_rate*featuredSSR_rate/(0.1*0.5)
        if tickets:
            self.tickets = 1.3
        else:
            self.tickets = 1
        if threePlus1:
            self.threePlus1 = 4/3
        else:
            self.threePlus1 = 1
        self.summonScore = self.units*self.coin*self.featuredRate*self.tickets*self.threePlus1*discount
    def shouldSummmon(self):
        if (self.summonScore>20): # Will need to be tuned
            return True
        else:
            return False
SummonRatings()
CarnivalChaLa = Banner([113,10,12,75,66,38,38,38,38,38],'cyan',threePlus1=True)
print(CarnivalChaLa.summonScore)
CarnivalDragonSoul = Banner([114,1,16,76,65,38,38,38,38,38],'cyan',threePlus1=True)
print(CarnivalDragonSoul.summonScore)
Kale = Banner([123,124,5,20,28,64,58],'red')
print(Kale.summonScore)
Turles = Banner([133,134,135,96,51,49,70],'red')
print(Turles.summonScore)
SSJ4Goku = Banner([139,4,54,55,8,9,15,138,32,35],'red',threePlus1=True)
print(SSJ4Goku.summonScore)
#NYSU2023_S1 = Banner([38,38,38,38,38,70,70,38,79,38,70,88,89,89,38,38,77,38,88],'red')
#NYSU2023_S2 = Banner([70,70,70,81,70,81,70,81,81,69,85,69,38],'red')
#NYSU2023_S3 = Banner([38,70,70,58,84,57,86,85,70,87,38,38],'red')
#NYSU2023_S4 = Banner([14,29,67,68,20,63,62,11,78,28,80],'red')
#NYSU2023_S5 = Banner([65,66,76,75,26,77,85,53,21,81,35,81,53,53,53],'red')
#NYSU2023 = Banner([14,29,67,68,20,63,62,11,78,28,80,38,70,70,58,84,57,86,85,70,87,38,38,38,38,38,38,38,70,70,38,79,38,70,88,89,89,38,38,77,38,88],'red')
#S1 = (9*NYSU2023.summonScore+20*NYSU2023_S1.summonScore)/10*5/2
#S2 = (9*NYSU2023.summonScore+20*NYSU2023_S2.summonScore)/10*5/3
#S3 = (9*NYSU2023.summonScore+20*NYSU2023_S3.summonScore)/10
#S4 = (9*NYSU2023.summonScore+20*NYSU2023_S4.summonScore)/10
#S5 = (9*NYSU2023.summonScore+20*NYSU2023_S5.summonScore)/10
#Rotation = np.mean([S1,S2,S3,S4,S5])
#print(Rotation)
