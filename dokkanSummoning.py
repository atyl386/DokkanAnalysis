import pickle
import pandas as pd
import datetime as dt
from dateutil.relativedelta import relativedelta
import numpy as np
from dokkanUnitConstants import NUM_COPIES_MAX
from dokkanEvaluation import parseDokkanAccountXML
from dokkanUnitConstants import DOKKAN_ACCOUNT_XML_FILE_PATH

HiPo_dupes = ["55%", "69%", "79%", "90%", "100%"]
User = parseDokkanAccountXML(DOKKAN_ACCOUNT_XML_FILE_PATH)
nUnits = len(User)


def SummonRating(ID):
    pkl = open("C:/Users/Tyler/Documents/DokkanAnalysis/DokkanUnits/100%/unit_" + str(ID) + ".pkl", "rb")
    unit = pickle.load(pkl)
    pkl.close()
    nCopies = User[ID]["num_copies"]
    evals = [0.0] * NUM_COPIES_MAX
    now = dt.datetime.today()
    EZADiscountFactor = 1/3
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
            EZADI = 0.1
        case 0:
            EZADI = 0.7

    if unit.exclusivity in ["DFLR", "DF", "CLR", "LR"]:
        rarityScore = 50  # These are summonRatings, have to be tuned
    else:
        rarityScore = 25
    if unit.EZA:
        EZA = 6 / 7
        futureEZA = 0
        globalEZADate = unit.gbl_date
    else:
        EZA = 1
        globalEZADate = unit.gbl_date + relativedelta(months=4 * 12)
        futureEZA = rarityScore * EZADiscountFactor ** (relativedelta(globalEZADate, now).years) * EZADI
    for i in range(NUM_COPIES_MAX):
        df = pd.read_excel("DokkanUnits/" + HiPo_dupes[i] + "/unitSummary.xlsx", index_col="ID")
        evals[i] = df.at[ID, "Evaluation"]
    if nCopies == 5:
        dupeImprovement = 0
    elif nCopies > 0:
        dupeImprovement = max((evals[nCopies] - evals[nCopies - 1]) / (evals[-1]), 0)
    else:
        dupeImprovement = max((evals[nCopies]) / (evals[-1]), 0)
    summonRating = max(max(evals[-1], 0) * dupeImprovement * EZA, max(0.2, futureEZA), 0)
    return summonRating


def SummonRatings():
    IDs = list(User.keys())
    commonName = [""] * nUnits
    nCopies = [0] * nUnits
    summonRatings = [0.0] * nUnits
    for ID in IDs:
        commonName[ID - 1] = User[ID]["common_name"]
        nCopies[ID - 1] = User[ID]["num_copies"]
        summonRatings[ID - 1] = SummonRating(ID)
    df = pd.DataFrame(
        data=np.transpose([IDs, commonName, nCopies, summonRatings]),
        columns=["ID", "common_name", "num_copies", "Summon Rating"],
    )
    df.set_index("ID", inplace=True)
    with pd.ExcelWriter("SummonRating.xlsx") as writer:
        df.to_excel(writer)


class Banner:
    def __init__(
        self,
        units,
        coin,
        SSR_rate=0.1,
        featuredSSR_rate=0.5,
        tickets=False,
        discount=1,
        threePlus1=False,
        gFeatured=False,
        gFeaturedEvery3=False,
        anniversaryFormat=False,
    ):
        self.units = np.mean([SummonRating(unit) for unit in units])
        if coin == "red" or coin == "cyan":
            self.coin = 1
        elif coin == "limited" or coin == "yellow":
            self.coin = 0.8
        else:
            self.coin = 0.7
        if gFeatured:
            self.featuredRate = (1 + 9 * SSR_rate * featuredSSR_rate) / (10 * 0.1 * 0.5)
        elif gFeaturedEvery3:
            self.featuredRate = (
                2 * SSR_rate * featuredSSR_rate / (0.1 * 0.5) + (1 + 9 * SSR_rate * featuredSSR_rate) / (10 * 0.1 * 0.5)
            ) / 3
        else:
            self.featuredRate = SSR_rate * featuredSSR_rate / (0.1 * 0.5)
        if tickets:
            self.tickets = 1.3
        else:
            self.tickets = 1
        if threePlus1:
            self.threePlus1 = 4 / 3
        else:
            self.threePlus1 = 1
        if anniversaryFormat:
            self.anniBonus = (6 + (1 + 9 * SSR_rate * featuredSSR_rate) / (10 * 0.1 * 0.5)) / ((30 + 40 + 50 + 0 + 40 + 45 + 50)/50)
        else:
            self.anniBonus = 1 
        self.summonScore = self.units * self.coin * self.featuredRate * self.tickets * self.threePlus1 * discount * self.anniBonus

    def shouldSummmon(self):
        if self.summonScore > 20:  # Will need to be tuned
            return True
        else:
            return False


SummonRatings()
""" Halloween = Banner([115, 116, 83, 68, 64, 5, 78, 63, 62, 20], 'red')
HalloweenStep2 = Banner([64, 78, 63, 62, 20], 'red')
HalloweenStep3A = Banner([127, 128, 118, 108, 107, 124, 74, 73, 50, 52], 'red')
S1 = Halloween.summonScore*25/20
S2 = (6*Halloween.summonScore+20*HalloweenStep2.summonScore)/7
S3 = (8*Halloween.summonScore+20*HalloweenStep3A.summonScore + 20*Halloween.summonScore)/10
Rotation = np.mean([S1,S2,S3])
print(Rotation) """
Goku_Gohan_Trunks = Banner([246, 247, 160, 42, 63, 2, 62, 44, 248, 101], 'red', threePlus1=True)
print(Goku_Gohan_Trunks.summonScore)
Broly = Banner([245, 79, 64, 23, 51, 49, 242, 49, 49, 49], 'cyan', threePlus1=True)
print(Broly.summonScore)
FamilyKamehameha = Banner([254, 165, 53, 22, 1, 78, 249, 250, 250, 250], 'cyan', threePlus1=True)
print(FamilyKamehameha.summonScore)
LSSBroly = Banner([253, 252, 161, 35, 4, 3, 59, 37, 161, 156], 'red', threePlus1=True)
print(LSSBroly.summonScore)
WWDL_1 = Banner([36, 19, 31, 30, 17, 150, 39, 34, 8, 33, 40, 140, 11, 170, 21, 257, 41, 21, 93, 163, 135, 127, 126, 86, 104, 142, 142, 60, 60, 60, 128, 128, 128, 127, 10, 188, 188, 183, 183, 116, 25, 116, 116, 25, 25, 101, 101, 211, 25, 101, 116, 25, 25, 25, 101, 170],'red', discount=50*(2 + 10 * 2)/100)
print(WWDL_1.summonScore)
WWDL_2 = Banner([25, 18, 5, 7, 32, 134, 45, 38, 46, 25, 10, 20, 9, 25, 170, 48, 48, 25, 164, 155, 98, 170, 146, 131, 25, 145, 129, 25, 54, 8, 25, 132, 116, 25, 146, 116, 8, 126, 8, 25, 116, 25, 25, 48, 170, 41, 25, 48, 48, 25, 156, 25, 25, 25, 101, 101],'red', discount=50*(2 + 10 * 2)/100)
print(WWDL_2.summonScore)
# NYSU2023_S1 = Banner([38,38,38,38,38,70,70,38,79,38,70,88,89,89,38,38,77,38,88],'red')
# NYSU2023_S2 = Banner([70,70,70,81,70,81,70,81,81,69,85,69,38],'red')
# NYSU2023_S3 = Banner([38,70,70,58,84,57,86,85,70,87,38,38],'red')
# NYSU2023_S4 = Banner([14,29,67,68,20,63,62,11,78,28,80],'red')
# NYSU2023_S5 = Banner([65,66,76,75,26,77,85,53,21,81,35,81,53,53,53],'red')
# NYSU2023 = Banner([14,29,67,68,20,63,62,11,78,28,80,38,70,70,58,84,57,86,85,70,87,38,38,38,38,38,38,38,70,70,38,79,38,70,88,89,89,38,38,77,38,88],'red')
# S1 = (9*NYSU2023.summonScore+20*NYSU2023_S1.summonScore)/10*5/2
# S2 = (9*NYSU2023.summonScore+20*NYSU2023_S2.summonScore)/10*5/3
# S3 = (9*NYSU2023.summonScore+20*NYSU2023_S3.summonScore)/10
# S4 = (9*NYSU2023.summonScore+20*NYSU2023_S4.summonScore)/10
# S5 = (9*NYSU2023.summonScore+20*NYSU2023_S5.summonScore)/10
# Rotation = np.mean([S1,S2,S3,S4,S5])
# print(Rotation)
