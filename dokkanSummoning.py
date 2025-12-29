import pandas as pd
import datetime as dt
from dateutil.relativedelta import relativedelta
from collections import defaultdict
from itertools import chain
import numpy as np
from dokkanUnitConstants import NUM_COPIES_MAX, DOKKAN_ACCOUNT_XML_FILE_PATH
from dokkanEvaluation import parseDokkanAccountXML, Unit, os

HiPo_dupes = ["55%", "69%", "79%", "90%", "100%"]
User = parseDokkanAccountXML(DOKKAN_ACCOUNT_XML_FILE_PATH)
nUnits = len(User)


def SummonRating(ID, unitSummaries):
    unit = Unit(ID, processUnit=False)
    unit.getConstants()
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
        rarityScore = 15
    if unit.EZA:
        EZA = 6 / 7
        futureEZA = 0
        EZADate = unit.date
    else:
        EZA = 1
        EZADate = unit.date + relativedelta(months=4 * 12)
        timeUntilEZA_years = relativedelta(EZADate, now)
        futureEZA = rarityScore * EZADiscountFactor ** (timeUntilEZA_years.years + timeUntilEZA_years.months/12) * EZADI
    if os.path.exists("DokkanUnits/" + HiPo_dupes[0] + "/unit_" + str(ID) + ".pkl"):
        for i in range(NUM_COPIES_MAX):
            evals[i] = unitSummaries[HiPo_dupes[i]].at[ID, "Evaluation"]
        if nCopies == 5:
            dupeImprovement = 0
        elif nCopies > 0:
            dupeImprovement = max((evals[nCopies] - evals[nCopies - 1]) / (evals[-1]), 0)
        else:
            dupeImprovement = max((evals[nCopies]) / (evals[-1]), 0)
        summonRating = max(max(evals[-1], 0) * dupeImprovement * EZA, max(0.2, futureEZA), 0)
    else:
        summonRating = max(0.2, futureEZA)
    return summonRating


def SummonRatings():
    unitSummaries = dict.fromkeys(HiPo_dupes)
    for i in range(NUM_COPIES_MAX):
        unitSummaries[HiPo_dupes[i]] = pd.read_excel("DokkanUnits/" + HiPo_dupes[i] + "/unitSummary.xlsx", index_col="ID")
    IDs = list(User.keys())
    commonName = [""] * nUnits
    nCopies = [0] * nUnits
    summonRatings = [0.0] * nUnits
    for ID in IDs:
        commonName[ID - 1] = User[ID]["common_name"]
        nCopies[ID - 1] = User[ID]["num_copies"]
        summonRatings[ID - 1] = SummonRating(ID, unitSummaries)
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
        summonPointsPerMulti=30,
        summonPoints=False,
        fourthiethAnniversary=False,
    ):
        df = pd.read_excel("SummonRating.xlsx", index_col="ID")
        summonRatingData = [(df.at[unit, "common_name"], round(df.at[unit, "Summon Rating"], 2)) for unit in units]
        self.summonRatings = defaultdict(list)
        for key, val in summonRatingData:
            self.summonRatings[key].append(val)
        self.units = np.mean(list(chain(*self.summonRatings.values())))
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
        if summonPoints:
            self.summonPoints = 15 * summonPointsPerMulti / 300 # avg 15 summon rating per ticket, 300 per ticket
        else:
            self.summonPoints = 0
        if fourthiethAnniversary:
            self.featuredRate = (3 + 7 * 0.2) / (10 * 0.1 * 0.5)
            coins = 0.25 * max(list(chain(*self.summonRatings.values())))
        else:
            coins = 0
        self.summonScore = self.units * self.coin * self.featuredRate * self.tickets * self.threePlus1 * discount * self.anniBonus + summonPoints + coins

    def shouldSummmon(self):
        if self.summonScore > 12.5:  # Will need to be tuned. Could be as high as 15
            return True
        else:
            return False


SummonRatings()
GohanGamma1 = Banner([444, 358, 161, 150, 37, 35, 40], "red", summonPoints=True, threePlus1=True)
print(GohanGamma1.summonRatings)
print(GohanGamma1.summonScore)
Gamma2Piccolo = Banner([445, 359, 160, 134, 44, 47, 42], "red", summonPoints=True, threePlus1=True)
print(Gamma2Piccolo.summonRatings)
print(Gamma2Piccolo.summonScore)
FutureGohanTrunks = Banner([443, 313, 14, 12, 438, 440, 154, 439, 434, 433], "cyan", SSR_rate=0.2)
print(FutureGohanTrunks.summonRatings)
print(FutureGohanTrunks.summonScore)
Android16 = Banner([437, 436, 368, 17, 15, 140, 10, 5, 39, 46], "red", gFeaturedEvery3=True, summonPoints=True)
print(Android16.summonRatings)
print(Android16.summonScore)
BlackFridayDF = Banner([374, 386, 327, 337, 246, 253, 85, 398, 388, 389], "red", threePlus1=True)
print(BlackFridayDF.summonRatings)
print(BlackFridayDF.summonScore)
BlackFridayCarnival = Banner([375, 387, 326, 325, 336, 335, 245, 254, 105, 402], "cyan", threePlus1=True)
print(BlackFridayCarnival.summonRatings)
print(BlackFridayCarnival.summonScore)
Gomah = Banner([435, 370, 355, 356, 303, 247, 281, 353, 263, 264], "yellow", gFeaturedEvery3=True, summonPoints=True)
print(Gomah.summonRatings)
print(Gomah.summonScore)
fourthiethAnniversary = Banner([434, 433, 432, 431, 430], "blue", fourthiethAnniversary=True, discount=5/3)
print(fourthiethAnniversary.summonRatings)
print(fourthiethAnniversary.summonScore)
SS4DaimaGokuMini = Banner([424, 423, 345, 343, 233, 100, 110, 28, 11, 104], "red", gFeaturedEvery3=True, summonPoints=True)
print(SS4DaimaGokuMini.summonRatings)
print(SS4DaimaGokuMini.summonScore)
PossessedBros = Banner([416, 266, 415, 417, 396, 119, 415, 415, 186, 159], "yellow", gFeaturedEvery3=True, summonPoints=True)
print(PossessedBros.summonRatings)
print(PossessedBros.summonScore)
Baby = Banner([414, 413, 351, 307, 282, 260, 84, 162, 7, 332], "red", gFeaturedEvery3=True)
print(Baby.summonRatings)
print(Baby.summonScore)
WrathfulBroly = Banner([410, 366, 156, 121, 389, 388, 334, 65, 99, 136], "cyan", SSR_rate=0.2, threePlus1=True)
print(WrathfulBroly.summonRatings)
print(WrathfulBroly.summonScore)
GoldenFriezeGogeta = Banner([409, 408, 359, 358, 320, 321, 97], "red", threePlus1=True)
print(GoldenFriezeGogeta.summonRatings)
print(GoldenFriezeGogeta.summonScore)
PeppyGals = Banner([405, 404, 403, 172, 240, 241, 141], "blue", discount=1/0.6, gFeatured=True, summonPoints=True)
print(PeppyGals.summonRatings)
print(PeppyGals.summonScore)
SSHyrbids = Banner([401, 400, 343, 160, 161, 233, 28, 257, 164, 155], "red", gFeaturedEvery3=True, summonPoints=True)
print(SSHyrbids.summonRatings)
print(SSHyrbids.summonScore)
SS4GogetaOne = Banner([387], "cyan", threePlus1=True, featuredSSR_rate=0.44, summonPoints=False)
print(SS4GogetaOne.summonRatings)
print(SS4GogetaOne.summonScore/5)
OmegaShenron = Banner([386, 385, 327, 253, 66, 4, 61, 259, 340, 323], "red", threePlus1=True, summonPoints=False)
print(OmegaShenron.summonRatings)
print(OmegaShenron.summonScore)
SS4Gogeta = Banner([387, 336, 326, 254, 83, 53, 12, 11, 11, 11], "cyan", threePlus1=True, summonPoints=False)
print(SS4Gogeta.summonRatings)
print(SS4Gogeta.summonScore)
BlueGokuVegeta = Banner([374, 376, 337, 246, 81, 63, 58, 85, 382, 383], "red", threePlus1=True, summonPoints=False)
print(BlueGokuVegeta.summonRatings)
print(BlueGokuVegeta.summonScore)
GokuBlackZamasu = Banner([375, 335, 325, 245, 67, 64, 105, 89, 185, 152], "cyan", threePlus1=True, summonPoints=False)
print(GokuBlackZamasu.summonRatings)
print(GokuBlackZamasu.summonScore)
RadiantSummer = Banner([218, 246, 253, 343, 282, 260, 100], "red")
print(RadiantSummer.summonRatings)
print(RadiantSummer.summonScore)
Tao = Banner([368, 367, 84, 110, 134, 150, 162, 33, 307, 32], "red", gFeaturedEvery3=True, summonPoints=True)
print(Tao.summonRatings)
print(Tao.summonScore)
KaleAndCaulifla = Banner([366, 313, 230, 114, 216, 210, 141, 136, 136, 136], "cyan", SSR_rate=0.2)
print(KaleAndCaulifla.summonRatings)
print(KaleAndCaulifla.summonScore)
Hit = Banner([358, 357, 320, 161, 35, 36, 20], "red", threePlus1=True)
print(Hit.summonRatings)
print(Hit.summonScore)
SSGSSKGoku = Banner([359, 356, 321, 160, 42, 43, 360], "red", threePlus1=True)
print(SSGSSKGoku.summonRatings)
print(SSGSSKGoku.summonScore)
Cell = Banner([351, 350, 282, 97, 15, 28, 7, 39, 46, 283], "red", gFeaturedEvery3=True)
print(Cell.summonRatings)
print(Cell.summonScore)
KidGoku = Banner([345, 344, 218, 233, 100, 18, 19], "red", threePlus1=True)
print(KidGoku.summonRatings)
print(KidGoku.summonScore)
SS3VegetaDaima = Banner([343, 321, 320, 260, 161, 160, 341, 342, 171, 9], "red", gFeaturedEvery3=True)
print(SS3VegetaDaima.summonRatings)
print(SS3VegetaDaima.summonScore)
SuperGogeta = Banner([337, 334, 253, 81, 4, 3, 58, 90, 259, 330], "red", threePlus1=True)
print(SuperGogeta.summonRatings)
print(SuperGogeta.summonScore)
GohanGokuFriezaToP = Banner([336, 335, 245, 67, 64, 23, 1, 279, 333, 340], "cyan", threePlus1=True)
print(GohanGokuFriezaToP.summonRatings)
print(GohanGokuFriezaToP.summonScore)
SuperVegito = Banner([327, 324, 246, 66, 63, 2, 61, 91, 95, 331], "red", threePlus1=True)
print(SuperVegito.summonRatings)
print(SuperVegito.summonScore)
GokuAndVegetaToP = Banner([326, 325, 254, 83, 53, 22, 51, 278, 113, 117], "cyan", threePlus1=True)
print(GokuAndVegetaToP.summonRatings)
print(GokuAndVegetaToP.summonScore)
DaimaGoku = Banner([320, 161, 35, 44, 47, 43, 41], "red", threePlus1=True)
print(DaimaGoku.summonRatings)
print(DaimaGoku.summonScore)
Glorio = Banner([321, 160, 42, 37, 40, 36, 48], "red", threePlus1=True)
print(Glorio.summonRatings)
print(Glorio.summonScore)
#WWDL_1 = Banner([36, 19, 31, 30, 17, 150, 39, 34, 8, 33, 40, 140, 11, 170, 21, 257, 41, 21, 93, 163, 135, 127, 126, 86, 104, 142, 142, 60, 60, 60, 128, 128, 128, 127, 10, 188, 188, 183, 183, 116, 25, 116, 116, 25, 25, 101, 101, 211, 25, 101, 116, 25, 25, 25, 101, 170],'red', discount=50*(2 + 10 * 2)/100)
#print(WWDL_1.summonScore)
#WWDL_2 = Banner([25, 18, 5, 7, 32, 134, 45, 38, 46, 25, 10, 20, 9, 25, 170, 48, 48, 25, 164, 155, 98, 170, 146, 131, 25, 145, 129, 25, 54, 8, 25, 132, 116, 25, 146, 116, 8, 126, 8, 25, 116, 25, 25, 48, 170, 41, 25, 48, 48, 25, 156, 25, 25, 25, 101, 101],'red', discount=50*(2 + 10 * 2)/100)
#print(WWDL_2.summonScore)

""" NYSU2025_DF_S1_S1A = Banner([82, 65, 173, 29, 16, 87, 89],"red")
NYSU2025_DF_S1_S1B = Banner([298, 262, 258, 211, 170, 156, 101],"red")
NYSU2025_DF_S1_S2 = Banner([283, 257, 248, 21, 93, 164, 163],"red")
NYSU2025_DF_S1_S3 = Banner([102, 7, 32, 31, 134, 150, 19],"red")
NYSU2025_DF_S1_S4 = Banner([162, 28, 15, 5, 30, 17, 18],"red")
NYSU2025_DF_S1_S5 = Banner([218, 84, 110, 100, 97],"red")
NYSU2025_DF_S1 = Banner([283, 257, 248, 21, 93, 164, 163, 102, 317, 32, 31, 134, 150, 19, 162, 28, 15, 5, 30, 17, 18, 218, 84, 110, 100, 97],"red")
DF_S1 = (8*NYSU2025_DF_S1.summonScore+20*NYSU2025_DF_S1_S1A.summonScore+20*NYSU2025_DF_S1_S1B.summonScore)/10*5/2
DF_S2 = (9*NYSU2025_DF_S1.summonScore+20*NYSU2025_DF_S1_S2.summonScore)/10*5/3
DF_S3 = (9*NYSU2025_DF_S1.summonScore+20*NYSU2025_DF_S1_S3.summonScore)/10
DF_S4 = (9*NYSU2025_DF_S1.summonScore+20*NYSU2025_DF_S1_S4.summonScore)/10
DF_S5 = (9*NYSU2025_DF_S1.summonScore+20*NYSU2025_DF_S1_S5.summonScore)/10
DF_Rotation = np.mean([DF_S1,DF_S2,DF_S3,DF_S4,DF_S5])
print(DF_Rotation)

NYSU2025_CARNIVAL_S1 = Banner([216, 186, 159, 158, 109, 99, 96],"cyan")
NYSU2025_CARNIVAL_S2 = Banner([118, 106, 119, 112, 26, 115, 123],"cyan")
NYSU2025_CARNIVAL_S3 = Banner([12, 52, 25, 120, 105, 121, 38],"cyan")
NYSU2025_CARNIVAL_S4 = Banner([231, 222, 217, 49, 50, 78, 80],"cyan")
NYSU2025_CARNIVAL_S5 = Banner([230, 214, 165, 157, 24],"cyan")
NYSU2025_CARNIVAL = Banner([118, 106, 119, 112, 26, 115, 123, 12, 52, 25, 120, 105, 121, 38, 231, 222, 217, 49, 50, 78, 80, 230, 214, 165, 157, 24],"cyan")
CARNIVAL_S1 = (9*NYSU2025_CARNIVAL.summonScore+20*NYSU2025_CARNIVAL_S1.summonScore)/10*5/2
CARNIVAL_S2 = (9*NYSU2025_CARNIVAL.summonScore+20*NYSU2025_CARNIVAL_S2.summonScore)/10*5/3
CARNIVAL_S3 = (9*NYSU2025_CARNIVAL.summonScore+20*NYSU2025_CARNIVAL_S3.summonScore)/10
CARNIVAL_S4 = (9*NYSU2025_CARNIVAL.summonScore+20*NYSU2025_CARNIVAL_S4.summonScore)/10
CARNIVAL_S5 = (9*NYSU2025_CARNIVAL.summonScore+20*NYSU2025_CARNIVAL_S5.summonScore)/10
Carnival_Rotation = np.mean([CARNIVAL_S1,CARNIVAL_S2,CARNIVAL_S3,CARNIVAL_S4,CARNIVAL_S5])
print(Carnival_Rotation) """