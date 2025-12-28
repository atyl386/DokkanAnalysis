from getUnitFromUser import *
import pandas as pd
from scipy.stats import truncnorm
import shutil
import pickle
from multiprocessing import Pool
import tqdm

HIPO_DUPES = ["55%", "69%", "79%", "90%", "100%"]

reCalc = True
analyseHiPo = False
optimiseslots = False
accountRanking = True
useMultiprocessing = True
updateEvaluationUnits = False
onlyEvaluationUnits = True
writeSummaryFiles = False


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
            elif field.tag == "slots":
                unitDict[field.tag] = literal_eval(field.attrib["value"])
            elif field.tag == "eval":
                unitDict[field.tag] = field.attrib["value"] == "True"
            else:
                unitDict[field.tag] = field.attrib["value"]
        dokkanAccountDict[_id] = unitDict
    return dokkanAccountDict


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
    return unit

def writeNCopySummary(units, attributeValues, evaluations, nCopies):
    idx = nCopies - 1   
    dfBase = pd.DataFrame(
        {
            "ID": [u.id for u in units[idx]],
            "common_name:": [u.commonName for u in units[idx]],
            "Evaluation": evaluations[:, idx],
        }
    ).set_index("ID")
    
    weightedSums = np.tensordot(
        attributeValues[:, :, :, idx],
        overallTurnWeights,
        axes=(1, 0)
    )

    outputPath = f"DokkanUnits/{HIPO_DUPES[idx]}/unitSummary.xlsx"

    with pd.ExcelWriter(outputPath, engine="xlsxwriter") as writer:
        dfOverall = pd.concat(
            [dfBase, pd.DataFrame(weightedSums, columns=ATTTRIBUTE_NAMES, index=dfBase.index)],
            axis=1,
        )
        dfOverall.to_excel(writer, sheet_name="Overall")
        for turn in range(NUM_EVAL_TURNS):
            dfTurn = pd.concat(
                [dfBase, pd.DataFrame(attributeValues[:, turn, :, idx], columns=ATTTRIBUTE_NAMES, index=dfBase.index)],
                axis=1,
            )
            dfTurn.to_excel(writer, sheet_name="turn " + str(turn + 1))

def writeSummary(units, attributeValues, evaluations, useMultiprocessing): 
    args = (
        (units, attributeValues, evaluations, nCopies)
        for nCopies in range(1, NUM_COPIES_MAX + 1)
    )

    if False: # multiprocessing is not working
        with Pool() as pool:
            list(
                tqdm.tqdm(
                    pool.starmap(writeNCopySummary, args),
                    total=NUM_COPIES_MAX,
                )
            )
    else:
        for nCopies in tqdm.tqdm(range(1, NUM_COPIES_MAX + 1), total=NUM_COPIES_MAX):
            writeNCopySummary(units, attributeValues, evaluations, nCopies)

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


def processRainbowUnit(ID, User, NUM_COPIES_MAX):
    unit = Unit(
        ID,
        User[ID]["common_name"],
        NUM_COPIES_MAX,
        User[ID]["BRZ_equip"],
        User[ID]["HiPo_choice_1"],
        User[ID]["HiPo_choice_2"],
        User[ID]["slots"],
    )
    attributeValues = unit.getAttributes()
    return unit, attributeValues


def processOtherUnit(ID, rainbowMeans, rainbowStds, overallEvaluator, User, NUM_COPIES_MAX):
    units = [None] * (NUM_COPIES_MAX - 1)
    attributeValues = np.zeros((NUM_EVAL_TURNS, NUM_ATTRIBUTES, NUM_COPIES_MAX - 1))
    evaluations = np.zeros(NUM_COPIES_MAX - 1)
    for nCopies in range(1, NUM_COPIES_MAX):
        units[nCopies - 1] = Unit(
            ID,
            User[ID]["common_name"],
            nCopies,
            User[ID]["BRZ_equip"],
            User[ID]["HiPo_choice_1"],
            User[ID]["HiPo_choice_2"],
            User[ID]["slots"],
        )
        attributeValues[:, :, nCopies - 1] = units[nCopies - 1].getAttributes()
        normalizeUnit(units[nCopies - 1], rainbowMeans, rainbowStds)
        evaluations[nCopies - 1] = overallEvaluator.evaluate(units[nCopies - 1])
    return units, attributeValues, evaluations


def optimiseSlots(ID, User, overallEvaluator, dokkanAccountXML, dokkanAccountRoot, rainbowMeans, rainbowStds):
    if ID in FIXED_SLOT_UNITS:
        return
    best_slots = copy.copy(User[ID]["slots"])
    stateIdx = 0
    nextTurn = 1
    while nextTurn < MAX_TURN:
        best_eval = -np.inf
        for slot in SLOTS:
            best_slots[stateIdx] = slot
            unit = Unit(
                ID,
                User[ID]["common_name"],
                NUM_COPIES_MAX,
                User[ID]["BRZ_equip"],
                User[ID]["HiPo_choice_1"],
                User[ID]["HiPo_choice_2"],
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
    dokkanAccountRoot.find(f"_{ID}").find("slots").set("value", str(best_slots))
    dokkanAccountXML.write(DOKKAN_ACCOUNT_XML_FILE_PATH, encoding="utf-8")


def optimiseHiPo(ID, User, overallEvaluator, dokkanAccountXML, dokkanAccountRoot, rainbowMeans, rainbowStds):
    best_HiPo = -1
    best_eval = -np.inf
    for i, HiPo_build in enumerate(HIPO_BUILDS):
        HiPo_unit = Unit(
            ID,
            User[ID]["common_name"],
            NUM_COPIES_MAX,
            HiPo_build[0],
            HiPo_build[1],
            HiPo_build[2],
            User[ID]["slots"],
            save=False,
        )
        normalizeUnit(HiPo_unit, rainbowMeans, rainbowStds)
        HiPo_evaluation = overallEvaluator.evaluate(HiPo_unit)
        if HiPo_evaluation > best_eval:
            best_HiPo = i
            best_eval = HiPo_evaluation
    unit = dokkanAccountRoot.find(f"_{ID}")
    for i, equip in enumerate(["BRZ_equip", "HiPo_choice_1", "HiPo_choice_2"]):
        unit.find(equip).set("value", HIPO_BUILDS[best_HiPo][i])
    dokkanAccountXML.write(DOKKAN_ACCOUNT_XML_FILE_PATH, encoding="utf-8")

def processRainbowUnitWrapper(args):
    return processRainbowUnit(*args)

def processOtherUnitWrapper(args):
    return processOtherUnit(*args)

if __name__ == "__main__":
    User = parseDokkanAccountXML(DOKKAN_ACCOUNT_XML_FILE_PATH)
    if onlyEvaluationUnits:
        evalUnitIDs = [ID for ID in User.keys() if User[ID]["eval"]]
    else:
        evalUnitIDs = User.keys()
    nUnits = len(evalUnitIDs)
    a, b = (1 - AVG_PEAK_TURN) / PEAK_TURN_STD, (99 - AVG_PEAK_TURN) / PEAK_TURN_STD
    turnDistribution = truncnorm(a, b, AVG_PEAK_TURN, PEAK_TURN_STD)

    overallTurnWeights = turnDistribution.cdf(np.arange(2, NUM_EVAL_TURNS + 2)) - turnDistribution.cdf(
        np.arange(1, NUM_EVAL_TURNS + 1)
    )
    attributeDict = {
        "Leader Skill": 2,
        "SBR": 1,
        "HP": 1.5,
        "Useability": 6,
        "Healing": 2,
        "Support": 5,
        "APT": 12,
        "Normal Defence": 12,
        "Super Attack Defence": 8,
        "Slot Bonus": 12,
    }

    top100AttributeDict = copy.copy(attributeDict)
    top100AttributeDict["Leader Skill"] = 0
    top100AttributeDict["SBR"] = 0
    top100AttributeDict["Useability"] = 0

    overallEvaluator = Evaluator(overallTurnWeights, attributeDict.values())
    top100Evaluator = Evaluator(overallTurnWeights, top100AttributeDict.values())

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
        reverseOrderIDs = np.flip(evalUnitIDs)
        print("Processing Rainbow Units")
        rainbowUnitArgsIter = (
            (ID, User, NUM_COPIES_MAX)
            for ID in reverseOrderIDs
        )
        if useMultiprocessing:
            with Pool() as pool:
                output = list(
                    tqdm.tqdm(
                        pool.imap(processRainbowUnitWrapper, rainbowUnitArgsIter),
                        total=nUnits
                    ),
                )
        else:
            output = [processRainbowUnit(*args) for args in tqdm.tqdm(rainbowUnitArgsIter, total=nUnits)]
        output = np.asarray(output, dtype=object)
        units[-1] = np.array(list(output[:, 0]))
        attributeValues[:, :, :, -1] = list(output[:, 1])
        [rainbowMeans, rainbowStds] = summaryStats(attributeValues[:, :, :, -1])
        for i in range(nUnits):
            normalizeUnit(units[-1][i], rainbowMeans, rainbowStds)
            evaluations[i, -1] = overallEvaluator.evaluate(units[-1][i])
        dokkanAccountXML = ET.parse(DOKKAN_ACCOUNT_XML_FILE_PATH)
        dokkanAccountRoot = dokkanAccountXML.getroot()
        if optimiseslots:
            print("Optimising Slots")
            if False: # multiprocessing is not working
                with Pool() as pool:
                    pool.starmap(
                        optimiseSlots,
                        tqdm.tqdm([(ID, User, overallEvaluator, dokkanAccountXML, dokkanAccountRoot, rainbowMeans, rainbowStds) for ID in reverseOrderIDs], total=nUnits),
                    )
            else:
                for ID in reverseOrderIDs:
                    optimiseSlots(ID, User, overallEvaluator, dokkanAccountXML, dokkanAccountRoot, rainbowMeans, rainbowStds)
        if analyseHiPo:
            print("Optimising Hidden Potential")
            if False: # multiprocessing is not working
                with Pool() as pool:
                    pool.starmap(
                        optimiseHiPo,
                        tqdm.tqdm([(ID, User, overallEvaluator, dokkanAccountXML, dokkanAccountRoot, rainbowMeans, rainbowStds) for ID in reverseOrderIDs], total=nUnits),
                    )
            else:
                for ID in reverseOrderIDs:
                    optimiseHiPo(ID, User, overallEvaluator, dokkanAccountXML, dokkanAccountRoot, rainbowMeans, rainbowStds)
        if updateEvaluationUnits:
            meanRainbowEvaluation = np.mean(evaluations[:, -1])
            stdRainbowEvations = np.std(evaluations[:, -1])
            for i, ID in enumerate(reverseOrderIDs):
                evalNode = dokkanAccountRoot.find(f"_{ID}/eval")
                if evaluations[i, -1] < MIN_EVALUATION:
                    evalNode.set("value", "False")
                else:
                    evalNode.set("value", "True")
            dokkanAccountXML.write(DOKKAN_ACCOUNT_XML_FILE_PATH, encoding="utf-8")
            exit()
        print("Processing Other Units")
        otherUnitArgsIter = (
            (ID, rainbowMeans, rainbowStds, overallEvaluator, User, NUM_COPIES_MAX)
            for ID in reverseOrderIDs
        )
        if useMultiprocessing:
            with Pool() as pool:
                output = list(
                    tqdm.tqdm(
                        pool.imap(processOtherUnitWrapper, otherUnitArgsIter),
                        total=nUnits,
                    )
                )
        else:
            output = [processOtherUnit(*args) for args in tqdm.tqdm(otherUnitArgsIter, total=nUnits)]
        output = np.asarray(output, dtype=object)
        units[:-1] = np.array(list(output[:, 0])).T
        attributeValues[:, :, :, :-1] = list(output[:, 1])
        evaluations[:, :-1] = list(output[:, 2])
        maxEvaluation = max(evaluations[:, -1])
        print("Computing Ranking Scores")
        evaluations = logisticMap(evaluations, maxEvaluation)
        if writeSummaryFiles:
            print("Writing results to files")
            writeSummary(units, attributeValues, evaluations, useMultiprocessing)

    # Calculate Overall Rankings
    scores = [0.0] * nUnits
    units = [None] * nUnits
    for i, ID in enumerate(evalUnitIDs):
        pkl = open("C:/Users/Tyler/Documents/DokkanAnalysis/DokkanUnits/100%/unit_" + str(ID) + ".pkl", "rb")
        units[i] = pickle.load(pkl)
        pkl.close()
        scores[i] = overallEvaluator.evaluate(units[i])
    ranking = np.flip(np.argsort(scores))
    rankingFilePath = os.path.join(CWD, "DokkanKitOutputs", "overallRanking.txt")
    rankingFile = open(rankingFilePath, "w")
    for rank in ranking:
        rankingFile.write(f"{units[rank].commonName} \n")

    if accountRanking:
        # Calculate Account Rankings
        scores = []
        units = []
        for ID in evalUnitIDs:
            numCopies = User[ID]["num_copies"]
            if numCopies > 0:
                pkl = open(
                    "C:/Users/Tyler/Documents/DokkanAnalysis/DokkanUnits/"
                    + HIPO_DUPES[numCopies - 1]
                    + "/unit_"
                    + str(ID)
                    + ".pkl",
                    "rb",
                )
                units.append(pickle.load(pkl))
                pkl.close()
                scores.append(top100Evaluator.evaluate(units[-1]))
        ranking = np.flip(np.argsort(scores))
        rankingFilePath = os.path.join(CWD, "DokkanKitOutputs", "accountRanking.txt")
        rankingFile = open(rankingFilePath, "w")
        for rank in ranking:
            rankingFile.write(f"{units[rank].commonName} \n")
