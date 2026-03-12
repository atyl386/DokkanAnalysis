import pandas as pd
import datetime as dt
from dateutil.relativedelta import relativedelta
from collections import defaultdict
from itertools import chain
import numpy as np
import os
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt

CWD = os.getcwd()
DOKKAN_ACCOUNT_XML_FILE_PATH = os.path.join(CWD, "dokkanAccount.xml")
NUM_COPIES_MAX = 5
HiPo_dupes = ["55%", "69%", "79%", "90%", "100%"]
# This number is a fudge factor to get sensible dupe improvement
NUM_COPIES = [0, 1, 2, 3, 4, 5]
DI_DICT = {-2: dict(zip(NUM_COPIES, [0.82, 0.06, 0.08, 0.02, 0.02, 0])),
     -1: dict(zip(NUM_COPIES, [0.58, 0.14, 0.19, 0.05, 0.04, 0])),
      0: dict(zip(NUM_COPIES, [0.46, 0.18, 0.24, 0.07, 0.05, 0])),
      1: dict(zip(NUM_COPIES, [0.28, 0.24, 0.32, 0.09, 0.07, 0])),
      2: dict(zip(NUM_COPIES, [0.1, 0.3, 0.4, 0.12, 0.08, 0]))
      }

def parseDokkanAccountXML(dokkanAccountXmlFilePath):
    dokkanAccountXML = ET.parse(dokkanAccountXmlFilePath)
    units = list(dokkanAccountXML.getroot())
    dokkanAccountDict = {}
    for unit in units:
        _id = int(unit.tag[1:])
        fields = list(unit)
        unitDict = {}
        for field in fields:
            if field.tag == "num_copies":
                unitDict[field.tag] = int(field.attrib["value"])
            elif field.tag == "release_date":
                unitDict[field.tag] = dt.datetime.strptime(field.attrib["value"], "%m/%y")
            elif field.tag == "rating":
                unitDict[field.tag] = int(field.attrib["value"])
            elif field.tag == "dis":
                unitDict[field.tag] = int(field.attrib["value"])
            else:
                unitDict[field.tag] = field.attrib["value"]
        dokkanAccountDict[_id] = unitDict
    return dokkanAccountDict

User = parseDokkanAccountXML(DOKKAN_ACCOUNT_XML_FILE_PATH)
nUnits = len(User)

def SummonRating(ID):
    nCopies = User[ID]["num_copies"]
    evals = [0.0] * NUM_COPIES_MAX
    now = dt.datetime.today()
    EZADiscountFactor = 1/3
    exclusivity = User[ID]["common_name"].split("_")[0]
    eza = User[ID]["eza"]
    dis = User[ID]["dis"]
    if User[ID]["common_name"] == "DF_TEQ_Golden_Frieza":
        exclusivity = "DF"
    if exclusivity in ["DFLR", "DF", "CLR", "LR"]:
        rarityScore = 7  # These are summonRatings, have to be tuned
    else:
        rarityScore = 3
    
    DI = DI_DICT[dis]
    EZADate = User[ID]["release_date"]
    if eza == "EZA":
        EZA = 6 / 7
    elif eza == "SEZA":
        EZA = 3 / 7
        futureEZA = 0
    elif eza == "None":
        EZA = 1
    else:
        raise ValueError("Invalid EZA value for unit ID " + str(ID))
    if eza != "SEZA":
        EZADate += relativedelta(months=4 * 12)
        timeUntilEZA = relativedelta(EZADate, now)
        timeUntilEZA_years = max(timeUntilEZA.years + timeUntilEZA.months/12 + timeUntilEZA.days/365, 0)
        futureEZA = rarityScore * EZADiscountFactor ** timeUntilEZA_years * DI[nCopies]
    if nCopies == 5:
        dupeImprovement = 0
    else:
        dupeImprovement = max(User[ID]["rating"] * DI[nCopies], 0)
    summonRating = max(dupeImprovement * EZA, max(0.02, futureEZA), 0)

    return summonRating


def SummonRatings():
    IDs = list(User.keys())
    commonName = [""] * nUnits
    nCopies = [0] * nUnits
    summonRatings = [0.0] * nUnits
    releaseDates = [0.0] * nUnits
    for ID in IDs:
        commonName[ID - 1] = User[ID]["common_name"]
        nCopies[ID - 1] = User[ID]["num_copies"]
        summonRatings[ID - 1] = SummonRating(ID)
        releaseDates[ID - 1] = User[ID]["release_date"]
    df = pd.DataFrame(
        data=np.transpose([IDs, commonName, nCopies, summonRatings]),
        columns=["ID", "common_name", "num_copies", "Summon Rating"],
    )
    df.set_index("ID", inplace=True)
    with pd.ExcelWriter("SummonRating.xlsx") as writer:
        df.to_excel(writer)
    
    plt.plot(releaseDates, summonRatings, "o")
    plt.xlabel("Release Date")
    plt.ylabel("Summon Rating")
    plt.title("Summon Rating vs Release Date")
    plt.show()


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
            self.summonPoints = 1.5 * summonPointsPerMulti / 300 # avg 1.5 summon rating per ticket, 300 per ticket
        else:
            self.summonPoints = 0
        if fourthiethAnniversary:
            self.featuredRate = (3 + 7 * 0.2) / (10 * 0.1 * 0.5)
            coins = 0.25 * max(list(chain(*self.summonRatings.values())))
        else:
            coins = 0
        self.summonScore = self.units * self.coin * self.featuredRate * self.tickets * self.threePlus1 * discount * self.anniBonus + self.summonPoints + coins

    def shouldSummmon(self):
        if self.summonScore > 1.5:
            return True
        else:
            return False


SummonRatings()
Dabura = Banner([462, 461, 424, 409, 460, 351, 282, 110, 311, 312], "red", gFeaturedEvery3=True, summonPoints=True)
print(Dabura.summonRatings)
print(Dabura.summonScore)
SS4Duo = Banner([458, 457, 386, 337, 3, 246, 66, 45, 38, 456], "red", threePlus1=True)
print(SS4Duo.summonRatings)
print(SS4Duo.summonScore)
ToPDuo = Banner([459, 387, 326, 254, 67, 64, 313, 376, 334, 141], "cyan", threePlus1=True)
print(ToPDuo.summonRatings)
print(ToPDuo.summonScore)
SS4DaimaGokuAdult = Banner([450, 448, 374, 327, 2, 253, 81, 320, 321, 343], "red", threePlus1=True)
print(SS4DaimaGokuAdult.summonRatings)
print(SS4DaimaGokuAdult.summonScore)
SS3DaimaVegetaAdult = Banner([449, 375, 335, 245, 83, 53, 13, 423, 186, 99], "cyan", threePlus1=True)
print(SS3DaimaVegetaAdult.summonRatings)
print(SS3DaimaVegetaAdult.summonScore + 0.9 / (500 / 14.5))
eleventhAnniversaryDF = Banner([253, 246, 218, 81, 66, 4, 63, 102, 3, 2, 37, 44, 62, 59, 85, 61, 58, 321, 320, 307, 282, 260, 233, 84, 160, 161, 110, 100, 97, 35, 42, 162, 28, 15, 5, 30, 43, 36, 17, 18, 7, 32, 31, 150, 134, 19, 45, 38, 46, 39, 34, 8, 33], "red")
print(eleventhAnniversaryDF.summonRatings)
print(eleventhAnniversaryDF.summonScore)
eleventhAnniversaryCarnival = Banner([313, 254, 245, 230, 83, 67, 79, 64, 53, 12, 23, 22, 13, 51, 1, 52, 25, 120, 105, 121, 85, 85, 117, 240], "cyan")
print(eleventhAnniversaryCarnival.summonRatings)
print(eleventhAnniversaryCarnival.summonScore)
"""NYSU2026_DF_S1 = Banner([334, 324, 308, 281, 261, 252, 247], "red")
NYSU2026_DF_S2 = Banner([218, 343, 307, 282, 260, 11, 398, 32, 33, 20], "red")
NYSU2026_DF_S3 = Banner([409, 401, 368, 351, 345, 233, 84, 110], "red")
NYSU2026_DF_S4 = Banner([218, 343, 307, 282, 260], "red")
NYSU2026_DF_S5 = Banner([409, 401, 368, 351, 345], "red")
NYSU2026_DF = Banner([409, 401, 368, 351, 345, 343, 307, 282, 260, 233, 218, 84, 110, 32, 33, 20, 11, 398], "red")
DF_S1 = (9*NYSU2026_DF.summonScore+20*NYSU2026_DF_S1.summonScore)/10*5/2
DF_S2 = (9*NYSU2026_DF.summonScore+20*NYSU2026_DF_S2.summonScore)/10*5/3
DF_S3 = (9*NYSU2026_DF.summonScore+20*NYSU2026_DF_S3.summonScore)/10
DF_S4 = (8*NYSU2026_DF.summonScore+20*NYSU2026_DF_S1.summonScore+20*NYSU2026_DF_S4.summonScore)/10
DF_S5 = (8*NYSU2026_DF.summonScore+20*NYSU2026_DF_S1.summonScore+20*NYSU2026_DF_S5.summonScore)/10
DF_Rotation = np.mean([DF_S1,DF_S2,DF_S3,DF_S4,DF_S5])
print(DF_Rotation)

NYSU2026_CARNIVAL_S1 = Banner([408, 400, 385, 376, 367, 357, 356, 350, 344], "cyan")
NYSU2026_CARNIVAL_S2 = Banner([230, 214, 165, 157, 24, 279, 278, 113, 249], "cyan")
NYSU2026_CARNIVAL_S3 = Banner([410, 366, 370, 355, 266, 105, 117, 340, 114, 318], "cyan")
NYSU2026_CARNIVAL_S4 = Banner([230, 214, 165, 157, 24], "cyan")
NYSU2026_CARNIVAL_S5 = Banner([410, 366, 370, 355, 266], "cyan")
NYSU2026_CARNIVAL = Banner([410, 370, 366, 355, 266, 230, 214, 165, 157, 24, 279, 278, 113, 249, 105, 117, 340, 114, 318],"cyan")
CARNIVAL_S1 = (9*NYSU2026_CARNIVAL.summonScore+20*NYSU2026_CARNIVAL_S1.summonScore)/10*5/2
CARNIVAL_S2 = (9*NYSU2026_CARNIVAL.summonScore+20*NYSU2026_CARNIVAL_S2.summonScore)/10*5/3
CARNIVAL_S3 = (9*NYSU2026_CARNIVAL.summonScore+20*NYSU2026_CARNIVAL_S3.summonScore)/10
CARNIVAL_S4 = (8*NYSU2026_CARNIVAL.summonScore+20*NYSU2026_CARNIVAL_S1.summonScore+20*NYSU2026_CARNIVAL_S4.summonScore)/10
CARNIVAL_S5 = (8*NYSU2026_CARNIVAL.summonScore+20*NYSU2026_CARNIVAL_S1.summonScore+20*NYSU2026_CARNIVAL_S5.summonScore)/10
Carnival_Rotation = np.mean([CARNIVAL_S1,CARNIVAL_S2,CARNIVAL_S3,CARNIVAL_S4,CARNIVAL_S5])
print(Carnival_Rotation)
GohanGamma1 = Banner([444, 358, 161, 150, 37, 35, 40], "red", summonPoints=True, threePlus1=True)
print(GohanGamma1.summonRatings)
print(GohanGamma1.summonScore)
Gamma2Piccolo = Banner([445, 359, 160, 134, 44, 47, 42], "red", threePlus1=True)
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
#WWDL_1 = Banner([36, 19, 31, 30, 17, 150, 39, 34, 8, 33, 40, 140, 11, 170, 21, 257, 41, 21, 93, 163, 135, 127, 126, 86, 104, 142, 142, 60, 60, 60, 128, 128, 128, 127, 10, 188, 188, 183, 183, 116, 25, 116, 116, 25, 25, 101, 101, 211, 25, 101, 116, 25, 25, 25, 101, 170],'red', discount=50*(2 + 10 * 2)/100)
#print(WWDL_1.summonScore)
#WWDL_2 = Banner([25, 18, 5, 7, 32, 134, 45, 38, 46, 25, 10, 20, 9, 25, 170, 48, 48, 25, 164, 155, 98, 170, 146, 131, 25, 145, 129, 25, 54, 8, 25, 132, 116, 25, 146, 116, 8, 126, 8, 25, 116, 25, 25, 48, 170, 41, 25, 48, 48, 25, 156, 25, 25, 25, 101, 101],'red', discount=50*(2 + 10 * 2)/100)
#print(WWDL_2.summonScore)"""