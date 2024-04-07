from getUnitFromUser import *
import pandas as pd
from scipy.stats import truncnorm
from dokkanAccount import User
import shutil
import pickle

nUnits = len(User)


def save_object(obj, filename):
    obj.inputHelper.file = None
    with open(filename, "wb") as outp:  # Overwrites any existing file.
        pickle.dump(obj, outp, pickle.HIGHEST_PROTOCOL)
    outp.close()


def summaryStats(attributeValues):
    # Compute means and stds for each attribute
    means = np.zeros((NUM_EVAL_TURNS, NUM_ATTRIBUTES))
    stds = np.zeros((NUM_EVAL_TURNS, NUM_ATTRIBUTES))
    for turn in range(NUM_EVAL_TURNS):
        for j in range(NUM_ATTRIBUTES):
            means[turn, j] = np.mean(attributeValues[:, turn, j])
            stds[turn, j] = np.std(attributeValues[:, turn, j])
    return [means, stds]


def normalizeUnit(unit, means, stds):
    # Normalise attributes and save unit objects in pkl files
    normalisedAttributes = np.zeros((NUM_EVAL_TURNS, NUM_ATTRIBUTES))
    attributes = unit.getAttributes()
    for j in range(NUM_ATTRIBUTES):
        normalisedAttributes[:, j] = (attributes[:, j] - means[:, j]) / stds[:, j]
    unit.setAttributes(normalisedAttributes)
    save_object(
        unit,
        "C:/Users/Tyler/Documents/DokkanAnalysis/DokkanUnits/"
        + HIPO_DUPES[unit.nCopies - 1]
        + "/unit_"
        + unit.id
        + ".pkl",
    )


def writeSummary(units, attributeValues, evaluations):
    # Create Attribute data frame for each turn
    for nCopies in range(1, NUM_COPIES_MAX + 1):
        df1 = pd.DataFrame(
            data=[
                [
                    str(i + 1),
                    units[nCopies - 1][i].commonName,
                    evaluations[i, nCopies - 1],
                ]
                for i in range(nUnits)
            ],
            columns=["ID", "Common Name", "Evaluation"],
        )
        weightedSums = np.zeros((nUnits, NUM_ATTRIBUTES))
        for turn in range(NUM_EVAL_TURNS):
            weightedSums = np.add(weightedSums, overallTurnWeights[turn] * attributeValues[:, turn, :, nCopies - 1])
        with pd.ExcelWriter("DokkanUnits/" + HIPO_DUPES[nCopies - 1] + "/unitSummary.xlsx") as writer:
            df = df1.join(pd.DataFrame(data=weightedSums, columns=ATTTRIBUTE_NAMES)).set_index("ID")
            df.to_excel(writer, sheet_name="Overall")
            for turn in range(NUM_EVAL_TURNS):
                df = df1.join(
                    pd.DataFrame(data=attributeValues[:, turn, :, nCopies - 1], columns=ATTTRIBUTE_NAMES)
                ).set_index("ID")
                df.to_excel(writer, sheet_name="turn " + str(turn + 1))


class Evaluator:
    def __init__(self, turnWeights, attributeWeights):
        self.turnWeights = turnWeights
        self.attributeWeights = np.array(list(attributeWeights))
        self.normaliseWeights()

    def normaliseWeights(self):
        self.turnWeights = self.turnWeights / np.sqrt((self.turnWeights**2).sum())
        self.attributeWeights = self.attributeWeights / np.sqrt((self.attributeWeights**2).sum())

    def evaluate(self, unit):
        score = 0.0
        for i, attribute in enumerate(unit.getAttributes().T):
            score += self.attributeWeights[i] * np.dot(self.turnWeights, attribute)
        return score


a, b = (1 - AVG_PEAK_TURN) / PEAK_TURN_STD, (99 - AVG_PEAK_TURN) / PEAK_TURN_STD
turnDistribution = truncnorm(a, b, AVG_PEAK_TURN, PEAK_TURN_STD)

overallTurnWeights = turnDistribution.cdf(np.arange(2, NUM_EVAL_TURNS + 2)) - turnDistribution.cdf(
    np.arange(1, NUM_EVAL_TURNS + 1)
)
attributeDict = {
    "Leader Skill": 3,
    "SBR": 0.5,
    "HP": 2,
    "Useability": 4,
    "Healing": 1.5,
    "Support": 5,
    "APT": 10,
    "Normal Defence": 11,
    "Super Attack Defence": 9,
    "Slot Bonus": 2
}
overallEvaluator = Evaluator(overallTurnWeights, attributeDict.values())

reCalc = True
analyseHiPo = True
optimiseSlots = False
if reCalc:
    dokkanUnitsPath = os.path.join(CWD, "dokkanUnits")
    if os.path.exists(dokkanUnitsPath):
        for item in os.listdir(dokkanUnitsPath):
            shutil.rmtree(os.path.join(dokkanUnitsPath, item))
    else:
        os.mkdir(dokkanUnitsPath)
    for dir in HIPO_DUPES:
        os.mkdir(os.path.join(dokkanUnitsPath, dir))
    attributeValues = np.zeros((nUnits, NUM_EVAL_TURNS, NUM_ATTRIBUTES, NUM_COPIES_MAX))
    units = [[None] * nUnits for i in range(NUM_COPIES_MAX)]
    evaluations = np.zeros((nUnits, NUM_COPIES_MAX))
    reverseOrderIDs = np.flip(list(User.keys()))
    for ID in reverseOrderIDs:
        print(ID)
        units[-1][ID - 1] = Unit(
            ID,
            User[ID]["Common Name"],
            NUM_COPIES_MAX,
            User[ID]["BRZ Equip"],
            User[ID]["HiPo Choice # 1"],
            User[ID]["HiPo Choice # 2"],
            User[ID]["Slots"],
        )
        attributeValues[ID - 1, :, :, -1] = units[-1][ID - 1].getAttributes()

    [rainbowMeans, rainbowStds] = summaryStats(attributeValues[:, :, :, -1])
    for ID in reverseOrderIDs:
        normalizeUnit(units[-1][ID - 1], rainbowMeans, rainbowStds)
        evaluations[ID - 1][-1] = overallEvaluator.evaluate(units[-1][ID - 1])
    if optimiseSlots:
        for ID in reverseOrderIDs:
            best_slots = copy.copy(User[ID]["Slots"])
            stateIdx = 0
            nextTurn = 1
            while nextTurn < MAX_TURN:
                best_eval = -np.inf
                for slot in SLOTS:
                    best_slots[stateIdx] = slot
                    unit = Unit(
                        ID,
                        User[ID]["Common Name"],
                        NUM_COPIES_MAX,
                        User[ID]["BRZ Equip"],
                        User[ID]["HiPo Choice # 1"],
                        User[ID]["HiPo Choice # 2"],
                        best_slots,
                        save=False,
                    )
                    normalizeUnit(unit, rainbowMeans, rainbowStds)
                    evaluation = overallEvaluator.evaluate(unit)
                    if evaluation > best_eval:
                        best_slot = slot
                        best_eval = evaluation
                best_slots[stateIdx] = best_slot
                stateIdx += 1
                nextTurn += RETURN_PERIOD_PER_SLOT[best_slot - 1]
            if best_slots == User[ID]["Slots"]:
                print(ID, "default Slots", User[ID]["Common Name"])
            else:
                print(ID, best_slots, User[ID]["Common Name"])
    if analyseHiPo:
        for ID in reverseOrderIDs:
            best_HiPo = None
            best_eval = evaluations[ID - 1][-1]
            for i, HiPo_build in enumerate(HIPO_BUILDS):
                HiPo_unit = Unit(
                    ID,
                    User[ID]["Common Name"],
                    NUM_COPIES_MAX,
                    HiPo_build[0],
                    HiPo_build[1],
                    HiPo_build[2],
                    User[ID]["Slots"],
                    save=False,
                )
                normalizeUnit(HiPo_unit, rainbowMeans, rainbowStds)
                HiPo_evaluation = overallEvaluator.evaluate(HiPo_unit)
                if HiPo_evaluation > best_eval:
                    best_HiPo = i
                    best_eval = HiPo_evaluation
            if best_HiPo == None:
                print(ID, "default HiPo", HiPo_unit.name)
            else:
                print(ID, HIPO_BUILDS[best_HiPo], HiPo_unit.name)
    for ID in reverseOrderIDs:
        print(ID)
        for nCopies in range(1, NUM_COPIES_MAX):
            units[nCopies - 1][ID - 1] = Unit(
                ID,
                User[ID]["Common Name"],
                nCopies,
                User[ID]["BRZ Equip"],
                User[ID]["HiPo Choice # 1"],
                User[ID]["HiPo Choice # 2"],
                User[ID]["Slots"],
            )
            attributeValues[ID - 1, :, :, nCopies - 1] = normalizeUnit(
                units[nCopies - 1][ID - 1], rainbowMeans, rainbowStds
            )
            evaluations[ID - 1][nCopies - 1] = overallEvaluator.evaluate(units[nCopies - 1][ID - 1])
    maxEvaluation = max(evaluations[:, -1])
    evaluations = logisticMap(evaluations, maxEvaluation)
    writeSummary(units, attributeValues, evaluations)

scores = [0.0] * nUnits
units = [None] * nUnits
for i in range(nUnits):
    pkl = open("C:/Users/Tyler/Documents/DokkanAnalysis/DokkanUnits/100%/unit_" + str(i + 1) + ".pkl", "rb")
    units[i] = pickle.load(pkl)
    pkl.close()
    scores[i] = overallEvaluator.evaluate(units[i])
ranking = np.flip(np.argsort(scores))
rankingFilePath = os.path.join(CWD, "DokkanKitOutputs", "ranking.txt")
rankingFile = open(rankingFilePath, "w") 
for rank in ranking:
    rankingFile.write(f"{units[rank].commonName} \n")
