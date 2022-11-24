import pickle
from dokkanAccount import User
import pandas as pd
import datetime as dt
from dateutil.relativedelta import relativedelta
import numpy as np
copiesMax = 5
HP_dupes = ['55%','69%','79%','90%','100%']
def SummonRating(ID):
    pkl = open('C:/Users/Tyler/Documents/DokkanAnalysis/DokkanUnits/100%/unit_'+str(ID)+'.pkl','rb')
    unit = pickle.load(pkl)
    pkl.close()
    nCopies = User[ID-1][3]
    evals = [0.0]*copiesMax
    now = dt.datetime.today()
    EZADiscountFactor = 0.5
    minEval = -100 # Baseline so know what is useful. This will change as database reaches steady state i.e. means and stds.
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

    if (unit.kit.rarity in ['DFLR','DF','DCLR']):
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
        futureEZA = EZADiscountFactor**(relativedelta(globalEZADate,now).months)*EZADI
    for i in range(copiesMax):
        df = pd.read_excel('DokkanUnits/'+HP_dupes[i]+'/unitSummary.xlsx')
        evals[i] = df.at[ID-1,'Evaluation']
    if nCopies == 5:
        dupeImprovement = 0
    elif nCopies > 0:
        dupeImprovement = max((evals[nCopies]-evals[nCopies-1])/(evals[-1]-minEval),0)
    else:
        dupeImprovement = max((evals[nCopies]-minEval)/(evals[-1]-minEval),0)
    summonRating = max(max(evals[-1]**1.5,0)*dupeImprovement*EZA,max(0.2,futureEZA),0)
    return summonRating
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
        self.summonScore = self.units*self.coin*self.featuredRate*self.tickets*self.threePlus1
    def shouldSummmon(self):
        if (self.summonScore>300): # Will need to be tuned
            return True
        else:
            return False
Heroes2022 = Banner([32,33,34,35,36,37,38,39,40],'blue',featuredSSR_rate=0.7,gFeatured=True)
print(Heroes2022.summonScore)
Heroes2022EZA = Banner([41,42,43,44,45,46,47,48],'blue',featuredSSR_rate=0.7,gFeatured=True,discount=5/3)
print(Heroes2022EZA.summonScore)
Gammas = Banner([8,9,11,38,38,38,38],'red')
print(Gammas.summonScore)
GalickGun = Banner([4,48,34,28,1,10,1,1,43],'red',threePlus1=True)
print(GalickGun.summonScore)
