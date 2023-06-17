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
#SummonRatings()
#Heroes2022 = Banner([32,33,34,35,36,37,38,39,40],'blue',featuredSSR_rate=0.7,gFeatured=True)
#print(Heroes2022.summonScore)
#Heroes2022EZA = Banner([41,42,43,44,45,46,47,48],'blue',featuredSSR_rate=0.7,gFeatured=True,discount=5/3)
#print(Heroes2022EZA.summonScore)
#Gammas = Banner([8,9,11,38,38,38,38],'red')
#print(Gammas.summonScore)
#GalickGun = Banner([4,53,54,55,56,57,58,59,60],'red',threePlus1=True,discount=15/11)
#print(GalickGun.summonScore) # Didn't summon as can buy with coins in March
#HatchiyakGoku = Banner([61,31,26,38,20,74,38,38,38,38,38,38],'cyan',SSR_rate=0.2)
#print(HatchiyakGoku.summonScore)
#BeastGohan = Banner([71,74,55,25,38,29,62,34,38,46],'red',threePlus1=True) 
#print(BeastGohan.summonScore)
#OrangePiccolo = Banner([72,73,54,24,38,14,63,38,34,60],'red',threePlus1=True)
#print(OrangePiccolo.summonScore)
# New LR, Gotenks&piccolo, cooler, gamma1, ff frieza, lr gods, evb vegeta, str gogeta, str vegito, ss vegeta
#GoldenBois = Banner([105,107,7,8,38,3,24,115,38,83],'red',threePlus1=True,tickets=True)
#print(GoldenBois.summonScore)
# New LR, eis&nouza, goku&vegeta, gamma2, ss goku, lr ss4s, ui goku, teq vegiot, phy buutenks, ss goku
##GTBois = Banner([106,108,6,9,83,2,38,116,38,83],'red',threePlus1=True,tickets=True)
#print(GTBois.summonScore)
#KidGoku = Banner([5,30,67,57,81,57,96],'red')
#print(KidGoku.summonScore)
#CarnivalChaLa = Banner([113,10,12,75,66,38,38,38,38,38],'cyan',threePlus1=True)
#print(CarnivalChaLa.summonScore)
#CarnivalDragonSoul = Banner([114,1,16,76,65,38,38,38,38,38],'cyan',threePlus1=True)
#print(CarnivalDragonSoul.summonScore)
#Bardock = Banner([51,52,68,80,84,58,98],'red')
#print(Bardock.summonScore)
Super17 = Banner([117,118,15,11,97,57,25],'red')
print(Super17.summonScore)
#GodGoku = Banner([122,121,4,68,84,38,67,38],'red')
#print(GodGoku.summonScore)
#WTGoku = Banner([130,128,72,62,29,18,85,18],'red',threePlus1=True)
#print(WTGoku.summonScore)
#WTPiccolo = Banner([129,127,71,63,14,18,86,18],'red',threePlus1=True)
#print(WTPiccolo.summonScore)
Turles = Banner([133,134,135,96,51,49,70],'red')
print(Turles.summonScore)
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
