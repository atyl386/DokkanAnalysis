import datetime as dt
from dokkanUnitHelperFunctions import *
import xml.etree.ElementTree as ET
import math
import click as clc
import glob

# TODO:
# Fix DAIMA SS4 Goku's crit in slot 2,3 from activating too late, shouldn't be after supering
# Make support section of input .xml if not used, uses the default support values
# - For units that get important buffs next to a unit they will always be next to, should include those buffs in their kit
# - Fix recievedOREvaded to use recievd and evaded attacks in atk calc
# - Make better way to integrate the no eval unit finding into normal evaluation run
# - Simplify getEventFactor code
# - Implement dodging counters, i.e. TEQ UI Goku
# - Implement Super EZA summoning bonuses 9don't think this really needs to be done as they aren't being added to banners)
# - Update rainbow orb changing units for those with don't change their own type
# - Try factor out some code within ability class into class functions
# - Make it ask if links have changed for a new form.
# - Change question from last turn buff ends on to duration as more explicit
# - Also might want to include attack all in atk calcs.
# - If ever do DPT, instead of APT, should use Lowers DEF in calcs. But most enemies are immunue to it anyway, so not a big deal.
# - Add some functionality that can update existing input .txt files with new questions (assuming not relevant to exisiting unit)
# - Instead of asking user how many of something, should ask until they enteran exit key ak a while loop instead of for loop
# - Once calculate how many supers do on turn 1, use this in the SBR calculation for debuffs on super(). i.e. SBR should be one of the last things to be calculated

##################################################### Helper Functions ############################################################################


def abilityQuestionaire(form, abilityPrompt, abilityClass, parameterPrompts=[], types=[], defaults=[]):
    numAbilities = form.unit.inputHelper.getAndSaveUserInput(abilityPrompt, default=0)
    abilities = []
    abilityTypeElement = form.unit.inputHelper.parent
    for i in range(numAbilities):
        form.unit.inputHelper.parent = form.unit.inputHelper.getChildElement(abilityTypeElement, f"ability_{i + 1}")
        parameters = []
        for j, parameterPrompt in enumerate(parameterPrompts):
            if len(types) == 0:  # If don't care about prompt choices
                parameters.append(form.unit.inputHelper.getAndSaveUserInput(parameterPrompt))
            else:
                parameters.append(
                    form.unit.inputHelper.getAndSaveUserInput(parameterPrompt, type=types[j], default=defaults[j])
                )
        if issubclass(abilityClass, PassiveAbility):
            effect = form.unit.inputHelper.getAndSaveUserInput(
                "What type of buff does the unit get?", type=clc.Choice(EFFECTS, case_sensitive=False), default="ATK"
            )
            activationProbability = form.unit.inputHelper.getAndSaveUserInput(
                "What is the probability this ability activates?", default=1.0
            )
            # If the status of this ability is known beforehand, scale it to account for this fact.
            if activationProbability != 1:
                knownApriori = yesNo2Bool[
                    form.unit.inputHelper.getAndSaveUserInput(
                        "Is the status of this ability known beforehand?",
                        type=clc.Choice(YES_NO, case_sensitive=False),
                        default="N",
                    )
                ]
            else:
                knownApriori = False
            buff = form.unit.inputHelper.getAndSaveUserInput("What is the value of the buff?", default=1.0)
            ability = abilityClass(form, activationProbability, knownApriori, effect, buff, args=parameters)
        elif issubclass(abilityClass, SingleTurnAbility):
            ability = abilityClass(form, parameters)
        abilities.append(ability)
    return abilities


def getCondition(inputHelper):
    """
    Askes the user questions to determine which Condition class(es) apply and returns them. Only want once per condition set.
    """
    abilityElement = inputHelper.parent
    numConditions = inputHelper.getAndSaveUserInput("How many conditions have to be met?", default=0)
    if numConditions < 1:
        return numConditions
    if numConditions > 1:
        operator = inputHelper.getAndSaveUserInput(
            "What is the condition logic?", type=clc.Choice(CONDITION_LOGIC), default="AND"
        )
        if numConditions > 2:
            compositeConditionElement = inputHelper.getChildElement(abilityElement, "composte_condition")
            inputHelper.parent = inputHelper.getChildElement(compositeConditionElement, "condition_a")
            conditionA = getCondition(inputHelper)
            inputHelper.parent = inputHelper.getChildElement(compositeConditionElement, "condition_b")
            conditionB = getCondition(inputHelper)
            return CompositeCondition(operator, [conditionA, conditionB])
    condition = [None] * numConditions

    for i in range(numConditions):
        inputHelper.parent = inputHelper.getChildElement(abilityElement, f"condition_{i + 1}")
        conditionType = inputHelper.getAndSaveUserInput(
            f"What type of condition is # {i + 1}?", type=clc.Choice(CONDITIONS, case_sensitive=False), default="Turn"
        )
        match conditionType:
            case "Turn":
                turnCondition = inputHelper.getAndSaveUserInput("What is the ability turn condition?", default=5)
                condition[i] = TurnCondition(turnCondition)
            case "TransformationTurn":
                turnCondition = inputHelper.getAndSaveUserInput(
                    "What is the transformation turn condition (relative to the form's starting turn)?", default=5
                )
                condition[i] = NextTurnCondition(turnCondition)
            case "Max HP":
                maxHpCondition = inputHelper.getAndSaveUserInput("What is the maximum HP condition?", default=0.7)
                condition[i] = MaxHpCondition(maxHpCondition)
            case "Min HP":
                minHpCondition = inputHelper.getAndSaveUserInput("What is the minimum HP condition?", default=0.7)
                condition[i] = MinHpCondition(minHpCondition)
            case "Max Enemy HP":
                enemyMaxHpCondition = inputHelper.getAndSaveUserInput(
                    "What is the maximum enemy HP condition?", default=0.5
                )
                condition[i] = EnemyMaxHpCondition(enemyMaxHpCondition)
            case "Min Enemy HP":
                enemyMinHpCondition = inputHelper.getAndSaveUserInput(
                    "What is the minimum enemy HP condition?", default=0.5
                )
                condition[i] = EnemyMinHpCondition(enemyMinHpCondition)
            case "Num Attacks Performed":
                numAttacksPerformedCondition = inputHelper.getAndSaveUserInput(
                    "How many performed attacks are required?", default=5
                )
                condition[i] = AttacksPerformedCondition(numAttacksPerformedCondition)
            case "Num Super Attacks Performed":
                numSupersPerformedCondition = inputHelper.getAndSaveUserInput(
                    "How many performed supers are required?", default=4
                )
                condition[i] = SupersPerformedCondition(numSupersPerformedCondition)
            case "Num Attacks Received":
                numAttacksReceivedCondition = inputHelper.getAndSaveUserInput(
                    "How many received attacks are required?", default=5
                )
                condition[i] = AttacksReceivedCondition(numAttacksReceivedCondition)
            case "Num Attacks Evaded":
                numAttacksEvadedCondition = inputHelper.getAndSaveUserInput(
                    "How many evaded attacks are required?", default=5
                )
                condition[i] = AttacksEvadedCondition(numAttacksEvadedCondition)
            case "Finish Skill Activation":
                requiredCharge = inputHelper.getAndSaveUserInput("What is the required charge condition?", default=30)
                condition[i] = FinishSkillActivatedCondition(requiredCharge)
            case "Deliver Final Blow":
                condition[i] = FinalBlowCondition()
            case "Revive":
                condition[i] = ReviveCondition()
            case "EX Chance":
                chance = inputHelper.getAndSaveUserInput("What is the EX Chance condition?", default=0.5)
                condition[i] = ChanceEXSuperCondition(chance)
            case "EX Crit":
                condition[i] = CritEXSuperCondition()
            case "EX Num Attacks Performed":
                numAttacksPerformedCondition = inputHelper.getAndSaveUserInput(
                    "How many performed attacks are required?", default=0
                )
                condition[i] = NumAttacksPerformedEXSuperCondition(numAttacksPerformedCondition)
            case "EX Ki":
                kiCondition = inputHelper.getAndSaveUserInput("How much ki is required?", default=12)
                condition[i] = KiEXSuperCondition(kiCondition)
            case "NA":
                condition[i] = Condition()
            case _:
                raise Exception(f"{conditionType} Condition type not implemented!")
    if numConditions == 2:
        return CompositeCondition(operator, condition)
    else:
        return condition[0]


# Overwrite this class function as has additional
def updateAttacksReceivedAndEvaded(self, state, effect):
    if state.evadeFirstNormalChance > 0:
        evadeFirstAttack = 1 - DODGE_CANCEL_FACTOR * (1 - state.buff["Disable Evasion Cancel"])
    else:
        evadeFirstAttack = 0
    pEvade = self.prob * (1 - DODGE_CANCEL_FACTOR * (1 - state.buff["Disable Evasion Cancel"]))
    if state.numAttacksDirected == NUM_ATTACKS_PER_TURN:
        numAttacksDirectedBeforeAttacking = NUM_CUMULATIVE_ATTACKS_BEFORE_ATTACKING[state.slot - 1]
    else:
        numAttacksDirectedBeforeAttacking = NUM_ATTACKS_DIRECTED_BEFORE_ATTACKING[state.slot - 1]
    numAttacksDirectedAfterAttacking = state.numAttacksDirected - numAttacksDirectedBeforeAttacking
    if effect == "EvasionA" or effect == "Nullify":
        state.numAttacksReceivedBeforeAttacking = max(numAttacksDirectedBeforeAttacking - evadeFirstAttack, 0) * (1 - pEvade)
        state.numAttacksEvadedBeforeAttacking = max(numAttacksDirectedBeforeAttacking - evadeFirstAttack, 0) * pEvade + evadeFirstAttack
        state.numSuperAttacksReceivedBeforeAttacking = state.numSuperAttacksDirectedBeforeAttacking * (1 - pEvade) * (1 - state.multiChanceBuff["Nullify"].prob)
    elif effect == "EvasionB" or effect == "Nullify":
        state.numAttacksReceivedAfterAttacking = numAttacksDirectedAfterAttacking * (1 - pEvade)
        state.numAttacksEvadedAfterAttacking = numAttacksDirectedAfterAttacking * pEvade
        state.numSuperAttacksReceivedAfterAttacking = state.numSuperAttacksDirectedAfterAttacking * (1 - pEvade) * (1 - state.multiChanceBuff["Nullify"].prob)
    else:
        raise Exception(f"{effect} effect update attacks received not implemented!")

    state.numAttacksReceived = state.numAttacksReceivedBeforeAttacking + state.numAttacksReceivedAfterAttacking
    state.numAttacksEvaded = state.numAttacksEvadedBeforeAttacking + state.numAttacksEvadedAfterAttacking
    state.numSuperAttacksReceived = state.numSuperAttacksReceivedBeforeAttacking + state.numSuperAttacksReceivedAfterAttacking


MultiChanceBuff.updateAttacksReceivedAndEvaded = updateAttacksReceivedAndEvaded


######################################################### Classes #################################################################


class InputHelper:
    def __init__(self, id, commonName):
        matchingFilePaths = glob.glob(os.path.join(CWD, "DokkanKits", "*_" + id + ".xml"))
        assert(len(matchingFilePaths) <= 1), f"Multiple files found for unit {id}"
        if len(matchingFilePaths) == 1:
            self.filePath = matchingFilePaths[0]
            self.tree = ET.parse(self.filePath)
            self.parent = self.tree.getroot()
        else:
            self.filePath = os.path.join(CWD, "DokkanKits", commonName + "_" + id + ".xml")
            self.parent = ET.Element("inputTree")
            self.tree = ET.ElementTree(self.parent)
        self.parentMap = {}

    def getAndSaveUserInput(self, prompt, type=None, default=None):
        child = self.parent.find(f'./input[@prompt="{prompt}"]')
        if child == None:
            if type == None and default == None:
                response = clc.prompt(prompt)
            elif type == None:
                response = clc.prompt(prompt, default=default)
            else:
                response = clc.prompt(prompt, type=type, default=default)
            child = ET.SubElement(self.parent, "input")
            child.set("prompt", prompt)
            child.set("response", str(response))
            ET.indent(self.tree, space="\t", level=0)
            self.tree.write(self.filePath, encoding="utf-8")
        else:
            response = simplest_type(child.attrib["response"])
        self.parentMap[child] = self.parent
        return response

    def getChildElement(self, parent, childTag):
        child = parent.find(f"{childTag}")
        if child == None:
            i = list(self.parentMap.values()).count(parent)
            child = ET.Element(f"{childTag}")
            parent.insert(i, child)
        self.parentMap[child] = parent
        return child


class Unit:
    def __init__(self, id, commonName=None, nCopies=None, brz=None, HiPo1=None, HiPo2=None, slots=None, save=True, processUnit=True):
        self.id = str(id)
        self.commonName = commonName
        self.nCopies = nCopies
        self.brz = brz
        self.HiPo1 = HiPo1
        self.HiPo2 = HiPo2
        self.save = save
        self.inputHelper = InputHelper(self.id, commonName)
        self.slots = slots
        if processUnit:
            self.getConstants()
            self.getHiPo()
            self.getSBR()
            self.getStates()
            self.interpStates()
            self.saveUnit()

    def getConstants(self):
        self.inputHelper.parent = self.inputHelper.getChildElement(self.inputHelper.tree.getroot(), "constants")
        self.exclusivity = self.inputHelper.getAndSaveUserInput(
            "What is the unit's exclusivity?", type=clc.Choice(EXCLUSIVITIES, case_sensitive=False), default="DF"
        )
        self.rarity = exclusivity2Rarity[self.exclusivity]
        self.name = self.inputHelper.getAndSaveUserInput("What is the unit's name?", default="Super Saiyan Goku")
        self._class = self.inputHelper.getAndSaveUserInput(
            "What is the unit's class?", type=clc.Choice(CLASSES, case_sensitive=False), default="S"
        )
        self._type = self.inputHelper.getAndSaveUserInput(
            "What is the unit's type?", type=clc.Choice(TYPES, case_sensitive=False), default="AGL"
        )
        self.EZA = yesNo2Bool[
            self.inputHelper.getAndSaveUserInput(
                "Has the unit EZA'd?", type=clc.Choice(yesNo2Bool.keys(), case_sensitive=False), default="N"
            )
        ]
        self.date = dt.datetime.strptime(
            self.inputHelper.getAndSaveUserInput(
                "When did the unit release on the Japanse version of Dokkan? (MM/YY)", default="01/26"
            ),
            "%m/%y",
        )
        self.HP = self.inputHelper.getAndSaveUserInput("What is the unit's Max Level HP stat?", default=0)
        self.ATK = self.inputHelper.getAndSaveUserInput("What is the unit's Max Level ATK stat?", default=0)
        self.DEF = self.inputHelper.getAndSaveUserInput("What is the unit's Max Level DEF stat?", default=0)
        self.leaderSkill = leaderSkillConversion[
            self.inputHelper.getAndSaveUserInput(
                "How would you rate the unit's leader skill on a scale of 1-10?",
                type=clc.Choice(leaderSkillConversion.keys(), case_sensitive=False),
                default="<200%",
            )
        ]
        self.teams = self.inputHelper.getAndSaveUserInput(
            "How many categories is the unit on? If the unit's viability is limited to certain categories, take this into account.",
            default=1,
        )
        self.kiMod12 = float(
            self.inputHelper.getAndSaveUserInput(
                "What is the unit's 12 ki attck modifer?",
                type=clc.Choice(KI_MODIFIERS_12),
                default="1.5",
            )
        )
        self.giantRageDuration = self.inputHelper.getAndSaveUserInput(
            "How many turns does the unit's giant/rage mode last for?",
            default=0.0,
        )
        self.giantRageActivationForm = -1
        if self.giantRageDuration != 0:
            self.giantRageActivationForm = self.inputHelper.getAndSaveUserInput(
                "What # form can turn giant/rage mode?",
                default=1,
            )

    def getHiPo(self):
        if self.exclusivity == "DF_Old":
            HiPoStats = oldHiddenPotentalStatsConverter[self._type][:, self.nCopies - 1]
        elif self.exclusivity == "F2P":
            HiPoStats = f2pHiddenPotentalStatsConverter[self._type][:, self.nCopies - 1]
        else:
            HiPoStats = hiddenPotentalStatsConverter[self._type][:, self.nCopies - 1]
        if self.id in HIPO_SPECIAL_EQUIPS.keys():
            HiPoBrz = HIPO_SPECIAL_EQUIPS[self.id]["BRZ"]
            HiPoSlv = HIPO_SPECIAL_EQUIPS[self.id]["SLV"]
            HiPoGld = HIPO_SPECIAL_EQUIPS[self.id]["GLD"]
        else:
            if self.brz in ATK_DEF:
                HiPoBrz = HIPO_BRZ[self.brz]
            else:
                HiPoBrz = HIPO_BRZ[(self.HiPo1, self.HiPo2)]
            HiPoSlv = HIPO_SLV[self.HiPo1]
            HiPoGld = HIPO_GLD[(self.HiPo1, self.HiPo2)]
        HiPoAbilities = np.array(HIPO_D0[self._type]) + np.array(HiPoBrz) + np.array(HiPoSlv)
        if self.nCopies > 1:
            HiPoAbilities += HIPO_D1[(self.HiPo1, self.HiPo2)]
        if self.nCopies > 2:
            HiPoAbilities += np.array(HIPO_D2[(self.HiPo1, self.HiPo2)]) + np.array(HiPoGld)
        self.HP += HiPoStats[0]
        self.ATK += HiPoStats[1] + HiPoAbilities[0]
        self.DEF += HiPoStats[2] + HiPoAbilities[1]
        self.pHiPo = {}
        self.pHiPo["AA"] = HiPoAbilities[2]
        self.pHiPo["Crit"] = HiPoAbilities[3]
        self.pHiPo["Evasion"] = HiPoAbilities[4]
        self.TAB = HIPO_TYPE_ATK_BOOST[self.nCopies - 1]
        self.TDB = HIPO_TYPE_DEF_BOOST[self.nCopies - 1]

    def getSBR(self):
        self.inputHelper.parent = self.inputHelper.getChildElement(self.inputHelper.tree.getroot(), "SBR")
        self.SBR = 0
        if yesNo2Bool[
            self.inputHelper.getAndSaveUserInput(
                "Does the unit have any SBR abilities?",
                type=clc.Choice(yesNo2Bool.keys(), case_sensitive=False),
                default="N",
            )
        ]:
            attackAll = attackAllConversion[
                self.inputHelper.getAndSaveUserInput(
                    "Does the unit attack all enemies on super?",
                    type=clc.Choice(yesNo2Bool.keys(), case_sensitive=False),
                    default="N",
                )
            ]

            seal = sealTurnConversion[
                self.inputHelper.getAndSaveUserInput(
                    "How many turns does the unit seal for?",
                    type=None,
                    default=0,
                )
            ]
            if seal != 0:
                seal *= self.inputHelper.getAndSaveUserInput(
                    "What is the unit's chance to seal?", default=0.0
                )  # Scale by number of enemies for all enemy seal, same for stun

            stun = stunTurnConversion[
                self.inputHelper.getAndSaveUserInput("How many turns does the unit stun for?", type=None, default=0)
            ]
            if stun != 0:
                stun *= self.inputHelper.getAndSaveUserInput("What is the unit's chance to stun?", default=0.0)

            attDebuffOnAtk = attDebuffTurnConversion[
                self.inputHelper.getAndSaveUserInput(
                    "How many turns does the unit lower the enemy attack by attacking?",
                    type=None,
                    default=0,
                )
            ]
            if attDebuffOnAtk != 0:
                attDebuffOnAtk *= attDebuffOnAttackConversion[
                    self.inputHelper.getAndSaveUserInput(
                        "How much is attack lowered by on attack?",
                        type=clc.Choice(attDebuffOnAttackConversion.keys(), case_sensitive=False),
                        default="Lowers",
                    )
                ]

            attDebuffPassive = attDebuffTurnConversion[
                self.inputHelper.getAndSaveUserInput(
                    "How many turns does the unit lower the enemy attack passively?",
                    type=None,
                    default=0,
                )
            ]
            if attDebuffPassive != 0:
                attDebuffPassive *= self.inputHelper.getAndSaveUserInput(
                    "How much is attack lowered passively?", default=0.3
                )

            multipleEnemyBuff = multipleEnemyBuffConversion[
                self.inputHelper.getAndSaveUserInput(
                    "How much of a buff does the unit get when facing multiple enemies?",
                    type=clc.Choice(multipleEnemyBuffConversion.keys(), case_sensitive=False),
                    default="NA",
                )
            ]
            sbrActiveSkillBuff = 0
            if yesNo2Bool[
                self.inputHelper.getAndSaveUserInput(
                    "Does the unit have an active skill that has SBR effects?",
                    type=clc.Choice(yesNo2Bool.keys(), case_sensitive=False),
                    default="N",
                )
            ]:
                sbrActiveSkillTurn = self.inputHelper.getAndSaveUserInput("What turn can it be activated?", default=1)
                sbrActiveSkillBuff += SBR_DF ** (sbrActiveSkillTurn - 1)

            self.SBR = (
                attackAllDebuffConversion[attackAll] * (seal + stun + attDebuffOnAtk)
                + attDebuffPassive
                + multipleEnemyBuff
                + attackAll
                + sbrActiveSkillBuff
            )
        return self.SBR

    def getStates(self):
        self.forms = []
        self.states = []
        self.stacks = dict(zip(STACK_EFFECTS, [[], [], [], []]))  # Dict mapping STACK_EFFECTS to list of Stack objects
        self.inputHelper.parent = self.inputHelper.getChildElement(self.inputHelper.tree.getroot(), "forms")
        self.formsElement = self.inputHelper.parent
        self.numForms = self.inputHelper.getAndSaveUserInput("How many forms does the unit have?", default=1)
        turn = 1
        formIdx = 0
        stateIdx = -1
        self.transformationTriggered = False
        self.fightPeak = False
        # Only non-zero in between activating the stanby finish skill attack and applying to subsequent state
        # Merge requests diffs appear super attack defense related and giant form / active skill related
        self.transformationAttackDPTNoLookAhead = 0
        self.transformationAttackDPTLookAhead = 0
        self.nextForm = 1
        applyTransformationAttackDPT = False
        self.critMultiplier = CRIT_MULTIPLIER + self.TAB * CRIT_TAB_INC
        while turn <= MAX_TURN:
            stateIdx += 1
            slot = self.slots[stateIdx]
            formIdx += self.nextForm
            if self.nextForm == 1:
                # Ignore case where turn == 1 as this is when nextForm == True doesn't mean transformation
                if turn != 1:
                    form.transformed = True
                self.inputHelper.parent = self.inputHelper.getChildElement(self.formsElement, f"form_{formIdx}")
                form = Form(self, turn, formIdx)
                self.forms.append(form)
            elif self.nextForm == -1:
                form = self.forms[-2]
            self.nextForm = 0
            form.turn = turn
            nextTurn = turn + RETURN_PERIOD_PER_SLOT[slot - 1]
            form.nextTurnRelative = nextTurn - form.initialTurn + 1
            if abs(PEAK_TURN - turn) <= abs(nextTurn - PEAK_TURN) and not (self.fightPeak):
                self.fightPeak = True
            state = State(form, slot, turn)
            state.setState()
            # If have finished a standby
            if self.transformationTriggered:
                # If the trigger condition for the finish is a revive, apply DPT this turn, otherwise next.
                try:
                    hasFinishCounter = (
                        form.abilities["Attack Enemy"][-1].finishSkillChargeCondition == "Revive"
                        or form.abilities["Attack Enemy"][-1].finishSkillChargeCondition == "SA Counter"
                    )
                except:
                    hasFinishCounter = False
                if hasFinishCounter:
                    applyTransformationAttackDPT = True
                    self.nextForm = -1
                if applyTransformationAttackDPT:
                    state.attributes["DPT No Look Ahead"] += self.transformationAttackDPTNoLookAhead
                    state.attributes["DPT Look Ahead"] += self.transformationAttackDPTLookAhead
                    turn = nextTurn
                    self.transformationAttackDPTNoLookAhead = 0
                    self.transformationAttackDPTLookAhead = 0
                    state.attacksPerformed += 1
                    state.superAttacksPerformed += 1
                    self.states.append(state)
                else:  # Set this to True so apply DPT in next state (e.g. Buu Bois)
                    applyTransformationAttackDPT = True
                    stateIdx -= 1
            else:
                # state.numAttacksEvaded = branchAttacksEvaded(0, -1, state.numAttacksDirectedBeforeAttacking, state.numAttacksDirectedAfterAttacking, state.multiChanceBuff["EvasionA"], state.multiChanceBuff["EvasionB"].chances["Start of Turn"] - state.multiChanceBuff["EvasionA"].chances["Start of Turn"], state.buff["Disable Evasion Cancel"], state.defBuffStatuses[("Evasion", "Receive")], state.defBuffStatuses[("Evasion", "Evade")])
                # state.numAttacksReceived = state.numAttacksDirected - state.numAttacksEvaded
                form.numAttacksGuarded += state.guard * state.numAttacksReceived
                form.numAttacksEvaded += state.numAttacksEvaded
                form.numAttacksReceived += state.numAttacksReceived
                form.numSuperAttacksReceived += state.numSuperAttacksReceived
                self.nextForm = form.checkCondition(
                    form.formChangeCondition,
                    form.transformed,
                    form.newForm,
                )
                self.states.append(state)
                turn = nextTurn

    def getAttributes(self):
        attributeValues = [None] * len(self.states)
        attributeNames = list(self.states[0].attributes.keys())
        for i, state in enumerate(self.states):
            attributeValues[i] = list(state.attributes.values())
        return attributeNames, np.array(attributeValues)

    def setAttributes(self, attributes):
        for i in range(len(attributes[:, 0])):
            if i == len(self.states):
                state = copy.deepcopy(self.states[i - 1])
                self.states.append(state)
            else:
                state = self.states[i]
            for j, attributeName in enumerate(ATTTRIBUTE_NAMES):
                state.attributes[attributeName] = attributes[i, j]

    def interpStates(self):
        stateTurns = [state.turn for state in self.states]
        self.uninterpolatedStates = copy.deepcopy(self.states)
        _, self.uninterpolatedAttributes = self.getAttributes()
        interpAttrs = np.array([np.interp(EVAL_TURNS, stateTurns, self.uninterpolatedAttributes[:, i]) for i in range(NUM_ATTRIBUTES)]).T
        self.setAttributes(interpAttrs)

    def saveUnit(self):
        if self.save:
            # Output the unit's attributes to a .txt file
            outputFilePath = os.path.join(
                CWD, "DokkanKitOutputs", HIPO_DUPES[self.nCopies - 1], self.commonName + "_" + self.id + ".txt"
            )
            outputFile = open(outputFilePath, "w")
            for i, state in enumerate(self.uninterpolatedStates):
                outputFile.write(f"Form # {state.form.formIdx} / State # {i + 1} / Turn # {state.turn} \n \n")
                for j, attributeName in enumerate(ATTTRIBUTE_NAMES):
                    outputFile.write(f"{attributeName}: {round(self.uninterpolatedAttributes[i, j], 6)} \n")
                outputFile.write("\n")


class Form:
    def __init__(self, unit, initialTurn, formIdx, giantRageMode=False):
        self.unit = unit
        self.formElement = unit.inputHelper.parent
        self.initialTurn = initialTurn
        self.formIdx = formIdx
        self.giantRageMode = giantRageMode
        self.linkNames = [""] * MAX_NUM_LINKS
        self.linkCommonality = 0
        self.carryOverBuffs = dict(zip(EXTRA_BUFF_EFFECTS, [CarryOverBuff(effect) for effect in EXTRA_BUFF_EFFECTS]))
        self.linkEffects = dict(zip(LINK_EFFECT_NAMES, np.zeros(len(LINK_EFFECT_NAMES))))
        self.numAttacksReceived = 0  # Number of attacks received so far in this form.
        self.numAttacksGuarded = 0
        self.numAttacksEvaded = 0
        self.numSuperAttacksReceived = 0
        self.attacksPerformed = 0
        self.superAttacksPerformed = 0
        self.charge = 0
        self.superAttacks = {}  # Will be a dict of SuperAttack objects
        # This will be a list of Ability objects which will be iterated through each state to call applyToState.
        self.abilities = dict(zip(PHASES, [[] for i in range(len(PHASES))]))
        self.transformed = False
        self.newForm = True
        self.intentional12Ki = False
        self.revived = False
        self.canAttack = yesNo2Bool[unit.inputHelper.getAndSaveUserInput("Can this form attack?", default="Y")]
        if self.unit.rarity == "LR":
            self.intentional12Ki = yesNo2Bool[
                self.unit.inputHelper.getAndSaveUserInput("Should a 12 Ki be targetted for this form?", default="N")
            ]
        self.normalCounterMult = counterAttackConversion[
            self.unit.inputHelper.getAndSaveUserInput(
                "What is the unit's normal counter multiplier?",
                type=clc.Choice(counterAttackConversion.keys(), case_sensitive=False),
                default="NA",
            )
        ]
        self.saCounterMult = counterAttackConversion[
            self.unit.inputHelper.getAndSaveUserInput(
                "What is the unit's super attack counter multiplier?",
                type=clc.Choice(counterAttackConversion.keys(), case_sensitive=False),
                default="NA",
            )
        ]
        self.hasEXSuper = yesNo2Bool[
            self.unit.inputHelper.getAndSaveUserInput(
                "Does the unit have an EX super attack?", default="N"
            )
        ]
        self.getLinks()
        # assert len(np.unique(self.linkNames)) == MAX_NUM_LINKS , "Duplicate links"
        self.getSuperAttacks()
        ################################################ Turn Start #####################################################
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(self.formElement, "default")
        self.abilities["Start of Turn"].extend(
            abilityQuestionaire(
                self,
                "How many unconditional buffs does the form have?",
                Buff,
            )
        )
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(self.formElement, "turn_dpendent")
        self.abilities["Start of Turn"].extend(
            abilityQuestionaire(
                self,
                "How many turn dependent buffs does the form have?",
                TurnDependent,
                [
                    "What turn does the buff start from?",
                    "What turn does the buff end on (last turn active)?",
                ],
                [None, None],
                [self.initialTurn, MAX_TURN],
            )
        )
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(self.formElement, "slot_dependent")
        self.abilities["Start of Turn"].extend(
            abilityQuestionaire(
                self,
                "How many slot specific buffs does the form have?",
                SlotDependent,
                ["Which slot is required?"],
                [None],
                # e.g. [1] or [2, 3]
                [None],
            )
        )
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(self.formElement, "health_dependent")
        self.abilities["Start of Turn"].extend(
            abilityQuestionaire(
                self,
                "How many health threshold buffs does the form have?",
                HealthDependent,
                ["What is the threshold health value?", "Is it a max HP condition?"],
                [None, clc.Choice(YES_NO)],
                [0.5, "Y"],
            )
        )
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(self.formElement, "health_scale")
        self.abilities["Start of Turn"].extend(
            abilityQuestionaire(
                self,
                "How many health scale buffs does the form have?",
                HealthScale,
                ["The more HP remaining, the better?"],
                [clc.Choice(YES_NO)],
                ["Y"],
            )
        )
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(self.formElement, "per_turn")
        self.abilities["Start of Turn"].extend(
            abilityQuestionaire(
                self,
                "How many different buffs does the form get per turn?",
                PerTurn,
                ["What is the maximum buff?", "Applied at start of turn?", "What turn does the buff start from?"],
                [None, clc.Choice(YES_NO), None],
                [1.0, "N", 1],
            )
        )
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(self.formElement, "domain")
        self.abilities["Start of Turn"].extend(
            abilityQuestionaire(
                self,
                "How many Domain skills does the form have?",
                Domain,
                [
                    "What is the Domain type?",
                    "How much is the effect?",
                    "What proportion does it effect?",
                    "How many turns does it last?",
                ],
                [clc.Choice(DOMAIN_TYPES), None, None, None],
                ["Increase Damage Received", 0.3, 0.5, 5],
            )
        )
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(self.formElement, "active_skill_buffs")
        self.abilities["Start of Turn"].extend(
            abilityQuestionaire(
                self,
                "How many active skill buffs does the form have?",
                ActiveSkillBuff,
                [
                    "What type of buff does the unit get?",
                    "What is the value of the buff?",
                    "How many turns does it last?",
                    "How many times can it be activated?",
                ],
                [clc.Choice(EFFECTS, case_sensitive=False), None, None, None],
                ["ATK", 1.0, 1, 1],
            )
        )
        ############################################ Active / Finish Attacks ###############################################
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(self.formElement, "offensive_on_super")
        self.abilities["Active / Finish Attacks"].extend(
            abilityQuestionaire(
                self,
                "How many different offensive buffs does the form get when performing a super attack / attacking?",
                PerformingSuperAttackOffence,
                ["Does the buff only apply to the first attack?"],
                [clc.Choice(YES_NO)],
                ["N"],
            )
        )
        if self.unit.giantRageActivationForm == self.formIdx:
            self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(self.formElement, "giant_rage_mode")
            giantRageModeATK = self.unit.inputHelper.getAndSaveUserInput(
                "What is the giant/rage mode attack stat?", default=60000
            )
            self.abilities["Active / Finish Attacks"].append(GiantRageMode(self, [giantRageModeATK]))
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(self.formElement, "active_skill_attack")
        self.abilities["Active / Finish Attacks"].extend(
            abilityQuestionaire(
                self,
                "How many active skill attacks does the form have?",
                ActiveSkillAttack,
                [
                    "What is the attack multiplier?",
                    "What is the additional attack buff when performing the attack?",
                    "What is the additional P2 ATK buff when performing the attack?",
                    "Does this active skill trigger a transformation?",
                ],
                [clc.Choice(SPECIAL_ATTACK_MULTIPLIER_NAMES, case_sensitive=False), None, None, clc.Choice(YES_NO)],
                ["Ultimate", 0.0, 0.0, "N"],
            )
        )
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(self.formElement, "standby_finish_attack")
        self.abilities["Active / Finish Attacks"].extend(
            abilityQuestionaire(
                self,
                "How many Non-Counterattack Standby Finish Skills does the form have?",
                StandbyFinishSkill,
                [
                    "What is the type of the Finish Effect condition?",
                    "What is the attack multiplier?",
                    "What is the attack buff when finish is activated?",
                    "What is the buff per charge?",
                ],
                [
                    clc.Choice(FINISH_EFFECT_CONDITIONS, case_sensitive=False),
                    clc.Choice(SPECIAL_ATTACK_MULTIPLIER_NAMES, case_sensitive=False),
                    None,
                    None,
                ],
                ["Ki sphere obtained by allies", "Super-Ultimate", 1.0, 0.1],
            )
        )
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(self.formElement, "defensive_on_super")
        self.abilities["Active / Finish Attacks"].extend(
            abilityQuestionaire(
                self,
                "How many different defensive buffs does the form get when performing a super attack / attacking?",
                PerformingSuperAttackDefence,
            )
        )
        ############################################## Collect Ki ##################################################
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(self.formElement, "ki_sphere_dependent")
        self.abilities["Collect Ki"].extend(
            abilityQuestionaire(
                self,
                "How many ki sphere dependent buffs does the form have?",
                KiSphereDependent,
                [
                    "What type of ki spheres are required?",
                    "What is the required amount?",
                    "Is buff applied when attacking?",
                    "Does the buff only apply within that turn?",
                    "What is the maximum buff?",
                ],
                [clc.Choice(ORB_REQUIREMENTS), None, clc.Choice(YES_NO), clc.Choice(YES_NO), None],
                ["Any", 0, "N", "Y", 99.0],
            )
        )
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(self.formElement, "ki_dependent")
        self.abilities["Collect Ki"].extend(
            abilityQuestionaire(
                self,
                "How many ki dependent buffs does the form have?",
                KiDependent,
                ["What is the required ki?"],
                [None],
                [24],
            )
        )
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(self.formElement, "per_ki")
        self.abilities["Collect Ki"].extend(
            abilityQuestionaire(
                self,
                "How many per ki buffs does the form have?",
                PerKi,
                ["What is the maximum buff?"],
                [None],
                [1.0],
            )
        )
        ############################################## Receive Attacks ##################################################
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(self.formElement, "first_targeted_attack")
        self.abilities["Receive Attacks"].extend(
            abilityQuestionaire(
                self,
                "How many different buffs does the form get for the first targeted attack?",
                ForFirstTargtedAttack,
            )
        )
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(self.formElement, "after_receive_attack")
        self.abilities["Receive Attacks"].extend(
            abilityQuestionaire(
                self,
                "How many different buffs does the form get after receiving an attack?",
                AfterAttackReceived,
                [
                    "How many turns does the buff last?",
                    "How many attacks received are required?",
                    "Does the buff start from the next attacking turn?",
                    "What slots are required?",
                    "Requires super attack?",
                ],
                [None, None, clc.Choice(YES_NO), None, clc.Choice(YES_NO)],
                [1, 0, "N", "[1, 2, 3]", "N"],
            )
        )
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(self.formElement, "after_guard_attack")
        self.abilities["Receive Attacks"].extend(
            abilityQuestionaire(
                self,
                "How many different buffs does the form get after guarding an attack?",
                AfterGuardActivated,
                ["How many turns does the buff last?", "How many attacks guarded are required?"],
                [None, None],
                [1, 0],
            )
        )
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(self.formElement, "after_evade_attack")
        self.abilities["Receive Attacks"].extend(
            abilityQuestionaire(
                self,
                "How many different buffs does the form get after evading an attack?",
                AfterAttackEvaded,
                [
                    "How many turns does the buff last?",
                    "How many evasions are required?",
                    "Does the buff start from the next attacking turn?",
                ],
                [None, None, clc.Choice(YES_NO)],
                [1, 0, "N"],
            )
        )
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(
            self.formElement, "after_recieve_or_evade_attack"
        )
        self.abilities["Receive Attacks"].extend(
            abilityQuestionaire(
                self,
                "How many different buffs does the form get after receiving or evading an attack?",
                AfterAttackReceivedOrEvaded,
                ["How many turns does the buff last?"],
                [None],
                [1],
            )
        )
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(self.formElement, "until_recieve_attack")
        self.abilities["Receive Attacks"].extend(
            abilityQuestionaire(
                self,
                "How many different buffs does the form get until recieving an attack?",
                UntilAttackRecieved,
            )
        )
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(self.formElement, "per_attack_received")
        self.abilities["Receive Attacks"].extend(
            abilityQuestionaire(
                self,
                "How many different buffs does the form get on attacks received?",
                PerAttackReceived,
                ["What is the maximum buff?", "Within the same turn?", "Requires super attack?"],
                [None, clc.Choice(YES_NO), clc.Choice(YES_NO)],
                [1.0, "N", "N"],
            )
        )
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(
            self.formElement, "per_attack_received_or_evaded"
        )
        self.abilities["Receive Attacks"].extend(
            abilityQuestionaire(
                self,
                "How many different buffs does the form get on attacks received or evaded?",
                PerAttackReceivedOrEvaded,
                ["What is the maximum buff?", "Within the same turn?", "What slots are required?", "Requires super attack?"],
                [None, clc.Choice(YES_NO), None, clc.Choice(YES_NO)],
                [1.0, "N", "[1, 2, 3]", "N"],
            )
        )
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(self.formElement, "per_attack_guarded")
        self.abilities["Receive Attacks"].extend(
            abilityQuestionaire(
                self,
                "How many different buffs does the form get on attacks guarded?",
                PerAttackGuarded,
                ["What is the maximum buff?"],
                [None],
                [1.0],
            )
        )
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(self.formElement, "per_attack_evaded")
        self.abilities["Receive Attacks"].extend(
            abilityQuestionaire(
                self,
                "How many different buffs does the form get on attacks evaded?",
                PerAttackEvaded,
                ["What is the maximum buff?", "Within the same turn?"],
                [None, clc.Choice(YES_NO)],
                [1.0, "N"],
            )
        )
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(
            self.formElement, "after_x_attacks_received_in_battle"
        )
        self.abilities["Receive Attacks"].extend(
            abilityQuestionaire(
                self,
                "How many different buffs does the form get after receiving X attacks in battle?",
                EveryTimeXAttacksReceivedInBattle,
                ["How many attacks received are required?", "What is the maximum buff?", "Within the same turn?", "Does the buff start from the next attacking turn?",],
                [None, None, clc.Choice(YES_NO), clc.Choice(YES_NO)],
                [5, 1.0, "Y", "N"],
            )
        )
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(
            self.formElement, "after_x_attacks_evaded_in_battle"
        )
        self.abilities["Receive Attacks"].extend(
            abilityQuestionaire(
                self,
                "How many different buffs does the form get after evading X attacks in battle?",
                EveryTimeXAttacksEvadedInBattle,
                ["How many attacks evaded are required?", "What is the maximum buff?", "Within the same turn?", "Does the buff start from the next attacking turn?",],
                [None, None, clc.Choice(YES_NO), clc.Choice(YES_NO)],
                [5, 1.0, "Y", "N"],
            )
        )
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(
            self.formElement, "after_x_attacks_received_evaded_in_battle"
        )
        self.abilities["Receive Attacks"].extend(
            abilityQuestionaire(
                self,
                "How many different buffs does the form get after receiving or evading X attacks in battle?",
                EveryTimeXAttacksReceivedOrEvadedInBattle,
                ["How many attacks are required?", "What is the maximum buff?", "Within the same turn?", "Does the buff start from the next attacking turn?",],
                [None, None, clc.Choice(YES_NO), clc.Choice(YES_NO)],
                [5, 1.0, "Y", "N"],
            )
        )
        ############################################## Attack Enemy ##################################################
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(self.formElement, "after_perform_attack")
        self.abilities["Attack Enemy"].extend(
            abilityQuestionaire(
                self,
                "How many different buffs does the form get after performing an attack?",
                AfterAttackPerformed,
                [
                    "How many turns does the buff last?",
                    "How many attacks performed are required?",
                    "Requires super attack?",
                    "What slots are required?",
                ],
                [None, None, clc.Choice(YES_NO), None],
                [1, 5, "Y", "[1, 2, 3]"],
            )
        )
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(
            self.formElement, "after_x_attacks_in_battle"
        )
        self.abilities["Attack Enemy"].extend(
            abilityQuestionaire(
                self,
                "How many different buffs does the form get after performing X attacks in battle?",
                EveryTimeXAttacksPerformedInBattle,
                [
                    "How many attacks performed are required?",
                    "What is the maximum buff?",
                    "Within the same turn?",
                    "Does the buff start from the next attacking turn?",
                    "Requires super attack?",
                ],
                [None, None, clc.Choice(YES_NO), clc.Choice(YES_NO), clc.Choice(YES_NO)],
                [5, 1.0, "Y", "N", "Y"],
            )
        )
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(
            self.formElement, "per_attack_super_performed"
        )
        self.abilities["Attack Enemy"].extend(
            abilityQuestionaire(
                self,
                "How many different buffs does the form get per attack / super performed?",
                PerAttackPerformed,
                ["What is the maximum buff?", "Requires super attack?", "Within the same turn?", "What slots are required?"],
                [None, clc.Choice(YES_NO, case_sensitive=False), clc.Choice(YES_NO, case_sensitive=False), None],
                [1.0, "N", "N", "[1, 2, 3]"],
            )
        )
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(self.formElement, "nullification")
        self.abilities["Receive Attacks"].extend(
            abilityQuestionaire(
                self,
                "How many different nullification abilities does the form have?",
                Nullification,
                ["Does this nullification have counter?", "How much health is restored if nullified?", "What is the additional P2 ATK buff when performing the counter?", "What turn does the buff start from?", "What turn does the buff end on (last turn active)?"],
                [clc.Choice(YES_NO), None, None, None, None],
                ["N", 0.0, 0.0, self.initialTurn, MAX_TURN],
            )
        )
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(self.formElement, "revive")
        self.abilities["Attack Enemy"].extend(
            abilityQuestionaire(
                self,
                "How many revive skills does the form have?",
                Revive,
                [
                    "How much HP is revived with?",
                    "Does the revive only apply to this unit?",
                ],
                [None, None],
                [0.7, "N"],
            )
        )
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(self.formElement, "revival_counter")
        self.abilities["Attack Enemy"].extend(
            abilityQuestionaire(
                self,
                "How many Revival Counterattack Finish Skills does the form have?",
                RevivalCounterFinishSkill,
                [
                    "What is the attack multiplier?",
                    "What is the attack buff when finish is activated?",
                ],
                [
                    clc.Choice(SPECIAL_ATTACK_MULTIPLIER_NAMES, case_sensitive=False),
                    None,
                ],
                ["Super-Ultimate", 1.0],
            )
        )
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(self.formElement, "sa_counter")
        self.abilities["Attack Enemy"].extend(
            abilityQuestionaire(
                self,
                "How many Super Attack Counterattack Finish Skills does the form have?",
                SACounterFinishSkill,
                [
                    "What is the attack multiplier?",
                    "What is the attack buff when finish is activated?",
                ],
                [
                    clc.Choice(SPECIAL_ATTACK_MULTIPLIER_NAMES, case_sensitive=False),
                    None,
                ],
                ["Super-Intense", 1.0],
            )
        )
        ################################################ Turn End #####################################################
        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(
            self.formElement, f"form_{self.formIdx}_change_condition"
        )
        self.formChangeCondition = getCondition(unit.inputHelper)
        if self.formIdx < self.unit.numForms:
            self.newForm = True
        else:
            self.newForm = False

    def getLinks(self):
        linksElement = self.unit.inputHelper.getChildElement(self.unit.inputHelper.parent, "links")
        for linkIndex in range(MAX_NUM_LINKS):
            self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(linksElement, f"link_{linkIndex + 1}")
            self.linkNames[linkIndex] = self.unit.inputHelper.getAndSaveUserInput(
                f"What is the form's link # {linkIndex+1}",
                type=clc.Choice(LINKS, case_sensitive=False),
                default="Fierce Battle",
            )
            linkCommonality = self.unit.inputHelper.getAndSaveUserInput(
                "If has an ideal linking partner, what is the chance this link is active?",
                default=-1,
            )
            link = Link(self.linkNames[linkIndex], linkCommonality)
            for linkEffectName in LINK_EFFECT_NAMES:
                self.linkEffects[linkEffectName] += link.effects[linkEffectName]
        self.linkEffects["Commonality"] /= MAX_NUM_LINKS
        self.unit.inputHelper.parent = self.formElement

    def getSuperAttacks(self):
        superAttacksElement = self.unit.inputHelper.getChildElement(self.unit.inputHelper.parent, "super_attack")
        for superAttackType in SUPER_ATTACK_CATEGORIES:
            if superAttackType == "EX" and not self.hasEXSuper:
                continue
            self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(
                superAttacksElement, f"{superAttackNameConversion[superAttackType]}"
            )
            if not (superAttackType == "18 Ki" and (self.unit.rarity != "LR" or self.intentional12Ki)):
                multiplier = superAttackConversion[
                    self.unit.inputHelper.getAndSaveUserInput(
                        f"What is the form's {superAttackType} super attack multiplier?",
                        type=clc.Choice(SUPER_ATTACK_MULTIPLIER_NAMES, case_sensitive=False),
                        default=DEFAULT_SUPER_ATTACK_MULTIPLIER_NAMES[superAttackType],
                    )
                ][superAttackLevelConversion[self.unit.rarity][self.unit.EZA]]
                avgSuperAttack = SuperAttack(superAttackType, multiplier)
                defaultSuperAttack = copy.deepcopy(avgSuperAttack)
                if superAttackType != "EX":
                    numSuperAttacks = self.unit.inputHelper.getAndSaveUserInput(
                        f"How many different {superAttackType} super attacks does this form have?",
                        default=1,
                    )
                else:
                    exSuperCondition = getCondition(self.unit.inputHelper)
                    avgSuperAttack = EXSuperAttack(avgSuperAttack, exSuperCondition)
                    numSuperAttacks = 1
                superFracTotal = 0
                superAttackVariationsElement = self.unit.inputHelper.getChildElement(
                    self.unit.inputHelper.parent, f"{superAttackNameConversion[superAttackType]}_variations"
                )
                for i in range(numSuperAttacks):
                    self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(
                        superAttackVariationsElement, f"{superAttackNameConversion[superAttackType]}_variation_{i + 1}"
                    )
                    if numSuperAttacks > 1:
                        superFrac = self.unit.inputHelper.getAndSaveUserInput(
                            f"What is the probability of this {superAttackType} super attack variant from occuring?",
                            default=1.0,
                        )
                    else:
                        superFrac = 1
                    numEffects = self.unit.inputHelper.getAndSaveUserInput(
                        f"How many effects does this form's {superAttackType} super attack have?",
                        default=1,
                    )
                    superAttackEffectsElement = self.unit.inputHelper.getChildElement(
                        self.unit.inputHelper.parent,
                        f"{superAttackNameConversion[superAttackType]}_variation_{i + 1}_effects",
                    )
                    for j in range(numEffects):
                        self.unit.inputHelper.parent = self.unit.inputHelper.getChildElement(
                            superAttackEffectsElement,
                            f"{superAttackNameConversion[superAttackType]}_variation_{i + 1}_effect_{j + 1}",
                        )
                        effectType = self.unit.inputHelper.getAndSaveUserInput(
                            "What type of effect does the unit get on super?",
                            type=clc.Choice(SUPER_ATTACK_EFFECTS, case_sensitive=False),
                            default="ATK",
                        )
                        activationProbability = self.unit.inputHelper.getAndSaveUserInput(
                            "What is the probability this effect activates when supering?",
                            default=1.0,
                        )
                        buff = self.unit.inputHelper.getAndSaveUserInput("What is the value of the buff?", default=0.0)
                        duration = self.unit.inputHelper.getAndSaveUserInput(
                            "How many turns does it last for?", default=99
                        )
                        avgSuperAttack.effects[effectType].append(SuperAttackEffect(buff, duration, activationProbability, superFrac))
                        if i == 0:
                            defaultSuperAttack.effects[effectType].append(SuperAttackEffect(buff, duration, activationProbability, 1))
                    superFracTotal += superFrac
                    self.unit.inputHelper.parent = superAttackVariationsElement
                assert superFracTotal == 1, "Invald super attack variant probabilities entered"
                self.unit.inputHelper.parent = superAttacksElement
            self.superAttacks[superAttackType] = avgSuperAttack
            if superAttackType == "12 Ki":
                self.superAttacks["AS"] = defaultSuperAttack
        self.unit.inputHelper.parent = self.formElement

    def checkCondition(self, condition, activated, newForm):
        if activated or condition == -1:
            nextForm = 0
        elif condition == 0:
            nextForm = 1
        else:
            result = condition.isSatisfied(self)
            if result:
                if newForm:
                    nextForm = 1
                else:
                    nextForm = -1
            else:
                nextForm = 0
        return nextForm

    # Get charge per turn for a standby finish skill
    def getCharge(self, chargeCondition):
        charge = 0
        match chargeCondition:
            case "x2 same / rainbow or x1 other":
                # Currently assumes have type orb changing
                charge = (
                    (
                        orbChangeConversion["Orb Change"]["Same"]
                        + orbChangeConversion["Orb Change"]["Rainbow"]
                        + (NUM_SLOTS - 1)
                        * (
                            orbChangeConversion["No Orb Change"]["Same"]
                            + orbChangeConversion["No Orb Change"]["Rainbow"]
                        )
                    )
                    * 2
                    + self.numOtherTypeOrbs
                    + (NUM_SLOTS - 1) * orbChangeConversion["No Orb Change"]["Other"]
                )
            case "Ki sphere obtained by allies":
                # Currently assumes have rainbow orb changing
                charge = NUM_SLOTS * (
                    orbChangeConversion["Rainbow Orb Change"]["Same"]
                    + orbChangeConversion["Rainbow Orb Change"]["Rainbow"]
                    + orbChangeConversion["Rainbow Orb Change"]["Other"]
                )
            case "Attack performed by allies":
                charge = (
                    NUM_SLOTS
                    - PROBABILITY_KILL_ENEMY_BEFORE_ATTACKING[1]
                    - PROBABILITY_KILL_ENEMY_BEFORE_ATTACKING[2]
                    + (NUM_ATTACKS_PERFORMED_PER_UNIT_PER_TURN - 1)
                    * (
                        NUM_SLOTS
                        - PROBABILITY_KILL_ENEMY_BEFORE_ATTACKING[1]
                        - PROBABILITY_KILL_ENEMY_BEFORE_ATTACKING[2]
                        - (NUM_SLOTS - 1) * PROBABILITY_KILL_ENEMY_PER_ATTACK
                    )
                )
            case "Revive":
                charge = int(
                    next(ability for ability in self.abilities["Attack Enemy"] if isinstance(ability, Revive)).activated
                    == True
                )
            case "SA Counter":
                charge = len([ability for ability in self.abilities["Start of Turn"] if ability.effect == "Scouter"])
            case "Turn":
                charge = 1
            case "Broly SS Trio":
                charge = NUM_SLOTS * (
                    3 * np.mean(NUM_ATTACKS_DIRECTED)
                    + 2 * ORB_COUNTS_NO_ORB_CHANGING[1]
                    + ORB_COUNTS_COMPLETE_ORB_CHANGING[0]
                    + ORB_COUNTS_COMPLETE_ORB_CHANGING[2]
                )
            case "Dragon Balls":
                charge = (
                    NUM_SLOTS
                    * (1 + 4 * (7 / 23) / 2)
                    * (
                        orbChangeConversion["No Orb Change"]["Same"]
                        + orbChangeConversion["Rainbow Orb Change"]["Rainbow"]
                        + orbChangeConversion["Rainbow Orb Change"]["Other"]
                    )
                )
            case _:
                raise Exception(f"{chargeCondition} Charge Condition not implemented!")
        return charge


class CarryOverBuff:
    def __init__(self, effect):
        self.effect = effect
        if effect in ADDITIONAL_ATTACK_PARAMETERS:
            self.value = []
        else:
            self.value = 0

    def get(self):
        if self.effect in ADDITIONAL_ATTACK_PARAMETERS:
            return copy.copy(self.value)
        else:
            return self.value

    def add(self, value):
        if self.effect in ADDITIONAL_ATTACK_PARAMETERS:
            self.value.append(value)
        else:
            self.value += value

    def sub(self, value):
        if self.effect in ADDITIONAL_ATTACK_PARAMETERS:
            self.value.remove(value)
        else:
            self.value -= value


class Link:
    def __init__(self, name, commonality):
        self.name = name
        i = LINK_NAMES.index(self.name) + 1
        self.effects = {}
        if commonality == -1:
            self.effects[LINK_EFFECT_NAMES[-1]] = float(LINK_DATA[i, 9])
        else:
            self.effects[LINK_EFFECT_NAMES[-1]] = float(commonality)
        for j in range(len(LINK_EFFECT_NAMES) - 1):
            self.effects[LINK_EFFECT_NAMES[j]] = float(LINK_DATA[i, j + 1]) * self.effects[LINK_EFFECT_NAMES[-1]]


class SuperAttack:
    def __init__(self, superAttackType, multiplier):
        self.superAttackType = superAttackType
        self.multiplier = multiplier
        self.effects = dict(
            zip(SUPER_ATTACK_EFFECTS, [[] for i in range(len(SUPER_ATTACK_EFFECTS))])
        )
    
    def getTotalBuff(self, effectName):
        return sum([effect.buff for effect in self.effects[effectName]])
    
    def getMaxDuration(self, effectName):
        return max([effect.duration for effect in self.effects[effectName]], default=0)


class EXSuperAttack(SuperAttack):
    def __init__(self, superAttack, exSuperCondition):
        super().__init__(superAttack.superAttackType, superAttack.multiplier)
        self.exSuperCondition = exSuperCondition


class SuperAttackEffect:
    def __init__(self, buff, duration, activationProbability=1, superFrac=1):
        self.buff = buff * activationProbability * superFrac
        self.duration = duration * superFrac


class OrbCollect:
    def __init__(self, orbType):
        self.orbType = orbType
        self.prob = [1]
        self.num = [orbChangeConversion["No Orb Change"][orbType]]
        self.expected = copy.copy(self.num)

    def getNumOrbs(self):
        return sum(self.expected)


class OrbCollection:
    def __init__(self):
        self.orbCollects = dict(zip(ORB_TYPES, [OrbCollect(orbType) for orbType in ORB_TYPES]))
        self.kiPerOrb = dict(zip(ORB_TYPES, [1, KI_PER_SAME_TYPE_ORB, 1]))

    def getNumCategoryOrbs(self, orbCategory):
        return [
            sum([self.orbCollects[orbType].expected[i] for orbType in orbRequirement2TypeConversion[orbCategory]])
            for i in range(len(self.orbCollects["Same"].prob))
        ]

    def getCollectKi(self):
        return sum([self.kiPerOrb[orbType] * self.orbCollects[orbType].getNumOrbs() for orbType in ORB_TYPES])

    def addOrbChange(self, orbChange, prob):
        for orbType in ORB_TYPES:
            numOrbs = orbChangeConversion[orbChange][orbType]
            if prob == 1:
                self.orbCollects[orbType].prob = [1]
                self.orbCollects[orbType].num = [numOrbs]
                self.orbCollects[orbType].expected = [numOrbs]
            else:
                self.orbCollects[orbType].prob = [p * (1 - prob) for p in self.orbCollects[orbType].prob]  # Renormalise
                self.orbCollects[orbType].prob.append(prob)
                assert sum(self.orbCollects[orbType].prob) == 1
                self.orbCollects[orbType].num.append(numOrbs)
                self.orbCollects[orbType].expected = np.multiply(
                    self.orbCollects[orbType].prob, self.orbCollects[orbType].num
                )


class State:
    def __init__(self, form, slot, turn):
        self.form = form
        self.slot = slot  # Slot no.
        self.turn = turn
        # Dictionary for variables which have a 1-1 relationship with Buff EFFECTS
        self.buff = {
            "Ki": LEADER_SKILL_KI + form.carryOverBuffs["Ki"].get(),
            "AEAAT": form.carryOverBuffs["AEAAT"].get(),
            "Disable Guard": 0,
            "Heal": form.carryOverBuffs["Heal"].get(),
            "Damage Dealt Heal": 0,
            "Attacks Guaranteed to Hit": 0,
            "Disable Evasion Cancel": 0,
        }
        self.p1Buff = {}
        self.p2Buff = {}
        self.p3Buff = {}
        for effect in ATK_DEF:
            if form.giantRageMode:
                self.p1Buff[effect] = 0
            else:
                self.p1Buff[effect] = ATK_DEF_SUPPORT
            self.p2Buff[effect] = form.carryOverBuffs[effect].get()
            self.p3Buff[effect] = 0
        self.p2Buff["ATK"] += form.linkEffects["On Super ATK"]
        self.evadeFirstNormalChance = 0
        self.evadeFirstSuperChance = 0
        self.multiChanceBuff = {}
        self.numAttacksDirected = NUM_ATTACKS_DIRECTED[self.slot - 1]
        self.numNormalAttacksDirectedBeforeAttacking = NUM_NORMAL_ATTACKS_DIRECTED_BEFORE_ATTACKING[self.slot - 1]
        self.numNormalAttacksDirectedAfterAttacking = NUM_NORMAL_ATTACKS_DIRECTED_AFTER_ATTACKING[self.slot - 1]
        self.numSuperAttacksDirectedBeforeAttacking = NUM_SUPER_ATTACKS_DIRECTED_BEFORE_ATTACKING[self.slot - 1]
        self.numSuperAttacksDirectedAfterAttacking = NUM_SUPER_ATTACKS_DIRECTED_AFTER_ATTACKING[self.slot - 1]
        self.numAttacksDirectedBeforeAttacking = NUM_ATTACKS_DIRECTED_BEFORE_ATTACKING[self.slot - 1]
        self.numAttacksDirectedAfterAttacking = NUM_ATTACKS_DIRECTED_AFTER_ATTACKING[self.slot - 1]
        self.numAttacksReceivedAfterAttacking = NUM_ATTACKS_DIRECTED_AFTER_ATTACKING[self.slot - 1]
        self.numAttacksEvadedAfterAttacking = 0
        self.numSuperAttacksReceivedAfterAttacking = NUM_SUPER_ATTACKS_DIRECTED_AFTER_ATTACKING[self.slot - 1]
        for effect in MULTI_CHANCE_EFFECTS:
            self.multiChanceBuff[effect] = MultiChanceBuff(effect)
        for effect in MULTI_CHANCE_EFFECTS:
            if effect in MULTI_CHANCE_EFFECTS_NO_NULLIFY:
                inputEffect = "Evasion" if "Evasion" in effect else effect
                self.multiChanceBuff[effect].updateChance("HiPo", form.unit.pHiPo[inputEffect], effect, self)
                self.multiChanceBuff[effect].updateChance("Links", form.linkEffects[inputEffect], effect, self)
                if inputEffect == "Evasion":
                    self.multiChanceBuff[effect].updateChance(
                        "Start of Turn", form.carryOverBuffs[inputEffect].get(), effect, self
                    )
                else:
                    self.multiChanceBuff[effect].updateChance(
                        "On Super", form.carryOverBuffs[inputEffect].get(), effect, self
                    )
        self.aaPSuper = form.carryOverBuffs["aaPSuper"].get()
        self.aaPGuarantee = form.carryOverBuffs["aaPGuarantee"].get()
        self.orbCollection = OrbCollection()
        self.firstAttackBuff = 0
        self.firstAttackCritBuff = 0
        self.p2DefA = 0
        self.p2DefB = 0
        self.p2DefNormal = 0
        self.p2DefSuper = 0
        self.evadeSuper = 0
        self.preAttackCounterAtk = 0
        self.postAttackCounterAtk = 0
        self.p2ATKBuffPostAtttack = 0
        self.support = form.carryOverBuffs["ATK Support"].get()  # Support score
        self.dmgRedNormalA = form.carryOverBuffs["Dmg Red"].get()
        self.dmgRedNormalB = form.carryOverBuffs["Dmg Red"].get()
        self.dmgRedSuperA = form.carryOverBuffs["Dmg Red"].get()
        self.dmgRedSuperB = form.carryOverBuffs["Dmg Red"].get()
        self.guard = form.carryOverBuffs["Guard"].get()
        self.attacksPerformed = 0
        self.superAttacksPerformed = 0
        # Required for getting damage received for individual attacks
        self.defBuffStatuses = copy.deepcopy(defBuffStatusesBlank)
        # Required for getting DPTs for individual attacks
        self.atkPerAttackPerformed = np.zeros(MAX_TURN)
        self.atkPerSuperPerformed = np.zeros(MAX_TURN)
        self.critPerAttackPerformed = np.zeros(MAX_TURN)
        self.critPerSuperPerformed = np.zeros(MAX_TURN)
        self.DPTNoLookAhead = 0
        self.DPTLookAhead = 0
        self.activeSkillAttackActivated = False
        self.stackedStats = dict(zip(STACK_EFFECTS, np.zeros(len(STACK_EFFECTS))))
        self.randomKi = self.getRandomKi()
        self.canAttack = form.canAttack
        self.p2AtkBuffOnCounter = 0

    def setState(self):
        self.updateStackedStats()
        for ability in self.form.abilities["Start of Turn"]:
            ability.applyToState(self)
        self.setNoCritAtkMod()

        for ability in self.form.abilities["Active / Finish Attacks"]:
            ability.applyToState(self)

        for ability in self.form.abilities["Collect Ki"]:
            ability.applyToState(self)
        avgDefStartOfTurn = self.getDefStat(self.form.carryOverBuffs["DEF"].get())
        self.multiChanceBuff["Crit"].updateChance(
            "Super Attack Effect", self.stackedStats["Crit"], "Crit", self)
        self.multiChanceBuff["EvasionA"].updateChance(
            "Super Attack Effect", self.stackedStats["Evasion"], "EvasionA", self)
        for ability in self.form.abilities["Receive Attacks"]:
            ability.applyToState(self)
        self.setNoCritAtkMod()
        self.ki = min(round(self.buff["Ki"] + self.randomKi), rarity2MaxKi[self.form.unit.rarity])
        self.setInitialAttackDistribution()
        self.setAdditionalEXSuperChance()
        self.pAttack = 1 - PROBABILITY_KILL_ENEMY_BEFORE_ATTACKING[self.slot - 1]
        self.pNextAttack = self.pAttack - PROBABILITY_KILL_ENEMY_PER_ATTACK
        self.setAttacksPerformed()
        self.guard = min(self.guard, 1)
        self.avgDefPreSuper = self.getDefStat(self.p2Buff["DEF"])
        self.preAttackCounterAtk = self.getPreAttackCounter()

        for ability in self.form.abilities["Attack Enemy"]:
            ability.applyToState(self)
        self.addStacks()
        # Compute support bonuses from super attack effects
        for superAttackType in self.form.superAttacks.keys():
            match superAttackType:
                case "18 Ki":
                    numSupers = self.pAttack * self.pUSA
                case "12 Ki":
                    numSupers = self.pAttack * self.pSA
                case "EX":
                    numSupers = self.pAttack * (self.pEXSA + self.pAEXSA * self.aaSA * self.pNextAttack)
                case "AS":
                    numSupers = self.pAttack * (1 - self.pAEXSA) * self.aaSA * self.pNextAttack
                case _:
                    raise Exception(f"{superAttackType} Super Attack Type not implemented!")
            for superAttackEFfect in SUPPORT_SUPER_ATTACK_EFFECTS:
                for superAttackBuff in self.form.superAttacks[superAttackType].effects[superAttackEFfect]:
                    supportFactor = (
                        superAttackSupportFactorConversion[superAttackEFfect]
                        * superAttackBuff.buff
                        * (
                            superAttackBuff.duration
                            - 1
                            + (NUM_SLOTS - self.slot) / (NUM_SLOTS - 1)
                        )
                    )
                    self.support += supportFactor * numSupers
            self.multiChanceBuff["EvasionB"].updateChance(
                "Super Attack Effect", numSupers * self.form.superAttacks[superAttackType].getTotalBuff("Evasion"), "EvasionB", self)
            self.disableAction(pSuper = min(numSupers, 1) * self.form.superAttacks[superAttackType].getTotalBuff("Disable Action"))
        self.setNormal()
        self.SA = self.getSA(
            self.form.superAttacks["12 Ki"].multiplier,
            self.form.superAttacks["12 Ki"].getMaxDuration("ATK"),
            self.form.superAttacks["12 Ki"].getTotalBuff("ATK"),
        )
        self.addSA = self.getSA(
            self.form.superAttacks["AS"].multiplier,
            self.form.superAttacks["AS"].getMaxDuration("ATK"),
            self.form.superAttacks["AS"].getTotalBuff("ATK"),
        )
        self.setEXSA()
        self.setUSA()
        self.postAttackCounterAtk = self.getPostAttackCounter()
        self.DPTLookAhead += self.setDPT(lookAhead=True)
        self.DPTNoLookAhead += self.setDPT(lookAhead=False)
        self.setAvgDefMult()
        self.normalDamageTakenNoLookAhead = self.branchDamageTaken(
            1,
            0,
            -1,
            self.numNormalAttacksDirectedBeforeAttacking,
            self.numNormalAttacksDirectedAfterAttacking,
            self.p2Buff["DEF"] + self.p2DefNormal,
            self.multiChanceBuff["EvasionA"],
            0,
            self.guard,
            self.dmgRedNormalA,
            0,
            self.avgDefPreSuper,
            self.stackedStats["DEF"],
            self.defBuffStatuses,
            MAX_NORMAL_DAM_PER_TURN[self.turn - 1],
            ENEMY_NORMAL_CRIT_CHANCE,
            ENEMY_NORMAL_AVG_CRIT_DEF_DEBUFF,
            self.evadeFirstNormalChance,
        )
        self.normalDamageTakenLookAhead = self.branchDamageTaken(
            1,
            0,
            -1,
            self.numNormalAttacksDirectedBeforeAttacking,
            self.numNormalAttacksDirectedAfterAttacking,
            self.p2Buff["DEF"] + self.p2DefNormal,
            self.multiChanceBuff["EvasionA"],
            0,
            self.guard,
            self.dmgRedNormalA,
            0,
            self.avgDefPreSuper,
            self.stackedStats["DEF"],
            self.defBuffStatuses,
            MAX_NORMAL_DAM_PER_TURN_LOOK_AHEAD[self.turn - 1],
            ENEMY_NORMAL_CRIT_CHANCE,
            ENEMY_NORMAL_AVG_CRIT_DEF_DEBUFF,
            self.evadeFirstNormalChance,
        )
        self.saDamageTakenNoLookAhead = self.branchDamageTaken(
            1,
            0,
            -1,
            self.numSuperAttacksDirectedBeforeAttacking,
            self.numSuperAttacksDirectedAfterAttacking,
            self.p2Buff["DEF"] + self.p2DefSuper,
            copy.deepcopy(self.multiChanceBuff["EvasionA"]),
            self.evadeSuper,
            self.guard,
            self.dmgRedSuperA,
            self.multiChanceBuff["Nullify"].prob,
            self.avgDefPreSuper,
            self.stackedStats["DEF"],
            self.defBuffStatuses,
            MAX_SA_DAM_PER_TURN[self.turn - 1],
            ENEMY_SUPER_CRIT_CHANCE,
            ENEMY_SUPER_AVG_CRIT_DEF_DEBUFF,
            self.evadeFirstSuperChance,
        )
        self.saDamageTakenLookAhead = self.branchDamageTaken(
            1,
            0,
            -1,
            self.numSuperAttacksDirectedBeforeAttacking,
            self.numSuperAttacksDirectedAfterAttacking,
            self.p2Buff["DEF"] + self.p2DefSuper,
            copy.deepcopy(self.multiChanceBuff["EvasionA"]),
            self.evadeSuper,
            self.guard,
            self.dmgRedSuperA,
            self.multiChanceBuff["Nullify"].prob,
            self.avgDefPreSuper,
            self.stackedStats["DEF"],
            self.defBuffStatuses,
            MAX_SA_DAM_PER_TURN_LOOK_AHEAD[self.turn - 1],
            ENEMY_SUPER_CRIT_CHANCE,
            ENEMY_SUPER_AVG_CRIT_DEF_DEBUFF,
            self.evadeFirstSuperChance,
        )
        self.buff["Heal"] += (
            self.form.linkEffects["Heal"]
            + self.form.superAttacks["18 Ki"].getTotalBuff("Heal") * self.pUSA
            + self.form.superAttacks["12 Ki"].getTotalBuff("Heal") * self.pSA
            + self.form.superAttacks["AS"].getTotalBuff("Heal") * self.aaSA
            + (
                (0.03 + 0.0015 * HIPO_RECOVERY_BOOST[self.form.unit.nCopies - 1])
                * avgDefStartOfTurn
                * self.orbCollection.orbCollects["Same"].getNumOrbs()
                + self.buff["Damage Dealt Heal"] * self.DPTLookAhead
            )
            / AVG_HEALTH
        )
        self.buff["Heal"] = min(self.buff["Heal"], 1)
        self.slotFactor = self.slot**SLOT_FACTOR_POWER
        self.useability = (
            self.form.unit.teams
            / NUM_CATEGORIES_PER_UNIT_MAX
            * (1 + USEABILITY_SUPPORT_FACTOR * self.support + self.form.linkEffects["Commonality"])
        )
        sacrifcedHP = self.form.superAttacks["18 Ki"].getTotalBuff("Sacrifice HP") * self.pUSA + self.form.superAttacks["12 Ki"].getTotalBuff("Sacrifice HP") * self.pSA + self.form.superAttacks["AS"].getTotalBuff("Sacrifice HP") * self.aaSA
        attributeValues = [
            self.form.unit.leaderSkill,
            self.form.unit.SBR,
            self.form.unit.HP,
            self.useability,  # Requires user input, should make a version that loads from file
            self.buff["Heal"],
            self.support,
            self.DPTNoLookAhead,
            self.DPTLookAhead,
            self.normalDamageTakenNoLookAhead - sacrifcedHP,
            self.normalDamageTakenLookAhead - sacrifcedHP,
            self.saDamageTakenNoLookAhead,
            self.saDamageTakenLookAhead,
            self.slotFactor,
        ]
        self.attributes = dict(zip(ATTTRIBUTE_NAMES, attributeValues))
        self.form.attacksPerformed += self.attacksPerformed
        self.form.superAttacksPerformed += self.superAttacksPerformed

    def updateStackedStats(self):
        # Removes stacks from previous states if worn out
        for stat in STACK_EFFECTS:
            # Update previous stack durations
            for stack in self.form.unit.stacks[stat]:
                stack.duration -= RETURN_PERIOD_PER_SLOT[self.form.unit.states[-1].slot - 1]
            # Remove them if expired
            self.form.unit.stacks[stat] = [stack for stack in self.form.unit.stacks[stat] if stack.duration > 0]
            # Apply stacks
            for stack in self.form.unit.stacks[stat]:
                self.stackedStats[stat] += stack.buff

    def addStacks(self):
        for stat in STACK_EFFECTS:
            if self.form.unit.rarity == "LR":
                for superAttackBuff in self.form.superAttacks["18 Ki"].effects[stat]:
                    # If stack for long enough to last to next turn
                    if superAttackBuff.duration > RETURN_PERIOD_PER_SLOT[self.slot - 1]:
                        self.form.unit.stacks[stat].append(
                            Stack(
                                stat,
                                self.pUSA * superAttackBuff.buff,
                                superAttackBuff.duration,
                            )
                        )
            for superAttackBuff in self.form.superAttacks["12 Ki"].effects[stat]:
                if superAttackBuff.duration > RETURN_PERIOD_PER_SLOT[self.slot - 1]:
                    self.form.unit.stacks[stat].append(
                        Stack(
                            stat,
                            self.pSA * superAttackBuff.buff,
                            superAttackBuff.duration,
                        )
                    )
            if self.form.hasEXSuper:
                for superAttackBuff in self.form.superAttacks["EX"].effects[stat]:
                    if superAttackBuff.duration > RETURN_PERIOD_PER_SLOT[self.slot - 1]:
                        self.form.unit.stacks[stat].append(
                            Stack(
                                stat,
                                (self.pEXSA + self.pAEXSA * self.aaSA) * superAttackBuff.buff,
                                superAttackBuff.duration,
                            )
                        )
            for superAttackBuff in self.form.superAttacks["AS"].effects[stat]:
                if superAttackBuff.duration > RETURN_PERIOD_PER_SLOT[self.slot - 1]:
                    self.form.unit.stacks[stat].append(
                        Stack(
                            stat,
                            (1 - self.pAEXSA) * self.aaSA * superAttackBuff.buff,
                            superAttackBuff.duration,
                        )
                    )

    def getDefStat(self, p2Def):
        return (
            self.form.unit.DEF
            * (1 + LEADER_SKILL_STATS)
            * (1 + self.p1Buff["DEF"])
            * (1 + self.form.linkEffects["DEF"])
            * (1 + p2Def)
            * (1 + self.p3Buff["DEF"])
            * (1 + self.stackedStats["DEF"])
        )

    def setAvgDefMult(self):
        exSuperDefBuff = self.form.superAttacks["EX"].getTotalBuff("DEF") if self.form.hasEXSuper else 0
        self.avgDefMult = (
            self.stackedStats["DEF"] + (self.pSA + (1 - self.pAEXSA) * self.aaSA) * self.form.superAttacks["12 Ki"].getTotalBuff("DEF") + (self.pEXSA + (self.pAEXSA * self.aaSA)) * exSuperDefBuff
        )
        if self.form.unit.rarity == "LR":  # If unit is a LR
            self.avgDefMult += self.pUSA * self.form.superAttacks["18 Ki"].getTotalBuff("DEF")

    def setNoCritAtkMod(self):
        self.buff["AEAAT"] = min(self.buff["AEAAT"], 1)
        self.noCritAtkModifier = self.buff["AEAAT"] * (AEAAT_MULTIPLIER + self.form.unit.TAB * AEAAT_TAB_INC) + (1 - self.buff["AEAAT"]) * (self.buff["Disable Guard"] * (DISABLE_GUARD_MULTIPLIER + self.form.unit.TAB * DISABLE_GUARD_TAB_INC) + (1 - self.buff["Disable Guard"]) * (AVG_TYPE_ADVANATGE + self.form.unit.TAB * DEFAULT_TAB_INC))

    def getRandomKi(self):
        return (
            (0 if self.form.giantRageMode else KI_SUPPORT)
            + self.orbCollection.getCollectKi()
            + self.form.linkEffects["Ki"]
        )

    def setInitialAttackDistribution(self):
        """Returns the probability of normals, super-attacks and ultra-super-attacks and ex-super-attacks"""
        if self.form.hasEXSuper:
            self.pEXSA = self.form.superAttacks["EX"].exSuperCondition.chanceSatisfied([self.multiChanceBuff["Crit"].prob, 0, self.buff["Ki"], self.randomKi])
        else:
            self.pEXSA = 0

        self.pN = (1 - self.pEXSA) * ZTP_CDF(max(11 - self.buff["Ki"], 0), self.randomKi)
        
        if self.form.intentional12Ki or self.form.unit.rarity != "LR":
            self.pSA = 1 - self.pN - self.pEXSA
            self.pUSA = 0
        else:
            self.pUSA = (1 - self.pEXSA) * (1 - ZTP_CDF(max(17 - self.buff["Ki"], 0), self.randomKi))
            self.pSA = 1 - self.pN - self.pUSA - self.pEXSA

    def setAdditionalEXSuperChance(self):
        """Returns the probability of additional EX Supers on additional supers"""
        if self.form.hasEXSuper:
            # Assume EX Super condition only needs 0 or 1 attacks to have been performed
            self.pAEXSA = self.form.superAttacks["EX"].exSuperCondition.chanceSatisfied([self.multiChanceBuff["Crit"].prob, 1, self.buff["Ki"], self.randomKi])
        else:
            self.pAEXSA = 0

    def setAttacksPerformed(self):
        self.aaSA = branchAS(
            -1,
            len(self.aaPSuper),
            self.form.unit.pHiPo["AA"],
            1,
            self.aaPSuper,
            self.aaPGuarantee,
            self.form.unit.pHiPo["AA"],
        )
        self.aa = branchAA(
            -1,
            len(self.aaPSuper),
            self.form.unit.pHiPo["AA"],
            1,
            self.aaPSuper,
            self.aaPGuarantee,
            self.form.unit.pHiPo["AA"],
        )
        self.attacksPerformed = self.pAttack + self.aa * self.pNextAttack
        # Assume Binomial distribution for aaSA for the expected value
        self.superAttacksPerformed = self.pAttack + self.aaSA * self.pNextAttack

    def kiModifier(self, ki):
        """Returns the ki modifier for a unit (only used for normals and Ultras)"""
        if ki <= 12:
            return 1
        else:
            return np.linspace(self.form.unit.kiMod12, 2, 13)[ki - 12]

    def getAtkStat(self, p1Atk, p2Atk, kiMultiplier, saMultiplier):
        return (
            self.form.unit.ATK
            * (1 + LEADER_SKILL_STATS)
            * (1 + p1Atk)
            * (1 + self.form.linkEffects["SoT ATK"])
            * (1 + p2Atk)
            * (1 + self.p3Buff["ATK"])
            * kiMultiplier
            * saMultiplier
        )

    def setNormal(self):
        """Sets the ATK stat of a normal"""
        kiMultiplier = self.kiModifier(self.ki)
        self.normal = self.getAtkStat(
            self.p1Buff["ATK"] + self.stackedStats["ATK"], self.p2Buff["ATK"], kiMultiplier, 1
        )

    def SAMultiplier(self, baseMultiplier, nStacks, saAtk):
        """Returns the super-attack multiplier of a form"""
        stackingPenalty = 0
        if nStacks > 1:  # If stack attack
            stackingPenalty = saAtk
        return baseMultiplier + SA_BOOST_INC * HIPO_SA_BOOST[self.form.unit.nCopies - 1] - stackingPenalty

    def getSA(self, baseMultiplier, nStacks, saAtk):
        """Returns the ATK stat of a super-attack"""
        kiMultiplier = self.form.unit.kiMod12
        saMultiplier = self.SAMultiplier(baseMultiplier, nStacks, saAtk)
        return self.getAtkStat(
            self.p1Buff["ATK"], self.p2Buff["ATK"], kiMultiplier, saMultiplier + saAtk + self.stackedStats["ATK"]
        )
    
    def setEXSA(self):
        """Returns the ATK stat of an ex-super-attack"""
        if self.form.hasEXSuper:
            if self.ki > 12 and self.form.superAttacks["EX"].exSuperCondition.chanceSatisfied([1, 1, 24, 24]) == 0: # bad check for if can ex first turn
                kiMultiplier = self.kiModifier(self.ki)
            else:
                kiMultiplier = self.form.unit.kiMod12
            atkBuff = self.form.superAttacks["EX"].getTotalBuff("ATK")
            saMultiplier = self.SAMultiplier(
                self.form.superAttacks["EX"].multiplier,
                self.form.superAttacks["EX"].getMaxDuration("ATK"),
                atkBuff,
            )
            self.EXSA = self.getAtkStat(
                self.p1Buff["ATK"],
                self.p2Buff["ATK"],
                kiMultiplier,
                saMultiplier + atkBuff + self.stackedStats["ATK"],
            )
        return 0

    def setUSA(self):
        """Returns the ATK stat of an ultra-super-attack"""
        kiMultiplier = self.kiModifier(max(self.ki, 18))
        atkBuff = self.form.superAttacks["18 Ki"].getTotalBuff("ATK")
        saMultiplier = self.SAMultiplier(
            self.form.superAttacks["18 Ki"].multiplier,
            self.form.superAttacks["18 Ki"].getMaxDuration("ATK"),
            atkBuff,
        )
        self.USA = self.getAtkStat(
            self.p1Buff["ATK"],
            self.p2Buff["ATK"],
            kiMultiplier,
            saMultiplier + atkBuff + self.stackedStats["ATK"],
        )

    def getActiveAtk(self, ki, p2Atk, saMultActive):
        """Returns the ATK stat of an active-skill attack"""
        kiMultiplier = self.kiModifier(ki)
        saMultiplier = saMultActive + SA_BOOST_INC * HIPO_SA_BOOST[self.form.unit.nCopies - 1]
        return self.getAtkStat(self.p1Buff["ATK"], p2Atk, kiMultiplier, saMultiplier * (1 + self.stackedStats["ATK"]))
    
    def atk2Dmg(self, atk, pCrit, lookAhead):
        """Returns the damage dealt by an attack"""
        enemyDefArray = MAX_ENEMY_DEF_PER_TURN_LOOK_AHEAD if lookAhead else MAX_ENEMY_DEF_PER_TURN
        dmgThresholdArray = MAX_ENEMY_DMG_THRESHOLD_PER_TURN_LOOK_AHEAD if lookAhead else MAX_ENEMY_DMG_THRESHOLD_PER_TURN
        return (1 - ENEMY_DODGE_CHANCE + ENEMY_DODGE_CHANCE * self.buff["Attacks Guaranteed to Hit"]) * (dmgThreshold(atk * self.form.unit.critMultiplier * (1 - AVG_ENEMY_DMG_RED), dmgThresholdArray[self.turn - 1]) * pCrit + dmgThreshold(max(atk * self.noCritAtkModifier - enemyDefArray[self.turn - 1], 0) * (1 - AVG_ENEMY_DMG_RED), dmgThresholdArray[self.turn - 1]) * (1 - pCrit))

    def disableAction(self, pSuper = 1):
        pDisableSuper = min(pSuper * self.numSuperAttacksDirectedAfterAttacking / self.numAttacksDirectedAfterAttacking * (1 - ENEMY_DODGE_CHANCE + ENEMY_DODGE_CHANCE * self.buff["Attacks Guaranteed to Hit"]), self.numSuperAttacksDirectedAfterAttacking)
        self.numSuperAttacksDirectedAfterAttacking -= pDisableSuper
        pDisableNormal = min(pSuper * self.numNormalAttacksDirectedAfterAttacking / self.numAttacksDirectedAfterAttacking * (1 - ENEMY_DODGE_CHANCE + ENEMY_DODGE_CHANCE * self.buff["Attacks Guaranteed to Hit"]), self.numNormalAttacksDirectedAfterAttacking)
        self.numNormalAttacksDirectedAfterAttacking -= pDisableNormal
        self.numAttacksDirected -= pDisableNormal
        self.numAttacksDirectedAfterAttacking -= pDisableNormal
    
    def atkAfterAttacksPerformed(self):
        p2Buff = 0
        attacksToPerform = self.attacksPerformed
        i = 0
        for attack in self.atkPerAttackPerformed:
            if attacksToPerform >= 1:
                p2Buff += attack
            else:
                p2Buff += attacksToPerform * attack
                break
            attacksToPerform -= 1
            i += 1

        superAttacksToPerform = self.superAttacksPerformed
        multBuff = 0
        i = 0
        for attack in self.atkPerSuperPerformed:
            if i == 0 and self.form.unit.rarity == "LR":
                p2Buff += attack
                multBuff += self.form.superAttacks["18 Ki"].getTotalBuff("ATK")
            if attacksToPerform >= 1:
                p2Buff += attack
                multBuff += self.form.superAttacks["12 Ki"].getTotalBuff("ATK")
            else:
                p2Buff += attacksToPerform * attack
                multBuff += attacksToPerform * self.form.superAttacks["12 Ki"].getTotalBuff("ATK")
                break
            superAttacksToPerform -= 1
            i += 1

        return p2Buff, multBuff           
    
    def getPreAttackCounter(self):
        kiMultiplier = self.kiModifier(self.ki)
        return self.getAtkStat(
            self.p1Buff["ATK"],
            self.p2Buff["ATK"] + self.p2AtkBuffOnCounter,
            kiMultiplier,
            1 + self.stackedStats["ATK"]
        )

    def getPostAttackCounter(self):
        kiMultiplier = self.kiModifier(self.ki)
        p2Buff, saMultBuff = self.atkAfterAttacksPerformed()
        return self.getAtkStat(
            self.p1Buff["ATK"],
            self.p2Buff["ATK"] + p2Buff + self.p2ATKBuffPostAtttack / 2 + self.p2AtkBuffOnCounter, # divide by 2 as if the extra buff for having received all the attacks
            kiMultiplier,
            1 + self.stackedStats["ATK"] + saMultBuff
        )

    def branchDPT(
        self,
        i,
        mSA,
        mN,
        pAA,
        nProcs,
        crit,
        p2AtkBuff,
        atkPerAttackPerformed,
        critPerAttackPerformed,
        atkPerSuperPerformed,
        critPerSuperPerformed,
        lookAhead,
    ):
        """Returns the total remaining DPT of a unit in a turn recursively"""
        p2AtkFactor = (1 + self.p2Buff["ATK"] + p2AtkBuff) / (1 + self.p2Buff["ATK"])
        normal = self.atk2Dmg(mN * self.n_0 * p2AtkFactor, crit.prob, lookAhead)
        additional12Ki = self.atk2Dmg(mSA["12 Ki"] * self.aSA_0["12 Ki"] * p2AtkFactor, crit.prob, lookAhead)
        if self.form.hasEXSuper:
            additionalEXSA = self.atk2Dmg(mSA["EX"] * self.aSA_0["EX"] * p2AtkFactor, crit.prob, lookAhead)
        else:
            additionalEXSA = 0.0
        if i == self.nAA - 1:  # If no more additional attacks
            return 0.5 * pAA * (self.pAEXSA * additionalEXSA + (1 - self.pAEXSA) * additional12Ki + normal)  # Add average hidden-potential attack damage
        else:
            i += 1  # Increment attack counter
            # Calculate extra attack if get additional super and subsequent addditional attacks
            # Add damage if don't get any additional attacks
            crit0 = copy.deepcopy(crit)
            crit.updateChance("On Super", critPerAttackPerformed[0], "Crit")
            crit1 = copy.deepcopy(crit)
            crit.updateChance("On Super", critPerSuperPerformed[0] - critPerAttackPerformed[0], "Crit")
            crit2 = copy.deepcopy(crit)
            crit2.updateChance("Super Attack Effect", self.form.superAttacks["AS"].getTotalBuff("Crit"), "Crit")
            
            tempDPT0 = self.branchDPT(
                i,
                mSA,
                mN,
                pAA,
                nProcs,
                crit0,
                p2AtkBuff,
                atkPerAttackPerformed,
                critPerAttackPerformed,
                atkPerSuperPerformed,
                critPerSuperPerformed,
                lookAhead,
            )
            tempDPT1 = self.branchDPT(
                i,
                mSA,
                mN,
                pAA + self.form.unit.pHiPo["AA"] * (1 - self.form.unit.pHiPo["AA"]) ** nProcs,
                nProcs + 1,
                crit1,
                p2AtkBuff + atkPerAttackPerformed[0],
                atkPerAttackPerformed[1:],
                critPerAttackPerformed[1:],
                atkPerSuperPerformed,
                critPerSuperPerformed,
                lookAhead,
            )
            mSA2 = {key: mSA[key] + self.form.superAttacks["AS"].getTotalBuff("ATK") for key in mSA.keys()}
            tempDPT2 = self.branchDPT(
                i,
                mSA2,
                mN + self.form.superAttacks["AS"].getTotalBuff("ATK"),
                pAA + self.form.unit.pHiPo["AA"] * (1 - self.form.unit.pHiPo["AA"]) ** nProcs,
                nProcs + 1,
                crit2,
                p2AtkBuff + atkPerSuperPerformed[0],
                atkPerAttackPerformed,
                critPerAttackPerformed,
                atkPerSuperPerformed[1:],
                critPerSuperPerformed[1:],
                lookAhead,
            )
            if self.form.hasEXSuper:
                crit.updateChance("Super Attack Effect", self.form.superAttacks["EX"].getTotalBuff("Crit"), "Crit")
                crit3 = copy.deepcopy(crit)
                mSA3 = {key: mSA[key] + self.form.superAttacks["EX"].getTotalBuff("ATK") for key in mSA.keys()}
                tempDPT3 = self.branchDPT(
                    i,
                    mSA3,
                    mN + self.form.superAttacks["EX"].getTotalBuff("ATK"),
                    pAA + self.form.unit.pHiPo["AA"] * (1 - self.form.unit.pHiPo["AA"]) ** nProcs,
                    nProcs + 1,
                    crit3,
                    p2AtkBuff + atkPerSuperPerformed[0],
                    atkPerAttackPerformed,
                    critPerAttackPerformed,
                    atkPerSuperPerformed[1:],
                    critPerSuperPerformed[1:],
                    lookAhead,
                )
            else:
                tempDPT3 = 0.0

            return self.aaPSuper[i] * (self.pAEXSA * (additionalEXSA + tempDPT3) + (1 - self.pAEXSA) * (tempDPT2 + additional12Ki)) + (1 - self.aaPSuper[i]) * (
                self.aaPGuarantee[i] * (tempDPT1 + normal) + (1 - self.aaPGuarantee[i]) * tempDPT0
            )

    def setDPT(self, lookAhead):
        """Returns the DPT of a unit in a turn"""
        dpt = 0
        if self.canAttack:
            # Number of additional attacks from passive in each turn
            self.nAA = len(self.aaPSuper)
            i = -1  # iteration counter
            nProcs = 1  # Initialise number of HiPo procs

            mSA = {}
            self.aSA_0 = {}
            additionalSAs = ["12 Ki", "EX"] if self.form.hasEXSuper else ["12 Ki"]
            for sa in additionalSAs:
                if sa == "12 Ki":
                    superAttack = self.form.superAttacks["AS"]
                else:
                    superAttack = self.form.superAttacks["EX"]
                saMultiplier = self.SAMultiplier(
                    self.form.superAttacks[sa].multiplier,
                    superAttack.getMaxDuration("ATK"),
                    superAttack.getTotalBuff("ATK"),
                )
                mSA[sa] = (
                    saMultiplier + superAttack.getTotalBuff("ATK") + self.stackedStats["ATK"]
                )  # multiplier after SA effect
                
            self.aSA_0["12 Ki"] = self.addSA / mSA["12 Ki"]  # Get SA attack stat without multiplier
            if self.form.hasEXSuper:
                self.aSA_0["EX"] = self.EXSA / mSA["EX"]
            else:
                self.aSA_0["EX"] = 0

            baseAtk = 1 + self.p1Buff["ATK"] + self.stackedStats["ATK"]
            self.n_0 = self.normal / baseAtk
            pAA = self.form.unit.pHiPo["AA"]  # Probability of doing an additional attack next
            crit = copy.deepcopy(self.multiChanceBuff["Crit"])
            counterDmgPreSuper = self.numAttacksDirectedBeforeAttacking * self.atk2Dmg(self.form.normalCounterMult * self.preAttackCounterAtk, crit.prob, lookAhead) + NUM_SUPER_ATTACKS_DIRECTED_BEFORE_ATTACKING[self.slot - 1] * self.multiChanceBuff["Nullify"].chances["SA Counter"] * self.atk2Dmg(self.form.saCounterMult * self.preAttackCounterAtk, crit.prob, lookAhead)
            counterDmgPostSuper = self.numAttacksDirectedAfterAttacking * self.atk2Dmg(self.form.normalCounterMult * self.postAttackCounterAtk, crit.prob, lookAhead) + NUM_SUPER_ATTACKS_DIRECTED_AFTER_ATTACKING[self.slot - 1] * self.multiChanceBuff["Nullify"].chances["SA Counter"] * self.atk2Dmg(self.form.saCounterMult * self.postAttackCounterAtk, crit.prob, lookAhead)
            crit.updateChance("On Super", self.critPerAttackPerformed[0], "Crit")
            critN = copy.deepcopy(crit)
            crit1stN = copy.deepcopy(critN)
            if self.firstAttackCritBuff > 0:
                crit1stN.updateChance("On Super", self.firstAttackCritBuff, "Crit")
            crit.updateChance("On Super", self.critPerSuperPerformed[0] - self.critPerAttackPerformed[0], "Crit")
            crit.updateChance("Super Attack Effect", self.form.superAttacks["12 Ki"].getTotalBuff("Crit"), "Crit")
            critSA = copy.deepcopy(crit)
            crit1stSA = copy.deepcopy(critSA)
            if self.firstAttackCritBuff > 0:
                crit1stSA.updateChance("On Super", self.firstAttackCritBuff, "Crit")
            if self.form.hasEXSuper:
                crit.updateChance("Super Attack Effect", self.form.superAttacks["EX"].getTotalBuff("Crit") - self.form.superAttacks["12 Ki"].getTotalBuff("Crit"), "Crit")
                critEXSA = copy.deepcopy(crit)
                crit1stEXSA = copy.deepcopy(critEXSA)
                if self.firstAttackCritBuff > 0:
                    crit1stEXSA.updateChance("On Super", self.firstAttackCritBuff, "Crit")
            crit.updateChance(
                "Super Attack Effect",
                self.form.superAttacks["18 Ki"].getTotalBuff("Crit")
                - self.form.superAttacks["12 Ki"].getTotalBuff("Crit")
                - (self.form.superAttacks["EX"].getTotalBuff("Crit") if self.form.hasEXSuper else 0),
                "Crit",
            )
            critUSA = copy.deepcopy(crit)
            crit1stUSA = copy.deepcopy(critUSA)
            if self.firstAttackCritBuff > 0:
                crit1stUSA.updateChance("On Super", self.firstAttackCritBuff, "Crit")
            if self.pN > 0:
                dpt += self.pN * (self.atk2Dmg(
                    self.normal * (1 + self.firstAttackBuff), crit1stN.prob, lookAhead)
                    + self.branchDPT(
                        i,
                        mSA,
                        baseAtk,
                        pAA,
                        nProcs,
                        critN,
                        self.atkPerAttackPerformed[0],
                        self.atkPerAttackPerformed[1:],
                        self.critPerAttackPerformed[1:],
                        self.atkPerSuperPerformed,
                        self.critPerSuperPerformed,
                        lookAhead,
                    )
                )
            if self.pSA > 0:
                atkBuff = self.form.superAttacks["12 Ki"].getTotalBuff("ATK")
                m12Ki = {key: mSA[key] + atkBuff for key in mSA}
                dpt += self.pSA * (self.atk2Dmg(
                    self.SA * (1 + self.firstAttackBuff), crit1stSA.prob, lookAhead)
                    + self.branchDPT(
                        i,
                        m12Ki,
                        baseAtk + atkBuff,
                        pAA,
                        nProcs,
                        critSA,
                        self.atkPerSuperPerformed[0],
                        self.atkPerAttackPerformed,
                        self.critPerAttackPerformed,
                        self.atkPerSuperPerformed[1:],
                        self.critPerSuperPerformed[1:],
                        lookAhead,
                    )
                )
            if self.pEXSA > 0:
                atkBuff = self.form.superAttacks["EX"].getTotalBuff("ATK")
                mEX = {key: mSA[key] + atkBuff for key in mSA}
                dpt += self.pEXSA * (self.atk2Dmg(
                    self.EXSA * (1 + self.firstAttackBuff), crit1stEXSA.prob, lookAhead)
                    + self.branchDPT(
                        i,
                        mEX,
                        baseAtk + atkBuff,
                        pAA,
                        nProcs,
                        critEXSA,
                        self.atkPerSuperPerformed[0],
                        self.atkPerAttackPerformed,
                        self.critPerAttackPerformed,
                        self.atkPerSuperPerformed[1:],
                        self.critPerSuperPerformed[1:],
                        lookAhead,
                    )
                )
            if self.form.unit.rarity == "LR":  # If  is a LR
                atkBuff = self.form.superAttacks["18 Ki"].getTotalBuff("ATK")
                mUSA = {key: mSA[key] + atkBuff for key in mSA}
                dpt += self.pUSA * (self.atk2Dmg(
                    self.USA * (1 + self.firstAttackBuff), crit1stUSA.prob, lookAhead)
                    + self.branchDPT(
                        i,
                        mUSA,
                        baseAtk + atkBuff,
                        pAA,
                        nProcs,
                        critUSA,
                        self.atkPerSuperPerformed[0],
                        self.atkPerAttackPerformed,
                        self.critPerAttackPerformed,
                        self.atkPerSuperPerformed[1:],
                        self.critPerSuperPerformed[1:],
                        lookAhead,
                    )
                )
            dpt += (counterDmgPreSuper + counterDmgPostSuper)
        dpt = max(dpt, 0.0)
        return dpt

    def branchDamageTaken(
        self,
        pBranch,
        iA,
        iB,
        nAA,
        nAB,
        p2Def,
        evasion,
        pEvadeExtra,
        pGuard,
        dmgRed,
        pNullify,
        defence,
        postSuperDefMult,
        defBuffStatuses,
        maxDamage,
        enemyCritChance,
        enemyCritDefDebuff,
        evadeAttackChance,
    ):
        if pBranch == 0:
            return 0
        """Returns the remaining damage taken by a unit in a turn recursively"""
        # Get damage taken by the attack pre super
        pEvadeB = (
            self.multiChanceBuff["EvasionB"].chances["Start of Turn"]
            - self.multiChanceBuff["EvasionA"].chances["Start of Turn"]
        )
        dmgRedB = self.dmgRedNormalB - self.dmgRedNormalA
        evasion.updateChance("Start of Turn", pEvadeExtra, "")
        evasion1stAttack = copy.deepcopy(evasion)
        evasion1stAttack.updateChance("Start of Turn", evadeAttackChance, "")
        pE_N = (1 - DODGE_CANCEL_FACTOR * (1 - self.buff["Disable Evasion Cancel"])) * evasion1stAttack.prob
        pE = pE_N * (1 - pNullify) + pNullify
        pG = (1 - pE) * pGuard
        pR = 1 - pE - pG
        attackDamageTaken = getAttackDamageTaken(
            pE, pGuard, maxDamage, self.form.unit.TDB, dmgRed, defence, enemyCritChance, enemyCritDefDebuff,
        )
        # If last attack in sequence pre super
        if iA >= nAA - 1 and iB == -1:
            evasionPostEvadeB = copy.deepcopy(evasion)
            evasionPostHitB = copy.deepcopy(evasion)
            evasionPostEvadeB.updateChance(
                "Start of Turn",
                (defBuffStatuses[("Evasion", "Evade")][0] + defBuffStatuses[("Evasion", "ReceiveOrEvade")][0])
                * (nAA - iA)
                + pEvadeB,
                "",
            )
            evasionPostHitB.updateChance(
                "Start of Turn",
                (defBuffStatuses[("Evasion", "Receive")][0] + defBuffStatuses[("Evasion", "ReceiveOrEvade")][0])
                * (nAA - iA)
                + pEvadeB,
                "",
            )
            # mulitply by extra factor if only part is expected. 0 =< nAA - iA < 1 )
            defBuffNextStatuses, defBuffStatuses0 = processDefBuffStatuses(defBuffStatuses, 1 - (nAA - iA))
            return pBranch * (
                attackDamageTaken * (nAA - iA)
                + self.branchDamageTaken(
                    pE,
                    iA,
                    0,
                    nAA,
                    nAB,
                    p2Def
                    + self.p2DefB
                    + (defBuffStatuses0[("DEF", "Evade")] + defBuffStatuses0[("DEF", "ReceiveOrEvade")]) * (nAA - iA),
                    evasionPostEvadeB,
                    0,
                    pGuard + defBuffStatuses0[("Guard", "ReceiveOrEvade")] * (nAA - iA),
                    dmgRed
                    + dmgRedB
                    + (defBuffStatuses0[("DmgRed", "Evade")] + defBuffStatuses0[("DmgRed", "ReceiveOrEvade")])
                    * (nAA - iA),
                    pNullify,
                    defence
                    * (
                        1
                        + p2Def
                        + self.p2DefB
                        + (defBuffStatuses0[("DEF", "Evade")] + defBuffStatuses0[("DEF", "ReceiveOrEvade")])
                        * (nAA - iA)
                    )
                    / (1 + p2Def)
                    * (1 + self.avgDefMult)
                    / (1 + postSuperDefMult),
                    self.avgDefMult,
                    defBuffNextStatuses["Evade"],
                    maxDamage,
                    enemyCritChance,
                    enemyCritDefDebuff,
                    0
                )
                + self.branchDamageTaken(
                    pG,
                    iA,
                    0,
                    nAA,
                    nAB,
                    p2Def
                    + self.p2DefB
                    + (
                        defBuffStatuses0[("DEF", "Guard")]
                        + defBuffStatuses0[("DEF", "Receive")]
                        + defBuffStatuses0[("DEF", "ReceiveOrEvade")]
                    )
                    * (nAA - iA),
                    evasionPostHitB,
                    0,
                    pGuard
                    + (
                        defBuffStatuses0[("Guard", "Guard")]
                        + defBuffStatuses0[("Guard", "Receive")]
                        + defBuffStatuses0[("Guard", "ReceiveOrEvade")]
                    )
                    * (nAA - iA),
                    dmgRed
                    + dmgRedB
                    + (
                        defBuffStatuses0[("DmgRed", "Receive")]
                        + defBuffStatuses0[("DmgRed", "Guard")]
                        + defBuffStatuses0[("DmgRed", "ReceiveOrEvade")]
                    )
                    * (nAA - iA),
                    pNullify,
                    defence
                    * (
                        1
                        + p2Def
                        + self.p2DefB
                        + (
                            defBuffStatuses0[("DEF", "Guard")]
                            + defBuffStatuses0[("DEF", "Receive")]
                            + defBuffStatuses0[("DEF", "ReceiveOrEvade")]
                        )
                        * (nAA - iA)
                    )
                    / (1 + p2Def)
                    * (1 + self.avgDefMult)
                    / (1 + postSuperDefMult),
                    self.avgDefMult,
                    defBuffNextStatuses["Guard"],
                    maxDamage,
                    enemyCritChance,
                    enemyCritDefDebuff,
                    0
                )
                + self.branchDamageTaken(
                    pR,
                    iA,
                    0,
                    nAA,
                    nAB,
                    p2Def
                    + self.p2DefB
                    + (defBuffStatuses0[("DEF", "Receive")] + defBuffStatuses0[("DEF", "ReceiveOrEvade")]) * (nAA - iA),
                    evasionPostHitB,
                    0,
                    pGuard
                    + (defBuffStatuses0[("Guard", "Receive")] + defBuffStatuses0[("Guard", "ReceiveOrEvade")])
                    * (nAA - iA),
                    dmgRed
                    + dmgRedB
                    + (defBuffStatuses0[("DmgRed", "Receive")] + defBuffStatuses0[("DmgRed", "ReceiveOrEvade")])
                    * (nAA - iA),
                    pNullify,
                    defence
                    * (
                        1
                        + p2Def
                        + self.p2DefB
                        + (defBuffStatuses0[("DEF", "Receive")] + defBuffStatuses0[("DEF", "ReceiveOrEvade")])
                        * (nAA - iA)
                    )
                    / (1 + p2Def)
                    * (1 + self.avgDefMult)
                    / (1 + postSuperDefMult),
                    self.avgDefMult,
                    defBuffNextStatuses["Receive"],
                    maxDamage,
                    enemyCritChance,
                    enemyCritDefDebuff,
                    0
                )
            )
        elif iA < nAA - 1 or iB < nAB - 1:
            defBuffNextStatuses, defBuffStatuses0 = processDefBuffStatuses(defBuffStatuses)
            evasionPostEvade = copy.deepcopy(evasion)
            evasionPostHit = copy.deepcopy(evasion)
            evasionPostEvade.updateChance(
                "Start of Turn",
                defBuffStatuses0[("Evasion", "Evade")] + defBuffStatuses0[("Evasion", "ReceiveOrEvade")],
                "",
            )
            evasionPostHit.updateChance(
                "Start of Turn",
                defBuffStatuses0[("Evasion", "Receive")] + defBuffStatuses0[("Evasion", "ReceiveOrEvade")],
                "",
            )
            if iA < nAA - 1:
                iA += 1
            else:
                iB += 1
            return pBranch * (
                attackDamageTaken
                + self.branchDamageTaken(
                    pE,
                    iA,
                    iB,
                    nAA,
                    nAB,
                    p2Def
                    + defBuffStatuses0[("DEF", "Evade")]
                    + defBuffStatuses0[("DEF", "ReceiveOrEvade")],
                    evasionPostEvade,
                    0,
                    pGuard + defBuffStatuses0[("Guard", "ReceiveOrEvade")],
                    dmgRed + defBuffStatuses0[("DmgRed", "Evade")] + defBuffStatuses0[("DmgRed", "ReceiveOrEvade")],
                    pNullify,
                    defence
                    * (
                        1
                        + p2Def
                        + defBuffStatuses0[("DEF", "Evade")]
                        + defBuffStatuses0[("DEF", "ReceiveOrEvade")]
                    )
                    / (1 + p2Def),
                    postSuperDefMult,
                    defBuffNextStatuses["Evade"],
                    maxDamage,
                    enemyCritChance,
                    enemyCritDefDebuff,
                    0
                )
                + self.branchDamageTaken(
                    pG,
                    iA,
                    iB,
                    nAA,
                    nAB,
                    p2Def
                    + defBuffStatuses0[("DEF", "Guard")]
                    + defBuffStatuses0[("DEF", "Receive")]
                    + defBuffStatuses0[("DEF", "ReceiveOrEvade")],
                    evasionPostHit,
                    0,
                    pGuard + defBuffStatuses0[("Guard", "Receive")] + defBuffStatuses0[("Guard", "ReceiveOrEvade")],
                    dmgRed
                    + defBuffStatuses0[("DmgRed", "Guard")]
                    + defBuffStatuses0[("DmgRed", "Receive")]
                    + defBuffStatuses0[("DmgRed", "ReceiveOrEvade")],
                    pNullify,
                    defence
                    * (
                        1
                        + p2Def
                        + defBuffStatuses0[("DEF", "Guard")]
                        + defBuffStatuses0[("DEF", "Receive")]
                        + defBuffStatuses0[("DEF", "ReceiveOrEvade")]
                    )
                    / (1 + p2Def),
                    postSuperDefMult,
                    defBuffNextStatuses["Guard"],
                    maxDamage,
                    enemyCritChance,
                    enemyCritDefDebuff,
                    0
                )
                + self.branchDamageTaken(
                    pR,
                    iA,
                    iB,
                    nAA,
                    nAB,
                    p2Def
                    + defBuffStatuses0[("DEF", "Receive")]
                    + defBuffStatuses0[("DEF", "ReceiveOrEvade")],
                    evasionPostHit,
                    0,
                    pGuard + defBuffStatuses0[("Guard", "Receive")] + defBuffStatuses0[("Guard", "ReceiveOrEvade")],
                    dmgRed + defBuffStatuses0[("DmgRed", "Receive")] + defBuffStatuses0[("DmgRed", "ReceiveOrEvade")],
                    pNullify,
                    defence
                    * (
                        1
                        + p2Def
                        + defBuffStatuses0[("DEF", "Receive")]
                        + defBuffStatuses0[("DEF", "ReceiveOrEvade")]
                    )
                    / (1 + p2Def),
                    postSuperDefMult,
                    defBuffNextStatuses["Receive"],
                    maxDamage,
                    enemyCritChance,
                    enemyCritDefDebuff,
                    0
                )
            )
        else:
            # mulitply by extra factor if only part is expected. 0 =< nAB - iB < 1 )
            return pBranch * attackDamageTaken * (nAB - iB)


class Stack:
    def __init__(self, stat, buff, duration):
        self.stat = stat
        self.buff = buff
        self.duration = duration


class Ability:
    def __init__(self, form):
        self.form = form


class SingleTurnAbility(Ability):
    def __init__(self, form):
        super().__init__(form)
        self.condition = getCondition(form.unit.inputHelper)
        self.activated = False


class GiantRageMode(SingleTurnAbility):
    def __init__(self, form, args):
        super().__init__(form)
        self.ATK = args[0]
        form.unit.inputHelper.parent = form.unit.inputHelper.parentMap[form.unit.inputHelper.parent]
        self.giantRageForm = Form(form.unit, 1, form.formIdx + 1, giantRageMode=True)

    def applyToState(self, state):
        if state.form.checkCondition(self.condition, self.activated, True) and self.form.unit.fightPeak:
            self.activated = True
            # Create a State so can get access to setState for damage calc
            self.giantRageModeState = State(self.giantRageForm, state.slot, state.turn)
            giantRageUnit = copy.deepcopy(state.form.unit)
            giantRageUnit.ATK = self.ATK
            self.giantRageModeState.form.unit = giantRageUnit
            self.giantRageModeState.setState()  # Calculate the DPT of the state
            state.DPTNoLookAhead += self.giantRageModeState.DPTNoLookAhead * NUM_SLOTS * giantRageUnit.giantRageDuration
            state.DPTLookAhead += self.giantRageModeState.DPTLookAhead * NUM_SLOTS * giantRageUnit.giantRageDuration
            state.support += GIANT_RAGE_SUPPORT
            state.buff["Heal"] += GIANT_RAGE_HEAL


class Revive(SingleTurnAbility):
    def __init__(self, form, args):
        super().__init__(form)
        self.hpRegen, self.isThisCharacterOnly = args
        form.unit.inputHelper.parent = form.unit.inputHelper.parentMap[form.unit.inputHelper.parent]
        self.abilities = abilityQuestionaire(form, "How many additional constant buffs does this revive have?", Buff)

    def applyToState(self, state):
        # Usually want to revive the turn before fight peak
        if self.form.checkCondition(self.condition, self.activated, True):
            self.activated = True
            state.buff["Heal"] = min(state.buff["Heal"] + self.hpRegen, 1)
            if self.isThisCharacterOnly:
                state.support += REVIVE_UNIT_SUPPORT_BUFF
            else:
                state.support += REVIVE_ROTATION_SUPPORT_BUFF
            self.form.abilities["Start of Turn"].extend(self.abilities)
            self.form.revived = True


class Domain(SingleTurnAbility):
    def __init__(self, form, args):
        super().__init__(form)
        self.domainType, buff, self.prop, self.duration = args
        self.effectiveBuff = buff * aprioriProbMod(self.prop, True)
        form.unit.inputHelper.parent = form.unit.inputHelper.parentMap[form.unit.inputHelper.parent]

    def applyToState(self, state):
        if state.form.checkCondition(self.condition, self.activated, True):
            self.activated = True
            start = state.turn
            end = start + self.duration - 1
            params = [start, end]
            state.support += DOMAIN_SUPPORT_FACTOR
            match self.domainType:
                case "Increase Damage Received":
                    state.form.abilities["Start of Turn"].extend(
                        [
                            TurnDependent(
                                state.form,
                                1,
                                False,
                                "ATK Support",
                                self.effectiveBuff * ATK_SUPPORT_100_FACTOR,
                                self.duration,
                                params,
                            ),
                            TurnDependent(state.form, 1, False, "P3 ATK", self.effectiveBuff, self.duration, params),
                        ]
                    )
                case "Alternate Dimensional Space":
                    extremeClassBuff = 0.1 * aprioriProbMod(
                        self.prop, True
                    )  # prop to account for may be buffing enemies too
                    explodRageMovBossBuff = 0.1 * aprioriProbMod(
                        0.5
                        * math.factorial(NUM_CATEGORIES - 2)
                        * math.factorial(NUM_CATEGORIES - AVG_NUM_CATEGORIES_PER_UNIT)
                        / (
                            math.factorial(NUM_CATEGORIES)
                            * math.factorial(NUM_CATEGORIES - AVG_NUM_CATEGORIES_PER_UNIT - 2)
                        ),
                        True,
                    )  # 0.5 to account for not all allies being exploding rage or movie bosses. The other part comes from calculating the probability an average enemy is not on the movie bosses or exploding rage categories.
                    state.form.abilities["Start of Turn"].extend(
                        [
                            TurnDependent(state.form, 1, False, "Dmg Red A", 0.26, self.duration, params),
                            TurnDependent(
                                state.form, 1, False, "Ki Support", 4 * KI_SUPPORT_FACTOR, self.duration, params
                            ),
                            TurnDependent(state.form, 1, False, "Ki", 4, self.duration, params),
                            TurnDependent(
                                state.form,
                                1,
                                False,
                                "ATK Support",
                                extremeClassBuff * ATK_SUPPORT_100_FACTOR,
                                self.duration,
                                params,
                            ),
                            TurnDependent(
                                state.form,
                                1,
                                False,
                                "DEF Support",
                                extremeClassBuff * DEF_SUPPORT_100_FACTOR,
                                self.duration,
                                params,
                            ),
                            TurnDependent(
                                state.form,
                                0.5,
                                True,
                                "ATK Support",
                                explodRageMovBossBuff * ATK_SUPPORT_100_FACTOR,
                                self.duration,
                                params,
                            ),
                            TurnDependent(
                                state.form,
                                0.5,
                                True,
                                "DEF Support",
                                explodRageMovBossBuff * DEF_SUPPORT_100_FACTOR,
                                self.duration,
                                params,
                            ),
                            TurnDependent(state.form, 1, False, "P3 ATK", 0.2, self.duration, params),
                            TurnDependent(state.form, 1, False, "P3 DEF", 0.2, self.duration, params),
                            TurnDependent(
                                state.form,
                                1,
                                False,
                                "ATK Support",
                                self.effectiveBuff * ATK_SUPPORT_100_FACTOR,
                                self.duration,
                                params,
                            ),
                            TurnDependent(state.form, 1, False, "P3 ATK", self.effectiveBuff, self.duration, params),
                        ]
                    )
                case "City (Future) (Rift in Time)":
                    extremeClassBuff = 0.1 * aprioriProbMod(
                        self.prop, True
                    )  # prop to account for may be buffing enemies too
                    superBossesBuff = 0.1 * aprioriProbMod(
                        math.factorial(NUM_CATEGORIES - 1)
                        * math.factorial(NUM_CATEGORIES - AVG_NUM_CATEGORIES_PER_UNIT)
                        / (
                            math.factorial(NUM_CATEGORIES)
                            * math.factorial(NUM_CATEGORIES - AVG_NUM_CATEGORIES_PER_UNIT - 1)
                        ),
                        True,
                    )  # The other part comes from calculating the probability an average enemy is not on the super bosses category.
                    state.form.abilities["Start of Turn"].extend(
                        [
                            TurnDependent(
                                state.form, 1, False, "Ki Support", 2 * KI_SUPPORT_FACTOR, self.duration, params
                            ),
                            TurnDependent(state.form, 1, False, "Ki", 2, self.duration, params),
                            TurnDependent(
                                state.form,
                                1,
                                False,
                                "ATK Support",
                                extremeClassBuff * ATK_SUPPORT_100_FACTOR,
                                self.duration,
                                params,
                            ),
                            TurnDependent(
                                state.form,
                                1,
                                False,
                                "DEF Support",
                                extremeClassBuff * DEF_SUPPORT_100_FACTOR,
                                self.duration,
                                params,
                            ),
                            TurnDependent(
                                state.form,
                                1,
                                False,
                                "ATK Support",
                                superBossesBuff * ATK_SUPPORT_100_FACTOR,
                                self.duration,
                                params,
                            ),
                            TurnDependent(
                                state.form,
                                1,
                                False,
                                "DEF Support",
                                superBossesBuff * DEF_SUPPORT_100_FACTOR,
                                self.duration,
                                params,
                            ),
                            TurnDependent(state.form, 1, False, "P3 ATK", 0.2, self.duration, params),
                            TurnDependent(state.form, 1, False, "P3 DEF", 0.2, self.duration, params),
                        ]
                    )
                case "Shining World of Void":
                    superClassBuff = 0.15 * aprioriProbMod(
                        self.prop, True
                    )  # prop to account for may be buffing enemies too
                    RoGBuff = 0.15 * aprioriProbMod(
                        2
                        / 3
                        * math.factorial(NUM_CATEGORIES - 1)
                        * math.factorial(NUM_CATEGORIES - AVG_NUM_CATEGORIES_PER_UNIT)
                        / (
                            math.factorial(NUM_CATEGORIES)
                            * math.factorial(NUM_CATEGORIES - AVG_NUM_CATEGORIES_PER_UNIT - 1)
                        ),
                        True,
                    )  # 2/3 comes from not every ally on RoG. The other part comes from calculating the probability an average enemy is not on the RoG category.
                    state.form.abilities["Start of Turn"].extend(
                        [
                            TurnDependent(
                                state.form, 1, False, "Ki Support", 4 * KI_SUPPORT_FACTOR, self.duration, params
                            ),
                            TurnDependent(state.form, 1, False, "Ki", 4, self.duration, params),
                            TurnDependent(
                                state.form,
                                1,
                                False,
                                "ATK Support",
                                superClassBuff * ATK_SUPPORT_100_FACTOR,
                                self.duration,
                                params,
                            ),
                            TurnDependent(
                                state.form,
                                1,
                                False,
                                "DEF Support",
                                superClassBuff * DEF_SUPPORT_100_FACTOR,
                                self.duration,
                                params,
                            ),
                            TurnDependent(
                                state.form,
                                1,
                                False,
                                "ATK Support",
                                RoGBuff * ATK_SUPPORT_100_FACTOR,
                                self.duration,
                                params,
                            ),
                            TurnDependent(
                                state.form,
                                1,
                                False,
                                "Disable Evasion Cancel Support",
                                RoGBuff * DISABLE_EVASION_CANCEL_SUPPORT_FACTOR,
                                self.duration,
                                params,
                            ),
                            TurnDependent(state.form, 1, False, "P3 ATK", 0.3, self.duration, params),
                            TurnDependent(state.form, 1, False, "P3 DEF", 0.15, self.duration, params),
                            TurnDependent(state.form, 1, False, "Disable Evasion Cancel", 1, self.duration, params),
                        ]
                    )
                case "Molten Lava of Natade Village":
                    UncontrollablePowerBuff = 0.15 * aprioriProbMod(
                        2
                        / 3
                        * math.factorial(NUM_CATEGORIES - 1)
                        * math.factorial(NUM_CATEGORIES - AVG_NUM_CATEGORIES_PER_UNIT)
                        / (
                            math.factorial(NUM_CATEGORIES)
                            * math.factorial(NUM_CATEGORIES - AVG_NUM_CATEGORIES_PER_UNIT - 1)
                        ),
                        True,
                    )  # 2/3 comes from not every ally on Uncontrollable Power. The other part comes from calculating the probability an average enemy is not on the Uncontrollable Power category.
                    MovieHeroesDebuff = 0.1 * aprioriProbMod(
                        1
                        - math.factorial(NUM_CATEGORIES - 1)
                        * math.factorial(NUM_CATEGORIES - AVG_NUM_CATEGORIES_PER_UNIT)
                        / (
                            math.factorial(NUM_CATEGORIES)
                            * math.factorial(NUM_CATEGORIES - AVG_NUM_CATEGORIES_PER_UNIT - 1)
                        ),
                        True,
                    )  # The other part comes from calculating the probability an average enemy is on the Movie Heroes category.
                    state.form.abilities["Start of Turn"].extend(
                        [
                            TurnDependent(state.form, 1, False, "Orb Change", 1, self.duration, params),
                            TurnDependent(state.form, 1, False, "Guard", 1, self.duration, params),
                            TurnDependent(state.form, 1, False, "AEAAT", 1, 99, params),
                            TurnDependent(
                                state.form,
                                1,
                                False,
                                "ATK Support",
                                UncontrollablePowerBuff * ATK_SUPPORT_100_FACTOR,
                                self.duration,
                                params,
                            ),
                            TurnDependent(
                                state.form,
                                1,
                                False,
                                "DEF Support",
                                UncontrollablePowerBuff * DEF_SUPPORT_100_FACTOR,
                                self.duration,
                                params,
                            ),
                            TurnDependent(
                                state.form,
                                1,
                                False,
                                "ATK Support",
                                MovieHeroesDebuff * ATK_SUPPORT_100_FACTOR,
                                self.duration,
                                params,
                            ),
                            TurnDependent(state.form, 1, False, "P3 ATK", 0.15 + MovieHeroesDebuff, self.duration, params),
                            TurnDependent(state.form, 1, False, "P3 DEF", 0.15, self.duration, params),
                            TurnDependent(
                                state.form,
                                1,
                                False,
                                "ATK Support",
                                self.effectiveBuff * ATK_SUPPORT_100_FACTOR,
                                self.duration,
                                params,
                            ),
                            TurnDependent(state.form, 1, False, "P3 ATK", self.effectiveBuff, self.duration, params),
                        ]
                    )
                case "Earth Shrouded in Clouds":
                    DemonicPowerBuff = 0.15 * aprioriProbMod(
                        1.0
                        * math.factorial(NUM_CATEGORIES - 1)
                        * math.factorial(NUM_CATEGORIES - AVG_NUM_CATEGORIES_PER_UNIT)
                        / (
                            math.factorial(NUM_CATEGORIES)
                            * math.factorial(NUM_CATEGORIES - AVG_NUM_CATEGORIES_PER_UNIT - 1)
                        ),
                        True,
                    )  # 1.0 comes from every ally being on Uncontrollable Power. The other part comes from calculating the probability an average enemy is not on the Demonic Power category.
                    EarthBredFightersDebuff = 0.15 * aprioriProbMod(
                        1
                        - math.factorial(NUM_CATEGORIES - 1)
                        * math.factorial(NUM_CATEGORIES - AVG_NUM_CATEGORIES_PER_UNIT)
                        / (
                            math.factorial(NUM_CATEGORIES)
                            * math.factorial(NUM_CATEGORIES - AVG_NUM_CATEGORIES_PER_UNIT - 1)
                        ),
                        True,
                    )  # The other part comes from calculating the probability an average enemy is on the Earth-Bred Fighters category.
                    state.form.abilities["Start of Turn"].extend(
                        [
                            TurnDependent(state.form, 1, False, "Heal", 0.1, self.duration, params),
                            TurnDependent(state.form, 1, False, "Ki", 2, self.duration, params),
                            TurnDependent(state.form, 1, False, "Ki Support", 2, self.duration, params),
                            TurnDependent(
                                state.form,
                                1,
                                False,
                                "ATK Support",
                                DemonicPowerBuff * ATK_SUPPORT_100_FACTOR,
                                self.duration,
                                params,
                            ),
                            TurnDependent(
                                state.form,
                                1,
                                False,
                                "DEF Support",
                                DemonicPowerBuff * DEF_SUPPORT_100_FACTOR,
                                self.duration,
                                params,
                            ),
                            TurnDependent(
                                state.form,
                                1,
                                False,
                                "ATK Support",
                                EarthBredFightersDebuff * ATK_SUPPORT_100_FACTOR,
                                self.duration,
                                params,
                            ),
                            TurnDependent(state.form, 1, False, "P3 ATK", 0.15 + EarthBredFightersDebuff, self.duration, params),
                            TurnDependent(state.form, 1, False, "P3 DEF", 0.15, self.duration, params),
                            TurnDependent(
                                state.form,
                                1,
                                False,
                                "ATK Support",
                                self.effectiveBuff * ATK_SUPPORT_100_FACTOR,
                                self.duration,
                                params,
                            ),
                            TurnDependent(state.form, 1, False, "P3 ATK", self.effectiveBuff, self.duration, params),
                        ]
                    )
                case "Inside Majin Buu":
                    PowerAbsorptionOrTransformationBoostBuff = 0.15 * aprioriProbMod(
                        1.0
                        * math.factorial(NUM_CATEGORIES - 2)
                        * math.factorial(NUM_CATEGORIES - AVG_NUM_CATEGORIES_PER_UNIT)
                        / (
                            math.factorial(NUM_CATEGORIES)
                            * math.factorial(NUM_CATEGORIES - AVG_NUM_CATEGORIES_PER_UNIT - 2)
                        ),
                        True,
                    )  # 1.0 comes from every ally being on either Power Absoption or Transformation Boost. The other part comes from calculating the probability an average enemy is not on either category.
                    MajinBuuSagaBuff = 0.15 * aprioriProbMod(
                        0.75
                        * math.factorial(NUM_CATEGORIES - 1)
                        * math.factorial(NUM_CATEGORIES - AVG_NUM_CATEGORIES_PER_UNIT)
                        / (
                            math.factorial(NUM_CATEGORIES)
                            * math.factorial(NUM_CATEGORIES - AVG_NUM_CATEGORIES_PER_UNIT - 1)
                        ),
                        True,
                    )  # 0.75 comes from 75% of allies being on either Power Absoption or Transformation Boost. The other part comes from calculating the probability an average enemy is not on either category.
                    state.form.abilities["Start of Turn"].extend(
                        [
                            TurnDependent(
                                state.form,
                                1,
                                False,
                                "ATK Support",
                                (PowerAbsorptionOrTransformationBoostBuff + MajinBuuSagaBuff) * ATK_SUPPORT_100_FACTOR,
                                self.duration,
                                params,
                            ),
                            TurnDependent(
                                state.form,
                                1,
                                False,
                                "DEF Support",
                                (PowerAbsorptionOrTransformationBoostBuff + MajinBuuSagaBuff) * DEF_SUPPORT_100_FACTOR,
                                self.duration,
                                params,
                            ),
                            TurnDependent(state.form, 1, False, "P3 ATK", 0.3, self.duration, params),
                            TurnDependent(state.form, 1, False, "P3 DEF", 0.3, self.duration, params),
                        ]
                    )
                case "Cell Games Arena":
                    AndroidsOrAndroidsCellSagaBuff = 0.15 * aprioriProbMod(
                        0.5
                        * math.factorial(NUM_CATEGORIES - 2)
                        * math.factorial(NUM_CATEGORIES - AVG_NUM_CATEGORIES_PER_UNIT)
                        / (
                            math.factorial(NUM_CATEGORIES)
                            * math.factorial(NUM_CATEGORIES - AVG_NUM_CATEGORIES_PER_UNIT - 2)
                        ),
                        True,
                    )  # 0.5 comes from every ally being on either Androids or Androids/CellSaga. The other part comes from calculating the probability an average enemy is not on either category.
                    TournamentParticipantsBuff = 0.15 * aprioriProbMod(
                        1/3
                        * math.factorial(NUM_CATEGORIES - 1)
                        * math.factorial(NUM_CATEGORIES - AVG_NUM_CATEGORIES_PER_UNIT)
                        / (
                            math.factorial(NUM_CATEGORIES)
                            * math.factorial(NUM_CATEGORIES - AVG_NUM_CATEGORIES_PER_UNIT - 1)
                        ),
                        True,
                    )  # 1/3 comes from 1/3 of allies being on Tournament Particiapants. The other part comes from calculating the probability an average enemy is not on either category.
                    state.form.abilities["Start of Turn"].extend(
                        [
                            TurnDependent(
                                state.form,
                                1,
                                False,
                                "ATK Support",
                                (AndroidsOrAndroidsCellSagaBuff + TournamentParticipantsBuff) * ATK_SUPPORT_100_FACTOR,
                                self.duration,
                                params,
                            ),
                            TurnDependent(
                                state.form,
                                1,
                                False,
                                "DEF Support",
                                (AndroidsOrAndroidsCellSagaBuff + TournamentParticipantsBuff) * DEF_SUPPORT_100_FACTOR,
                                self.duration,
                                params,
                            ),
                            TurnDependent(state.form, 1, False, "P3 ATK", 0.3, self.duration, params),
                            TurnDependent(state.form, 1, False, "P3 DEF", 0.3, self.duration, params),
                        ]
                    )
                case "Earth Shrouded in Minus Energy":
                    InhumanDeedsOrPowerAbsorptionOrGTBossesBuff = 0.25 * aprioriProbMod(
                        1.0
                        * math.factorial(NUM_CATEGORIES - 3)
                        * math.factorial(NUM_CATEGORIES - AVG_NUM_CATEGORIES_PER_UNIT)
                        / (
                            math.factorial(NUM_CATEGORIES)
                            * math.factorial(NUM_CATEGORIES - AVG_NUM_CATEGORIES_PER_UNIT - 3)
                        ),
                        True,
                    )  # 0.5 comes from every ally being on either Androids or Androids/CellSaga. The other part comes from calculating the probability an average enemy is not on either category.
                    EarthProtectingHeroesFusedFightersGTHeroesDeBuff = 0.1 * aprioriProbMod(
                        3
                        - math.factorial(NUM_CATEGORIES - 3)
                        * math.factorial(NUM_CATEGORIES - AVG_NUM_CATEGORIES_PER_UNIT)
                        / (
                            math.factorial(NUM_CATEGORIES)
                            * math.factorial(NUM_CATEGORIES - AVG_NUM_CATEGORIES_PER_UNIT - 3)
                        ),
                        True,
                    )  # The other part comes from calculating the probability an average enemy is on the Earth Protecting heroes, fused fighters or GT heroes categories.
                    state.form.abilities["Start of Turn"].extend(
                        [
                            TurnDependent(
                                state.form,
                                1,
                                False,
                                "ATK Support",
                                (InhumanDeedsOrPowerAbsorptionOrGTBossesBuff + 0.2 * self.prop + EarthProtectingHeroesFusedFightersGTHeroesDeBuff) * ATK_SUPPORT_100_FACTOR,
                                self.duration,
                                params,
                            ),
                            TurnDependent(state.form, 1, False, "P3 ATK", 0.25 * self.prop * 0.2 + EarthProtectingHeroesFusedFightersGTHeroesDeBuff, self.duration, params),
                        ]
                    )
                case _:
                    raise Exception(f"{self.domainType} Domain Type not implemented!")


class ActiveSkillBuff(SingleTurnAbility):
    def __init__(self, form, args):
        super().__init__(form)
        self.effect, self.buff, self.duration, self.maxActivations = args
        self.activations = 0

    def applyToState(self, state):
        if self.form.checkCondition(self.condition, self.activations == self.maxActivations, True) and (
            self.form.unit.fightPeak or self.duration > 1
        ):
            self.activations += 1
            start = state.turn
            end = start + self.duration - 1
            params = [start, end]
            if self.effect in P3_EFFECTS_SUFFIX:
                self.effect = "P3 " + self.effect
            ability = TurnDependent(
                self.form, 1, False, self.effect, self.buff, effectDuration=self.duration, args=params
            )
            self.form.abilities["Start of Turn"].append(ability)


class ActiveSkillAttack(SingleTurnAbility):
    def __init__(self, form, args):
        super().__init__(form)
        attackMultiplier, attackBuff, self.p2AttackBuff, self.triggersTransformation = args
        self.activeMult = specialAttackConversion[attackMultiplier] + attackBuff

    def applyToState(self, state):
        if self.form.checkCondition(self.condition, self.activated, True) and self.form.unit.fightPeak:
            self.activated = True
            state.attacksPerformed += 1  # Parameter should be used to determine buffs from per attack performed buffs
            state.superAttacksPerformed += 1
            state.activeSkillAttackActivated = True
            activeAtk = (
                state.getActiveAtk(
                    rarity2MaxKi[state.form.unit.rarity], state.p2Buff["ATK"] + self.p2AttackBuff, self.activeMult
                )
            )
            activeDmgNoLookAhead = state.atk2Dmg(activeAtk, state.multiChanceBuff["Crit"].prob, False)
            activeDmgLookAhead = state.atk2Dmg(activeAtk, state.multiChanceBuff["Crit"].prob, True)
            if yesNo2Bool[self.triggersTransformation]:
                self.form.unit.transformationAttackDPTNoLookAhead = activeDmgNoLookAhead
                self.form.unit.transformationAttackDPTLookAhead = activeDmgLookAhead

                self.form.unit.transformationTriggered = True
                self.form.unit.nextForm = 1
            else:
                state.DPTNoLookAhead += activeDmgNoLookAhead
                state.DPTLookAhead += activeDmgLookAhead


# This skill is to apply to a unit already in it's standby mode.
# The condition to enter & exit the standy mode will be controlled by regular form changes.
class StandbyFinishSkill(SingleTurnAbility):
    def __init__(self, form, args):
        super().__init__(form)
        self.finishSkillChargeCondition, attackMultiplier, self.attackBuff, self.buffPerCharge = args
        self.activeMult = specialAttackConversion[attackMultiplier]

    def applyToState(self, state):
        if self.finishSkillChargeCondition in START_OF_TURN_FINISH_EFFECT_CONDITIONS:
            state.form.charge += state.form.getCharge(self.finishSkillChargeCondition)
        if state.form.checkCondition(self.condition, self.activated, True):
            self.activated = True
            self.activeMult += self.buffPerCharge * state.form.charge
            self.form.unit.transformationAttackDPTNoLookAhead = state.atk2Dmg(
                state.getActiveAtk(
                    rarity2MaxKi[self.form.unit.rarity], state.p2Buff["ATK"], self.activeMult * (1 + self.attackBuff)
                )
            , state.multiChanceBuff["Crit"].prob, False)
            self.form.unit.transformationAttackDPTLookAhead = state.atk2Dmg(
                state.getActiveAtk(
                    rarity2MaxKi[self.form.unit.rarity], state.p2Buff["ATK"], self.activeMult * (1 + self.attackBuff)
                )
            , state.multiChanceBuff["Crit"].prob, True)
            self.form.unit.transformationTriggered = True
            if self.form.unit.numForms > self.form.formIdx:
                self.form.unit.nextForm = 1
            else:
                self.form.unit.nextForm = -1
        if self.finishSkillChargeCondition in END_OF_TURN_FINISH_EFFECT_CONDITIONS:
            self.form.charge += self.form.getCharge(self.finishSkillChargeCondition)


class RevivalCounterFinishSkill(StandbyFinishSkill):
    def __init__(self, form, args):
        args = ["Revive"] + args + [0]
        super().__init__(form, args)


class SACounterFinishSkill(StandbyFinishSkill):
    def __init__(self, form, args):
        args = ["SA Counter"] + args + [0]
        super().__init__(form, args)


class PassiveAbility(Ability):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, effectDuration=None):
        super().__init__(form)
        self.activationProbability = aprioriProbMod(activationProbability, knownApriori)
        self.effect = effect
        self.effectDuration = effectDuration if effectDuration != None else 1
        self.effectiveBuff = buff * self.activationProbability
        if effect == "AAChance":
            self.superChance = form.unit.inputHelper.getAndSaveUserInput(
                "What is the chance for this to become a super?", default=0.0
            )
        if effect in SUPPORT_EFFECTS and effectDuration == None:
            self.effectDuration = form.unit.inputHelper.getAndSaveUserInput(
                "How many turns does the effect last for?", default=1
            )
        self.supportBuff = self.effectiveBuff * np.minimum(self.effectDuration, RETURN_PERIOD_PER_SLOT)


class Buff(PassiveAbility):
    def __init__(
        self,
        form,
        activationProbability,
        knownApriori,
        effect,
        buff,
        effectDuration=None,
        start=1,
        end=MAX_TURN,
        ki=0,
        slots=SLOTS,
        args=[],
    ):
        super().__init__(form, activationProbability, knownApriori, effect, buff, effectDuration)
        self.start = start
        self.end = end
        self.ki = ki
        self.slots = slots

    def applyToState(self, state):
        # Need to update in case one of the relevant variables has been updated
        if state.activeSkillAttackActivated:
            pHaveKi = 1
        else:
            pHaveKi = 1 - ZTP_CDF(self.ki - 1 - state.buff["Ki"], state.randomKi)
        effectiveBuff = self.effectiveBuff * pHaveKi
        supportBuff = self.supportBuff[state.slot - 1] * pHaveKi
        activationProbability = self.activationProbability * pHaveKi
        # Check if state is elligible for ability
        if (state.turn >= self.start) and (state.turn <= self.end) and (state.slot in self.slots):
            # If a support ability
            if self.effect in REGULAR_SUPPORT_EFFECTS:
                state.support += supportFactorConversion[self.effect] * supportBuff
            elif self.effect in ORB_CHANGING_EFFECTS:
                state.support += supportFactorConversion[self.effect] * supportBuff
                state.orbCollection.addOrbChange(self.effect, activationProbability)
            elif self.effect in state.buff.keys():
                state.buff[self.effect] += effectiveBuff
            elif self.effect in state.p1Buff.keys():
                state.p1Buff[self.effect] += effectiveBuff
            elif self.effect in MULTI_CHANCE_EFFECTS_NO_NULLIFY:
                state.multiChanceBuff[self.effect].updateChance("Start of Turn", effectiveBuff, self.effect, state)
            else:  # Edge cases
                match self.effect:
                    case "Dmg Red against Normals":
                        state.dmgRedNormalA += effectiveBuff
                        state.dmgRedNormalB += effectiveBuff
                    case "Dmg Red against Supers":
                        state.dmgRedSuperA += effectiveBuff
                        state.dmgRedSuperB += effectiveBuff
                    case "Guard":
                        state.guard += effectiveBuff
                    case "Dmg Red":
                        state.dmgRedNormalA += effectiveBuff
                        state.dmgRedNormalB += effectiveBuff
                        state.dmgRedSuperA += effectiveBuff
                        state.dmgRedSuperB += effectiveBuff
                    case "Dmg Red A":
                        state.dmgRedSuperA += effectiveBuff
                        state.dmgRedNormalA += effectiveBuff
                    case "Dmg Red B":
                        state.dmgRedSuperB += effectiveBuff
                        state.dmgRedNormalB += effectiveBuff
                    case "Evasion":
                        state.multiChanceBuff["EvasionA"].updateChance("Start of Turn", effectiveBuff, "EvasionA", state)
                        state.multiChanceBuff["EvasionB"].updateChance("Start of Turn", effectiveBuff, "EvasionB", state)
                    case "EvasionA":
                        state.multiChanceBuff["EvasionA"].updateChance("Start of Turn", effectiveBuff, "EvasionA", state)
                    case "EvasionB":
                        state.multiChanceBuff["EvasionB"].updateChance("Start of Turn", effectiveBuff, "EvasionB", state)
                    case "Evasion against Supers":
                        state.evadeSuper += effectiveBuff
                    case "Disable Action B":
                        state.disableAction()
                    case "AdditionalSuper":
                        state.aaPSuper.append(activationProbability)
                        state.aaPGuarantee.append(0)
                    case "AAChance":
                        state.aaPGuarantee.append(activationProbability)
                        state.aaPSuper.append(activationProbability * self.superChance)
                    case "Ki (Type Ki Sphere)":
                        state.orbCollection.kiPerOrb["Other"] += effectiveBuff
                        state.orbCollection.kiPerOrb["Same"] += effectiveBuff
                    case "Ki (Ki Sphere)":
                        state.orbCollection.kiPerOrb["Other"] += effectiveBuff
                        state.orbCollection.kiPerOrb["Same"] += effectiveBuff
                        state.orbCollection.kiPerOrb["Rainbow"] += effectiveBuff
                    case "Ki (Same Type Ki Sphere)":
                        state.orbCollection.kiPerOrb["Same"] += effectiveBuff
                    case "Ki (Rainbow Ki Sphere)":
                        state.orbCollection.kiPerOrb["Rainbow"] += effectiveBuff
                    case "P2 ATK":
                        state.p2Buff["ATK"] += effectiveBuff
                    case "P2 DEF":
                        state.p2Buff["DEF"] += effectiveBuff
                    case "P2 DEF B":
                        state.p2DefB += effectiveBuff
                    case "P2 DEF against Normals":
                        state.p2DefNormal += effectiveBuff
                    case "P2 DEF against Supers":
                        state.p2DefSuper += effectiveBuff
                    case "P3 ATK":
                        state.p3Buff["ATK"] += effectiveBuff
                    case "P3 DEF":
                        state.p3Buff["DEF"] += effectiveBuff
                    case "P3 Crit":
                        state.multiChanceBuff["Crit"].updateChance("Active Skill", effectiveBuff, "Crit", state)
                        state.setNoCritAtkMod()
                    case "P3 Evasion":
                        state.multiChanceBuff["EvasionA"].updateChance("Active Skill", effectiveBuff, "EvasionA", state)
                        state.multiChanceBuff["EvasionB"].updateChance("Active Skill", effectiveBuff, "EvasionB", state)
                    case "P3 Disable Action":
                        state.numSuperAttacksDirectedBeforeAttacking -= disableActionActiveDisableSuper[state.slot] * (
                            1 - ENEMY_DODGE_CHANCE + ENEMY_DODGE_CHANCE * state.buff["Attacks Guaranteed to Hit"]
                        )
                        state.numAttacksDirected -= disableActionActiveDisableNormal[state.slot]
                        state.numNormalAttacksDirectedBeforeAttacking -= disableActionActiveDisableNormal[
                            state.slot
                        ] * (1 - ENEMY_DODGE_CHANCE + ENEMY_DODGE_CHANCE * state.buff["Attacks Guaranteed to Hit"])
                        state.support += disableActionActiveSupportFactorConversion[state.slot] * supportBuff
                    case "Delay Target":
                        state.support += supportFactorConversion[self.effect] * supportBuff
                        state.dmgRedSuperA = 1
                        state.dmgRedSuperB = 1
                        state.dmgRedNormalA = 1
                        state.dmgRedNormalB = 1
                        state.numAttacksReceived = 0
                        state.numAttacksDirected = 0
                        state.numAttacksReceivedBeforeAttacking = 0
                        state.numAttacksReceivedAfterAttacking = 0
                        state.numAttacksEvaded = 0
                        state.numAttacksEvadedBeforeAttacking = 0
                        state.numSuperAttacksReceivedBeforeAttacking = 0
                        state.numSuperAttacksReceived = 0
                    case "Intercept":
                        pEvade = state.multiChanceBuff["EvasionA"].prob * (1 - DODGE_CANCEL_FACTOR * (1 - state.buff["Disable Evasion Cancel"]))
                        state.support += supportFactorConversion[self.effect] * supportBuff
                        state.numAttacksReceivedBeforeAttacking = NUM_CUMULATIVE_ATTACKS_BEFORE_ATTACKING[state.slot - 1] * (1 - pEvade)
                        state.numAttacksReceivedAfterAttacking = (NUM_ATTACKS_PER_TURN - NUM_CUMULATIVE_ATTACKS_BEFORE_ATTACKING[state.slot - 1]) * (1 - pEvade)
                        state.numAttacksDirected = NUM_ATTACKS_PER_TURN
                        state.numAttacksDirectedBeforeAttacking = NUM_CUMULATIVE_ATTACKS_BEFORE_ATTACKING[state.slot - 1]
                        state.numAttacksDirectedAfterAttacking = NUM_ATTACKS_PER_TURN - NUM_CUMULATIVE_ATTACKS_BEFORE_ATTACKING[state.slot - 1]
                        state.numAttacksEvaded = NUM_ATTACKS_PER_TURN * pEvade
                        state.numAttacksEvadedBeforeAttacking = NUM_CUMULATIVE_ATTACKS_BEFORE_ATTACKING[state.slot - 1] * pEvade
                        state.numAttacksReceived = state.numAttacksDirected * (1 - pEvade)
                        state.numSuperAttacksReceivedBeforeAttacking = state.numAttacksReceivedBeforeAttacking * (1 - FRAC_NORMAL)
                        state.numSuperAttacksReceived = state.numAttacksReceived * (1 - FRAC_NORMAL)
                    case "Stunned":
                        state.canAttack = False
                    case _:
                        raise Exception(f"{self.effect} Buff Effect not implemented!")
            state.randomKi = state.getRandomKi()


class TurnDependent(Buff):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, effectDuration=None, args=[]):
        start, end = args
        super().__init__(form, activationProbability, knownApriori, effect, buff, effectDuration, start=start, end=end)


class KiDependent(Buff):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args):
        ki = args[0]
        super().__init__(form, activationProbability, knownApriori, effect, buff, ki=ki)


class SlotDependent(Buff):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args):
        slots = args[0]
        super().__init__(form, activationProbability, knownApriori, effect, buff, slots=slots)


class HealthDependent(Buff):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args):
        health, isMaxHpCondition = args
        p = maxHealthCDF(health)
        if yesNo2Bool[isMaxHpCondition]:
            activationProbability *= p
        else:
            activationProbability *= 1 - p
        super().__init__(form, activationProbability, True, effect, buff)


class HealthScale(Buff):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args):
        isMoreHPBetter = args[0]
        if yesNo2Bool[isMoreHPBetter]:
            expectedBuff = MORE_HEALTH_REMAINING_MIN + EXPECTED_HEALTH_FRAC * (buff - MORE_HEALTH_REMAINING_MIN)
        else:
            expectedBuff = LESS_HEALTH_REMAINING_MIN + (1 - EXPECTED_HEALTH_FRAC) * (buff - LESS_HEALTH_REMAINING_MIN)
        super().__init__(form, activationProbability, True, effect, expectedBuff)


class PerEvent(PassiveAbility):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, max):
        super().__init__(form, activationProbability, knownApriori, effect, buff)
        self.max = max
        self.applied = 0


class PerKi(PerEvent):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args):
        super().__init__(form, activationProbability, knownApriori, effect, buff, args[0])

    def applyToState(self, state):
        ki = min(round(state.buff["Ki"] + state.randomKi), rarity2MaxKi[state.form.unit.rarity])
        effectiveBuff = min(self.effectiveBuff * ki, self.max)
        supportBuff = effectiveBuff * np.minimum(self.effectDuration, RETURN_PERIOD_PER_SLOT)
        if self.effect in REGULAR_SUPPORT_EFFECTS:
            state.support += supportFactorConversion[self.effect] * supportBuff[state.slot - 1]
        else:
            match self.effect:
                case "ATK":
                    state.p2Buff["ATK"] += effectiveBuff
                case "DEF":
                    state.p2Buff["DEF"] += effectiveBuff
                case "P2 DEF B":
                    state.p2DefB += effectiveBuff
                case _:
                    raise Exception(f"{self.effect} Per Ki Buff Effect not implemented!")

class PerTurn(PerEvent):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args):
        super().__init__(form, activationProbability, knownApriori, effect, buff, args[0])
        self.appliedAtStartOfTurn = yesNo2Bool[args[1]]
        self.initialTurn = args[2]

    def applyToState(self, state):
        if (
            not (self.appliedAtStartOfTurn) and state.turn - (state.form.initialTurn - 1) == self.initialTurn
        ) or state.turn - (state.form.initialTurn - 1) < self.initialTurn:
            isActive = 0
        else:
            isActive = 1
        self.applied += self.effectiveBuff * isActive
        self.applied = min(self.max, self.applied, key=abs)

        if self.effect in REGULAR_SUPPORT_EFFECTS:
            state.support += supportFactorConversion[self.effect] * self.supportBuff[state.slot - 1] * isActive
        else:
            match self.effect:
                case "Ki":
                    state.buff["Ki"] += self.applied
                case "ATK":
                    state.p1Buff["ATK"] += self.applied
                case "DEF":
                    state.p1Buff["DEF"] += self.applied
                case "Crit":
                    state.multiChanceBuff["Crit"].updateChance("On Super", self.applied, "Crit", state)
                    state.setNoCritAtkMod()
                case "Dmg Red":
                    state.dmgRedSuperA += self.applied
                    state.dmgRedSuperB += self.applied
                    state.dmgRedNormalA += self.applied
                    state.dmgRedNormalB += self.applied
                case "Evasion":
                    state.multiChanceBuff["EvasionA"].updateChance("Start of Turn", self.applied, "EvasionA", state)
                    state.multiChanceBuff["EvasionB"].updateChance("Start of Turn", self.applied, "EvasionB", state)
                case _:
                    raise Exception(f"{self.effect} Per Turn Buff Effect not implemented!")


class PerAttackPerformed(PerEvent):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args):
        super().__init__(form, activationProbability, knownApriori, effect, buff, args[0])
        self.requiresSuperAttack = yesNo2Bool[args[1]]
        self.withinTheSameTurn = yesNo2Bool[args[2]]
        self.slots = literal_eval(str(args[3]))

    def applyToState(self, state):
        if state.slot in self.slots:
            cumBuffPerAttack = self.effectiveBuff * (np.arange(len(state.aaPSuper) + 1) + 1)
            if self.requiresSuperAttack:
                turnBuff = self.effectiveBuff * state.superAttacksPerformed
            else:
                turnBuff = self.effectiveBuff * state.attacksPerformed
            buffToGo = self.max - self.applied
            cappedTurnBuff = min(buffToGo, turnBuff)
            cappedCumBuffPerAttack = np.sign(buffToGo) * np.minimum(abs(cumBuffPerAttack), abs(buffToGo))
            cappedBuffPerAttack = np.insert(np.diff(cappedCumBuffPerAttack), 0, cappedCumBuffPerAttack[0])
            if not (self.requiresSuperAttack) and self.effect in ["ATK", "Crit"]:
                match self.effect:
                    case "ATK":
                        state.atkPerAttackPerformed = cappedCumBuffPerAttack
                    case "Crit":
                        state.critPerAttackPerformed = cappedBuffPerAttack
            match self.effect:
                case "Ki":
                    pass  # Handled by carryOverBuffs
                case "ATK":
                    state.atkPerSuperPerformed = cappedCumBuffPerAttack
                case "DEF":
                    state.p2DefB += cappedTurnBuff
                case "Crit":
                    state.critPerSuperPerformed = cappedBuffPerAttack
                case "Dmg Red":
                    state.dmgRedSuperB += cappedTurnBuff
                    state.dmgRedNormalB += cappedTurnBuff
                case "Evasion":
                    state.multiChanceBuff["EvasionB"].updateChance("Start of Turn", cappedTurnBuff, "EvasionB", state)
                case _:
                    raise Exception(f"{self.effect} Per Attack Performed Buff Effect not implemented!")
            if not (self.withinTheSameTurn):
                state.form.carryOverBuffs[self.effect].add(cappedTurnBuff)
                self.applied += cappedTurnBuff


class PerAttackReceived(PerEvent):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args):
        super().__init__(form, activationProbability, knownApriori, effect, buff, args[0])
        self.withinTheSameTurn = yesNo2Bool[args[1]]
        self.requiresSuperAttack = yesNo2Bool[args[2]]

    def applyToState(self, state):
        if (self.requiresSuperAttack):
            numAttacksReceived = state.numSuperAttacksReceived
            numAttacksReceivedBeforeAttacking = state.numSuperAttacksReceivedBeforeAttacking
        else:
            numAttacksReceived = state.numAttacksReceived
            numAttacksReceivedBeforeAttacking = state.numAttacksReceivedBeforeAttacking
        cumBuffPerAttack = self.effectiveBuff * (np.arange(NUM_ATTACKS_PER_TURN) + 1)
        turnBuff = self.effectiveBuff * numAttacksReceived
        buffToGo = self.max - self.applied
        cappedTurnBuff = min(buffToGo, turnBuff, key=abs)
        cappedCumBuffPerAttack = np.sign(buffToGo) * np.minimum(abs(cumBuffPerAttack), abs(buffToGo))
        cappedBuffPerAttack = np.insert(np.diff(cappedCumBuffPerAttack), 0, cappedCumBuffPerAttack[0])
        match self.effect:
            case "Ki":
                state.buff["Ki"] += min(self.effectiveBuff * numAttacksReceivedBeforeAttacking, buffToGo, key=abs)
            case "ATK":
                preAtkBuff = min(self.effectiveBuff * numAttacksReceivedBeforeAttacking, buffToGo)
                state.p2Buff["ATK"] += preAtkBuff
                state.p2ATKBuffPostAtttack += min(
                    self.effectiveBuff * (numAttacksReceived - numAttacksReceivedBeforeAttacking), buffToGo - preAtkBuff, key=abs
                )
            case "DEF":
                state.defBuffStatuses[("DEF", "Receive")] += cappedBuffPerAttack
            case "Dmg Red":
                state.defBuffStatuses[("DmgRed", "Receive")] += cappedBuffPerAttack
            case "Crit":
                state.multiChanceBuff["Crit"].updateChance(
                    "On Super",
                    min(self.effectiveBuff * numAttacksReceivedBeforeAttacking, buffToGo, key=abs),
                    "Crit",
                    state,
                )
                state.setNoCritAtkMod()
            case _:
                raise Exception(f"{self.effect} Per Attack Received Buff Effect not implemented!")
        if not (self.withinTheSameTurn):
            state.form.carryOverBuffs[self.effect].add(cappedTurnBuff)
            self.applied += cappedTurnBuff


class PerAttackReceivedOrEvaded(PerEvent):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args):
        super().__init__(form, activationProbability, knownApriori, effect, buff, args[0])
        self.withinTheSameTurn = yesNo2Bool[args[1]]
        self.slots = literal_eval(str(args[2]))
        self.requiresSuperAttack = yesNo2Bool[args[3]]

    def applyToState(self, state):
        if state.slot in self.slots:
            if (self.requiresSuperAttack):
                numAttacksDirected = state.numSuperAttacksDirectedBeforeAttacking + state.numSuperAttacksDirectedAfterAttacking
                numAttacksDirectedBeforeAttacking = state.numSuperAttacksDirectedBeforeAttacking
            else:
                numAttacksDirected = state.numAttacksDirected
                numAttacksDirectedBeforeAttacking = state.numAttacksDirectedBeforeAttacking
            cumBuffPerAttack = self.effectiveBuff * (np.arange(NUM_ATTACKS_PER_TURN) + 1)
            turnBuff = self.effectiveBuff * numAttacksDirected
            buffToGo = self.max - self.applied
            cappedTurnBuff = min(buffToGo, turnBuff)
            cappedCumBuffPerAttack = np.sign(buffToGo) * np.minimum(abs(cumBuffPerAttack), abs(buffToGo))
            cappedBuffPerAttack = np.insert(np.diff(cappedCumBuffPerAttack), 0, cappedCumBuffPerAttack[0])
            match self.effect:
                case "Ki":
                    state.buff["Ki"] += min(self.effectiveBuff * numAttacksDirectedBeforeAttacking, buffToGo, key=abs)
                case "ATK":
                    preAtkBuff = min(self.effectiveBuff * numAttacksDirectedBeforeAttacking, buffToGo)
                    state.p2Buff["ATK"] += preAtkBuff
                    state.p2ATKBuffPostAtttack += min(
                        self.effectiveBuff * (numAttacksDirected - numAttacksDirectedBeforeAttacking), buffToGo - preAtkBuff, key=abs
                    )
                case "Crit":
                    state.multiChanceBuff["Crit"].updateChance(
                        "On Super",
                        min(self.effectiveBuff * numAttacksDirectedBeforeAttacking, buffToGo, key=abs),
                        "Crit",
                        state,
                    )
                    state.setNoCritAtkMod()
                case "DEF":
                    state.defBuffStatuses[("DEF", "ReceiveOrEvade")] += cappedBuffPerAttack
                case "Dmg Red":
                    state.defBuffStatuses[("DmgRed", "ReceiveOrEvade")] += cappedBuffPerAttack
                case "Evasion":
                    state.defBuffStatuses[("Evasion", "ReceiveOrEvade")] += cappedBuffPerAttack
                case _:
                    raise Exception(f"{self.effect} Per Attack Received Or Evaded Buff Effect not implemented!")
            if not (self.withinTheSameTurn):
                state.form.carryOverBuffs[self.effect].add(cappedTurnBuff)
                self.applied += cappedTurnBuff


class PerAttackGuarded(PerEvent):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args):
        super().__init__(form, activationProbability, knownApriori, effect, buff, args[0])

    def applyToState(self, state):
        cumBuffPerAttack = self.effectiveBuff * (np.arange(NUM_ATTACKS_PER_TURN) + 1)
        turnBuff = self.effectiveBuff * state.numAttacksReceived * state.guard
        buffToGo = self.max - self.applied
        cappedTurnBuff = min(buffToGo, turnBuff)
        state.form.carryOverBuffs[self.effect].add(cappedTurnBuff)
        cappedCumBuffPerAttack = np.sign(buffToGo) * np.minimum(abs(cumBuffPerAttack), abs(buffToGo))
        cappedBuffPerAttack = np.insert(np.diff(cappedCumBuffPerAttack), 0, cappedCumBuffPerAttack[0])
        match self.effect:
            case "Ki":
                state.buff["Ki"] += min(self.effectiveBuff * state.numAttacksReceivedBeforeAttacking, buffToGo)
            case "ATK":
                preAtkBuff = min(self.effectiveBuff * state.numAttacksReceivedBeforeAttacking * state.guard, buffToGo)
                state.p2Buff["ATK"] += preAtkBuff
                state.p2ATKBuffPostAtttack += min(
                    self.effectiveBuff * (state.numAttacksReceived - state.numAttacksReceivedBeforeAttacking) * state.guard, buffToGo - preAtkBuff, key=abs
                )
            case "DEF":
                state.defBuffStatuses[("DEF", "Receive")] += cappedBuffPerAttack
            case "Dmg Red":
                state.defBuffStatuses[("DmgRed", "Receive")] += cappedBuffPerAttack
            case "Crit":
                state.multiChanceBuff["Crit"].updateChance(
                    "On Super",
                    min(self.effectiveBuff * state.numAttacksReceivedBeforeAttacking, buffToGo),
                    "Crit",
                    state,
                )
                state.setNoCritAtkMod()
            case _:
                raise Exception(f"{self.effect} Per Attack Guarded Buff Effect not implemented!")
        self.applied += cappedTurnBuff


class PerAttackEvaded(PerEvent):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args):
        super().__init__(form, activationProbability, knownApriori, effect, buff, args[0])
        self.withinTheSameTurn = yesNo2Bool[args[1]]

    def applyToState(self, state):
        cumBuffPerAttack = self.effectiveBuff * (np.arange(NUM_ATTACKS_PER_TURN) + 1)
        turnBuff = self.effectiveBuff * state.numAttacksEvaded
        buffToGo = self.max - self.applied
        cappedTurnBuff = min(buffToGo, turnBuff)
        cappedCumBuffPerAttack = np.sign(buffToGo) * np.minimum(abs(cumBuffPerAttack), abs(buffToGo))
        cappedBuffPerAttack = np.insert(np.diff(cappedCumBuffPerAttack), 0, cappedCumBuffPerAttack[0])
        match self.effect:
            case "Ki":
                state.buff["Ki"] += min(self.effectiveBuff * state.numAttacksEvadedBeforeAttacking, buffToGo)
            case "ATK":
                preAtkBuff = min(self.effectiveBuff * state.numAttacksEvadedBeforeAttacking, buffToGo)
                state.p2Buff["ATK"] += preAtkBuff
                state.p2ATKBuffPostAtttack += min(
                    self.effectiveBuff * (state.numAttacksEvaded - state.numAttacksEvadedBeforeAttacking), buffToGo - preAtkBuff, key=abs
                )
            case "DEF":
                state.defBuffStatuses[("DEF", "Evade")] += cappedBuffPerAttack
            case "Crit":
                state.multiChanceBuff["Crit"].updateChance(
                    "On Super", min(self.effectiveBuff * state.numAttacksEvadedBeforeAttacking, buffToGo), "Crit", state
                )
                state.setNoCritAtkMod()
            case "Evasion":
                state.defBuffStatuses[("Evasion", "Evade")] += cappedBuffPerAttack
            case "Dmg Red":
                state.defBuffStatuses[("DmgRed", "Evade")] += cappedBuffPerAttack
            case _:
                raise Exception(f"{self.effect} Per Attack Evaded Buff Effect not implemented!")
        if not (self.withinTheSameTurn):
            state.form.carryOverBuffs[self.effect].add(cappedTurnBuff)
            self.applied += cappedTurnBuff


class AfterEvent(PassiveAbility):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, effectDuration, threshold=1):
        super().__init__(form, activationProbability, knownApriori, effect, buff)
        self.effectDuration = effectDuration
        self.turnsLeft = effectDuration
        self.threshold = threshold
        self.required = threshold
        self.increment = 0
        self.isNextTurnBuff = False
        self.maxEffectiveBuff = self.effectiveBuff
        if effect in ADDITIONAL_ATTACK_EFFECTS:
            self.applied = [0, 0]
        else:
            self.applied = 0
        self.eventFactor = 1

    def updateBuffToGo(self):
        if self.effect in ADDITIONAL_ATTACK_EFFECTS:
            self.buffToGo = 1.0
        else:
            self.buffToGo = self.maxEffectiveBuff - self.applied

    def resetAppliedBuffs(self, state):
        if self.turnsLeft < RETURN_PERIOD_PER_SLOT[state.slot - 1]:
            if self.effect in ADDITIONAL_ATTACK_EFFECTS:
                state.form.carryOverBuffs["aaPSuper"].sub(self.applied[0])
                state.form.carryOverBuffs["aaPGuarantee"].sub(self.applied[1])
                self.applied = [0, 0]
            else:
                state.form.carryOverBuffs[self.effect].sub(self.applied)
                self.applied = 0
                self.required = self.threshold
            self.turnsLeft = self.effectDuration

    def setTurnBuff(self, state):
        # geometric cdf
        turnBuff = self.effectiveBuff * self.eventFactor
        cappedTurnBuff = min(self.buffToGo, turnBuff, key=abs)
        if self.effect in state.buff.keys():
            state.buff[self.effect] += cappedTurnBuff
        elif self.effect in REGULAR_SUPPORT_EFFECTS:
            state.support += supportFactorConversion[self.effect] * self.supportBuff[state.slot - 1] * self.eventFactor
        else:
            match self.effect:
                case "ATK":
                    state.p2Buff["ATK"] += cappedTurnBuff
                case "DEF":
                    state.p2Buff["DEF"] += cappedTurnBuff
                case "AdditionalSuper":
                    state.aaPSuper.append(cappedTurnBuff)
                    state.aaPGuarantee.append(0)
                case "AAChance":
                    state.aaPGuarantee.append(cappedTurnBuff)
                    state.aaPSuper.append(cappedTurnBuff * self.superChance)
                case "Crit":
                    state.multiChanceBuff["Crit"].updateChance("On Super", cappedTurnBuff, "Crit", state)
                    state.setNoCritAtkMod()
                case "Guard":
                    state.guard += cappedTurnBuff
                case "Dmg Red":
                    state.dmgRedSuperA += cappedTurnBuff
                    state.dmgRedSuperB += cappedTurnBuff
                    state.dmgRedNormalA += cappedTurnBuff
                    state.dmgRedNormalB += cappedTurnBuff
                case "Evasion":
                    state.multiChanceBuff["EvasionA"].updateChance("Start of Turn", cappedTurnBuff, "EvasionA", state)
                    state.multiChanceBuff["EvasionB"].updateChance("Start of Turn", cappedTurnBuff, "EvasionB", state)
                case _:
                    raise Exception(f"{self.effect} After Event Buff Effect not implemented!")

    def nextTurnUpdate(self, state):
        # If abiltiy going to be active next turn
        if (
            not (np.any(self.applied))
            and (self.increment - self.required >= 0)
            and self.effectDuration > RETURN_PERIOD_PER_SLOT[state.slot - 1]
        ):
            if self.effect in ADDITIONAL_ATTACK_EFFECTS:
                state.form.carryOverBuffs["aaPSuper"].add(state.aaPSuper[-1])
                state.form.carryOverBuffs["aaPGuarantee"].add(state.aaPGuarantee[-1])
                self.applied = [state.aaPSuper[-1], state.aaPGuarantee[-1]]
            else:
                nextTurnBuff = min(self.buffToGo, self.effectiveBuff)
                state.form.carryOverBuffs[self.effect].add(nextTurnBuff)
                self.applied += nextTurnBuff


class AfterAttackPerformed(AfterEvent):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args):
        super().__init__(form, activationProbability, knownApriori, effect, buff, args[0], args[1])
        self.requiresSuperAttack = args[2]
        self.slots = literal_eval(str(args[3]))

    def setEventFactor(self):
        if self.required == 0 or (self.required - self.increment <= 0 and self.effect in ["DEF", "Dmg Red", "Guard"]):
            self.eventFactor = 1
        else:
            self.eventFactor = 0

    def applyToState(self, state):
        if state.slot in self.slots:
            self.buffToGo = self.effectiveBuff
            if yesNo2Bool[self.requiresSuperAttack]:
                self.increment = state.superAttacksPerformed
                self.required = max(self.threshold - state.form.superAttacksPerformed, 0)
            else:
                self.increment = state.attacksPerformed
                self.required = max(self.threshold - state.form.attacksPerformed, 0)
            if not (np.any(self.applied)):
                self.setEventFactor()
                self.setTurnBuff(state)
                if self.effect in ADDITIONAL_ATTACK_EFFECTS:
                    # Require this incase AdditionalSuper or AAChance get buffed after they get set in setStates()
                    state.setAttacksPerformed()
            if self.effect not in REGULAR_SUPPORT_EFFECTS:
                self.nextTurnUpdate(state)
            if np.any(self.applied):
                self.turnsLeft -= RETURN_PERIOD_PER_SLOT[state.slot - 1]


class AfterAttackReceived(AfterEvent):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args=[]):
        super().__init__(form, activationProbability, knownApriori, effect, buff, args[0], args[1])
        self.nextAttackingTurn = yesNo2Bool[args[2]]
        self.slots = literal_eval(str(args[3]))
        self.requiresSuperAttack = yesNo2Bool[args[4]]

    def setTurnBuff(self, state):
        # geometric cdf
        turnBuff = self.effectiveBuff * self.eventFactor
        cappedTurnBuff = min(self.buffToGo, turnBuff, key=abs)
        cappedBuffPerAttack = np.insert(
            np.zeros(NUM_ATTACKS_PER_TURN - 1),
            min(round(max(self.required - 1, 0)), NUM_ATTACKS_PER_TURN - 1),
            cappedTurnBuff,
        )
        if self.effect in state.buff.keys():
            state.buff[self.effect] += cappedTurnBuff
        elif self.effect in REGULAR_SUPPORT_EFFECTS:
            state.support += supportFactorConversion[self.effect] * self.supportBuff[state.slot - 1] * self.eventFactor
        else:
            match self.effect:
                case "ATK":
                    state.p2Buff["ATK"] += cappedTurnBuff
                case "DEF":
                    state.defBuffStatuses[("DEF", "Receive")] += cappedBuffPerAttack
                case "AdditionalSuper":
                    state.aaPSuper.append(cappedTurnBuff)
                    state.aaPGuarantee.append(0)
                case "AAChance":
                    state.aaPGuarantee.append(cappedTurnBuff)
                    state.aaPSuper.append(cappedTurnBuff * self.superChance)
                case "Crit":
                    state.multiChanceBuff["Crit"].updateChance("On Super", cappedTurnBuff, "Crit", state)
                    state.setNoCritAtkMod()
                case "Guard":
                    state.defBuffStatuses[("Guard", "Receive")] += cappedBuffPerAttack
                case "Dmg Red":
                    state.defBuffStatuses[("DmgRed", "Receive")] += cappedBuffPerAttack
                case "Evasion":
                    state.defBuffStatuses[("Evasion", "Receive")] += cappedBuffPerAttack
                case "Heal":
                    state.buff["Heal"] += cappedTurnBuff
                case _:
                    raise Exception(f"{self.effect} After Attack Received Buff Effect not implemented!")

    def setEventFactor(self, state):
        # If buff is a defensive one
        if self.effect in ["DEF", "Dmg Red", "Evasion", "Guard", "P2 ATK Support", "P2 DEF Support"]:
            self.eventFactor = 1
        else:
            if self.threshold == 1:
                if (self.requiresSuperAttack):
                    numAttacksReceivedBeforeAttacking = state.numSuperAttacksReceivedBeforeAttacking
                else:
                    numAttacksReceivedBeforeAttacking = state.numAttacksReceivedBeforeAttacking
                self.eventFactor = min(numAttacksReceivedBeforeAttacking, 1)
            else:
                if self.required == 0:
                    self.eventFactor = 1
                else:
                    self.eventFactor = 0

    def applyToState(self, state):
        if state.slot in self.slots:
            self.increment = state.numAttacksReceived
            # Check if ability will be active next turn
            if self.threshold > 1:
                if not (self.isNextTurnBuff) and self.nextAttackingTurn:
                    self.required = 99
                else:
                    self.required = max(self.threshold - state.form.numAttacksReceived, 0)
            if self.nextAttackingTurn:
                if np.any(self.applied) and self.turnsLeft < RETURN_PERIOD_PER_SLOT[state.slot - 1]:
                    self.isNextTurnBuff = False
                    self.resetAppliedBuffs(state)
                else:
                    self.isNextTurnBuff = True
                    self.effectiveBuff = self.maxEffectiveBuff * (1 - poisson.cdf(self.required - 1, self.increment))
            self.updateBuffToGo()
            if np.any(self.applied):
                self.resetAppliedBuffs(state)
            else:
                self.setEventFactor(state)
                if not (self.nextAttackingTurn):
                    self.setTurnBuff(state)
                if self.effect not in REGULAR_SUPPORT_EFFECTS:
                    self.nextTurnUpdate(state)
            if np.any(self.applied):
                self.turnsLeft -= RETURN_PERIOD_PER_SLOT[state.slot - 1]


class AfterGuardActivated(AfterEvent):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args=[]):
        super().__init__(form, activationProbability, knownApriori, effect, buff, args[0], args[1])

    def setTurnBuff(self, state):
        # geometric cdf
        turnBuff = self.effectiveBuff * self.eventFactor
        cappedTurnBuff = min(self.buffToGo, turnBuff, key=abs)
        cappedBuffPerAttack = np.insert(
            np.zeros(NUM_ATTACKS_PER_TURN - 1),
            min(round(max(self.required - 1, 0)), NUM_ATTACKS_PER_TURN - 1),
            cappedTurnBuff,
        )
        if self.effect in state.buff.keys():
            state.buff[self.effect] += cappedTurnBuff
        elif self.effect in REGULAR_SUPPORT_EFFECTS:
            state.support += supportFactorConversion[self.effect] * self.supportBuff[state.slot - 1] * self.eventFactor
        else:
            match self.effect:
                case "ATK":
                    state.p2Buff["ATK"] += cappedTurnBuff
                case "DEF":
                    state.defBuffStatuses[("DEF", "Guard")] += cappedBuffPerAttack
                case "AdditionalSuper":
                    state.aaPSuper.append(cappedTurnBuff)
                    state.aaPGuarantee.append(0)
                case "AAChance":
                    state.aaPGuarantee.append(cappedTurnBuff)
                    state.aaPSuper.append(cappedTurnBuff * self.superChance)
                case "Crit":
                    state.multiChanceBuff["Crit"].updateChance("On Super", cappedTurnBuff, "Crit", state)
                    state.setNoCritAtkMod()
                case "Dmg Red":
                    state.defBuffStatuses[("DmgRed", "Guard")] += cappedBuffPerAttack
                case "Guard":
                    state.defBuffStatuses[("Guard", "Guard")] += cappedBuffPerAttack
                case _:
                    raise Exception(f"{self.effect} After Guard Activated Buff Effect not implemented!")

    def setEventFactor(self, state):
        if state.guard == 0:
            self.eventFactor = 0
        else:
            # If buff is a defensive one
            if self.effect in ["DEF", "Dmg Red", "Guard"]:
                self.eventFactor = 1
            else:
                if self.threshold == 1:
                    self.eventFactor = min(state.numAttacksReceivedBeforeAttacking * state.guard, 1)
                else:
                    if self.required == 0:
                        self.eventFactor = 1
                    else:
                        self.eventFactor = 0

    def applyToState(self, state):
        self.increment = state.numAttacksReceived * state.guard
        self.updateBuffToGo()
        if self.threshold > 1:
            self.required = max(self.threshold - state.form.numAttacksReceived * state.guard, 0)
        if np.any(self.applied):
            self.resetAppliedBuffs(state)
        else:
            self.setEventFactor(state)
            self.setTurnBuff(state)
            if self.effect not in REGULAR_SUPPORT_EFFECTS:
                self.nextTurnUpdate(state)
        if np.any(self.applied):
            self.turnsLeft -= RETURN_PERIOD_PER_SLOT[state.slot - 1]


class AfterAttackEvaded(AfterEvent):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args=[]):
        super().__init__(form, activationProbability, knownApriori, effect, buff, args[0], args[1])
        self.nextAttackingTurn = yesNo2Bool[args[2]]

    def setTurnBuff(self, state):
        # geometric cdf
        turnBuff = self.effectiveBuff * self.eventFactor
        cappedTurnBuff = min(self.buffToGo, turnBuff, key=abs)
        cappedBuffPerAttack = np.insert(
            np.zeros(NUM_ATTACKS_PER_TURN - 1),
            min(round(max(self.required - 1, 0)), NUM_ATTACKS_PER_TURN - 1),
            cappedTurnBuff,
        )
        if self.effect in state.buff.keys():
            state.buff[self.effect] += cappedTurnBuff
        elif self.effect in REGULAR_SUPPORT_EFFECTS:
            state.support += supportFactorConversion[self.effect] * self.supportBuff[state.slot - 1] * self.eventFactor
        else:
            match self.effect:
                case "ATK":
                    state.p2Buff["ATK"] += cappedTurnBuff
                case "DEF":
                    state.defBuffStatuses[("DEF", "Evade")] += cappedBuffPerAttack
                case "AdditionalSuper":
                    state.aaPSuper.append(cappedTurnBuff)
                    state.aaPGuarantee.append(0)
                case "AAChance":
                    state.aaPGuarantee.append(cappedTurnBuff)
                    state.aaPSuper.append(cappedTurnBuff * self.superChance)
                case "Crit":
                    state.multiChanceBuff["Crit"].updateChance("On Super", cappedTurnBuff, "Crit", state)
                    state.setNoCritAtkMod()
                case "Evasion":
                    state.defBuffStatuses[("Evasion", "Evade")] += cappedBuffPerAttack
                case "Dmg Red":
                    state.defBuffStatuses[("DmgRed", "Evade")] += cappedBuffPerAttack
                case _:
                    raise Exception(f"{self.effect} After Attack Evaded Buff Effect not implemented!")

    def setEventFactor(self, state):
        # If buff is a defensive one
        if self.effect in ["DEF", "Dmg Red", "Evasion"]:
            self.eventFactor = 1
        else:
            if self.threshold == 1:
                self.eventFactor = min(state.numAttacksEvadedBeforeAttacking, 1)
            else:
                if self.required == 0:
                    self.eventFactor = 1
                else:
                    self.eventFactor = 0

    def applyToState(self, state):
        self.increment = state.numAttacksEvaded
        if self.threshold > 1:
            if not (self.isNextTurnBuff) and self.nextAttackingTurn:
                self.required = 99
            else:
                self.required = max(self.threshold - state.form.numAttacksEvaded, 0)
        if self.nextAttackingTurn:
            if np.any(self.applied) and self.turnsLeft < RETURN_PERIOD_PER_SLOT[state.slot - 1]:
                self.isNextTurnBuff = False
                self.resetAppliedBuffs(state)
            else:
                self.isNextTurnBuff = True
                if self.effect == "Evasion":
                    # Is working out how much extra evasion chance is to be gained on average by dodding threshold attacks in a turn
                    self.effectiveBuff = (self.maxEffectiveBuff - state.multiChanceBuff["EvasionA"].chances["Start of Turn"]) * (
                        1 - poisson.cdf(self.required - 1, self.increment)
                    )
                else:
                    self.effectiveBuff = self.maxEffectiveBuff * (1 - poisson.cdf(self.required - 1, self.increment))
        self.updateBuffToGo()
        if np.any(self.applied):
            self.resetAppliedBuffs(state)
        else:
            self.setEventFactor(state)
            if not (self.nextAttackingTurn):
                self.setTurnBuff(state)
            if self.effect not in REGULAR_SUPPORT_EFFECTS:
                self.nextTurnUpdate(state)
        if np.any(self.applied):
            self.turnsLeft -= RETURN_PERIOD_PER_SLOT[state.slot - 1]


class AfterAttackReceivedOrEvaded(AfterEvent):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args=[]):
        super().__init__(form, activationProbability, knownApriori, effect, buff, args[0])

    def setTurnBuff(self, state):
        # geometric cdf
        turnBuff = self.effectiveBuff * self.eventFactor
        cappedTurnBuff = min(self.buffToGo, turnBuff, key=abs)
        cappedBuffPerAttack = np.insert(
            np.zeros(NUM_ATTACKS_PER_TURN - 1),
            min(round(max(self.required - 1, 0)), NUM_ATTACKS_PER_TURN - 1),
            cappedTurnBuff,
        )
        if self.effect in state.buff.keys():
            state.buff[self.effect] += cappedTurnBuff
        elif self.effect in REGULAR_SUPPORT_EFFECTS:
            state.support += supportFactorConversion[self.effect] * self.supportBuff[state.slot - 1] * self.eventFactor
        else:
            match self.effect:
                case "ATK":
                    state.p2Buff["ATK"] += cappedTurnBuff
                case "DEF":
                    state.defBuffStatuses[("DEF", "ReceiveOrEvade")] += cappedBuffPerAttack
                case "AdditionalSuper":
                    state.aaPSuper.append(cappedTurnBuff)
                    state.aaPGuarantee.append(0)
                case "AAChance":
                    state.aaPGuarantee.append(cappedTurnBuff)
                    state.aaPSuper.append(cappedTurnBuff * self.superChance)
                case "Crit":
                    state.multiChanceBuff["Crit"].updateChance("On Super", cappedTurnBuff, "Crit", state)
                    state.setNoCritAtkMod()
                case "Guard":
                    state.defBuffStatuses[("Guard", "ReceiveOrEvade")] += cappedBuffPerAttack
                case "Dmg Red":
                    state.defBuffStatuses[("DmgRed", "ReceiveOrEvade")] += cappedBuffPerAttack
                case "Evasion":
                    state.defBuffStatuses[("Evasion", "ReceiveOrEvade")] += cappedBuffPerAttack
                case _:
                    raise Exception(f"{self.effect} After Attack Received Or Evaded Buff Effect not implemented!")

    def setEventFactor(self, state):
        # If buff is a defensive one
        if self.effect in ["DEF", "Dmg Red", "Evasion"]:
            self.eventFactor = 1
        else:
            if self.threshold == 1:
                self.eventFactor = min(state.numAttacksDirectedBeforeAttacking, 1)
            else:
                if self.required == 0:
                    self.eventFactor = 1
                else:
                    self.eventFactor = 0

    def applyToState(self, state):
        self.increment = state.numAttacksDirected
        self.updateBuffToGo()
        if self.threshold > 1:
            raise Exception("Need to implement form.numAttacksDirected")
        if np.any(self.applied):
            self.resetAppliedBuffs(state)
        else:
            self.setEventFactor(state)
            self.setTurnBuff(state)
            if self.effect not in REGULAR_SUPPORT_EFFECTS:
                self.nextTurnUpdate(state)
        if np.any(self.applied):
            self.turnsLeft -= RETURN_PERIOD_PER_SLOT[state.slot - 1]


class UntilEvent(PassiveAbility):
    def __init__(self, form, activationProbability, knownApriori, effect, buff):
        super().__init__(form, activationProbability, knownApriori, effect, buff)
        self.eventFactor = 1


class UntilAttackRecieved(UntilEvent):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args=[]):
        super().__init__(form, activationProbability, knownApriori, effect, buff)

    def applyToState(self, state):
        if self.effect in state.buff.keys():
            state.buff[self.effect] += self.effectiveBuff
        else:
            match self.effect:
                case "DEF":
                    state.p2Buff["DEF"] += self.effectiveBuff
                    state.defBuffStatuses[("DEF", "Receive")][0] -= self.effectiveBuff
                case "Evasion":
                    state.multiChanceBuff["EvasionA"].updateChance(
                        "Start of Turn", self.effectiveBuff, "EvasionA", state
                    )
                    state.multiChanceBuff["EvasionB"].updateChance(
                        "Start of Turn", self.effectiveBuff, "EvasionB", state
                    )
                    state.defBuffStatuses[("Evasion", "Receive")][0] -= self.effectiveBuff
                case "P2 DEF B":
                    state.p2DefB += self.effectiveBuff
                    state.defBuffStatuses[("DEF", "Receive")][0] -= self.effectiveBuff
                case "Guard":
                    state.guard += self.effectiveBuff
                    state.defBuffStatuses[("Guard", "Receive")][0] -= self.effectiveBuff
                case "Dmg Red":
                    state.dmgRedSuperA += self.effectiveBuff
                    state.dmgRedSuperB += self.effectiveBuff
                    state.dmgRedNormalA += self.effectiveBuff
                    state.dmgRedNormalB += self.effectiveBuff
                    state.defBuffStatuses[("DmgRed", "Receive")][0] -= self.effectiveBuff
                case _:
                    raise Exception(f"{self.effect} Until Attack Evaded Buff Effect not implemented!")


class ForFirstTargtedAttack(PassiveAbility):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args=[]):
        super().__init__(form, activationProbability, knownApriori, effect, buff)

    def applyToState(self, state):
        match self.effect:
            case "Evasion":
                state.evadeFirstNormalChance = self.effectiveBuff * (state.numNormalAttacksDirectedBeforeAttacking + state.numNormalAttacksDirectedAfterAttacking) / state.numAttacksDirected
                state.evadeFirstSuperChance = self.effectiveBuff * (state.numSuperAttacksDirectedBeforeAttacking + state.numSuperAttacksDirectedAfterAttacking) / state.numAttacksDirected
                state.multiChanceBuff["EvasionA"].updateAttacksReceivedAndEvaded(state, "EvasionA")
            case _:
                raise Exception(f"{self.effect} Until Attack Evaded Buff Effect not implemented!")

class EveryTimeXEventsInBattle(PassiveAbility):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args):
        super().__init__(form, activationProbability, knownApriori, effect, buff)
        self.threshold, self.max, self.withinTheSameTurn, self.nextAttackingTurn = args
        self.nextAttackingTurn = yesNo2Bool[self.nextAttackingTurn]
        self.required = self.threshold
        self.applied = 0
        self.isNextTurnBuff = False

    def applyBuff(self, state):
        self.required -= self.increment
        if round(self.required) <= 0:
            if not self.isNextTurnBuff and self.nextAttackingTurn:
                self.isNextTurnBuff = True
                return
            self.isNextTurnBuff = False
            buffToGo = self.max - self.applied
            cappedTurnBuff = min(buffToGo, self.effectiveBuff)
            match self.effect:
                case "Ki":
                    state.buff["Ki"] += cappedTurnBuff
                case "ATK":
                    state.p2Buff["ATK"] += cappedTurnBuff
                case "AdditionalSuper":
                    state.aaPSuper.append(cappedTurnBuff)
                    state.aaPGuarantee.append(0)
                case "DEF":
                    state.p2Buff["DEF"] += cappedTurnBuff
                case "Guard":
                    state.guard += cappedTurnBuff
                case "Dmg Red":
                    state.dmgRedSuperA += cappedTurnBuff
                    state.dmgRedSuperB += cappedTurnBuff
                    state.dmgRedNormalA += cappedTurnBuff
                    state.dmgRedNormalB += cappedTurnBuff
                case "Evasion":
                    state.multiChanceBuff["EvasionA"].updateChance("Start of Turn", cappedTurnBuff, "EvasionA", state)
                    state.multiChanceBuff["EvasionB"].updateChance("Start of Turn", cappedTurnBuff, "EvasionB", state)
                case "Heal":
                    state.buff["Heal"] += cappedTurnBuff
                case "Crit":
                    state.multiChanceBuff["Crit"].updateChance("On Super", cappedTurnBuff, "Crit", state)
                    state.setNoCritAtkMod()
                case "Disable Action":
                    state.disableAction()
                case _:
                    raise Exception(f"{self.effect} Every Time X Events in Battle Buff Effect not implemented!")
            if self.effect in ADDITIONAL_ATTACK_EFFECTS:
                # Require this incase AdditionalSiper or AAChance get buffed after they get set in setStates()
                state.setAttacksPerformed()
            self.required = self.threshold
            if not (yesNo2Bool[self.withinTheSameTurn]):
                state.form.carryOverBuffs[self.effect].add(cappedTurnBuff)
                self.applied += cappedTurnBuff


class EveryTimeXAttacksPerformedInBattle(EveryTimeXEventsInBattle):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args):
        super().__init__(form, activationProbability, knownApriori, effect, buff, args[:4])
        self.requiresSuperAttack = args[4]

    def applyToState(self, state):
        if yesNo2Bool[self.requiresSuperAttack]:
            self.increment = state.superAttacksPerformed
        else:
            self.increment = state.attacksPerformed
        self.applyBuff(state)


class EveryTimeXAttacksReceivedInBattle(EveryTimeXEventsInBattle):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args):
        super().__init__(form, activationProbability, knownApriori, effect, buff, args)

    def applyToState(self, state):
        self.increment = state.numAttacksReceived
        self.applyBuff(state)


class EveryTimeXAttacksEvadedInBattle(EveryTimeXEventsInBattle):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args):
        super().__init__(form, activationProbability, knownApriori, effect, buff, args)

    def applyToState(self, state):
        self.increment = state.numAttacksEvaded
        self.applyBuff(state)

class EveryTimeXAttacksReceivedOrEvadedInBattle(EveryTimeXEventsInBattle):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args):
        super().__init__(form, activationProbability, knownApriori, effect, buff, args)

    def applyToState(self, state):
        self.increment = state.numAttacksReceived + state.numAttacksEvaded
        self.applyBuff(state)

class PerformingSuperAttackOffence(PassiveAbility):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args=[]):
        super().__init__(form, activationProbability, knownApriori, effect, buff)
        self.firstAttackOnly = yesNo2Bool[args[0]]

    def applyToState(self, state):
        match self.effect:
            case "ATK":
                if self.firstAttackOnly:
                    state.firstAttackBuff += self.effectiveBuff
                else:
                    state.p2Buff["ATK"] += self.effectiveBuff
            case "Crit":
                if self.firstAttackOnly:
                    state.firstAttackCritBuff += self.effectiveBuff
                else:
                    state.multiChanceBuff["Crit"].updateChance("On Super", self.effectiveBuff, "Crit", state)
                    state.setNoCritAtkMod()
            case _:
                raise Exception(f"{self.effect} Super Attack Offense Buff Effect not implemented!")


class PerformingSuperAttackDefence(PassiveAbility):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args=[]):
        super().__init__(form, activationProbability, knownApriori, effect, buff)

    def applyToState(self, state):
        match self.effect:
            case "DEF":
                # If have activated active skill attack this turn
                if state.superAttacksPerformed > 0:
                    state.p2Buff["DEF"] += self.effectiveBuff
                else:
                    state.p2DefB += self.effectiveBuff
            case "Dmg Red":
                state.dmgRedSuperB += self.effectiveBuff
                state.dmgRedNormalB += self.effectiveBuff
                # If have activated active skill attack this turn
                if state.superAttacksPerformed > 0:
                    state.dmgRedSuperA += self.effectiveBuff
                    state.dmgRedNormalA += self.effectiveBuff
            case "Evasion":
                state.multiChanceBuff["EvasionA"].updateChance("Start of Turn", self.effectiveBuff, "EvasionA", state)
                # If have activated active skill attack this turn
                if state.superAttacksPerformed > 0:
                    state.multiChanceBuff["EvasionB"].updateChance(
                        "Start of Turn", self.effectiveBuff, "EvasionB", state
                    )
            case _:
                raise Exception(f"{self.effect} Super Attack Defence Buff Effect not implemented!")


class KiSphereDependent(PerEvent):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args):
        self.orbType, self.required, self.whenAttacking, self.withinTheSameTurn, max = args
        super().__init__(form, activationProbability, knownApriori, effect, buff, max)

    def applyToState(self, state):
        if self.required == 0:  # If buff per orb
            effectFactor = sum(state.orbCollection.getNumCategoryOrbs(self.orbType))
        else:  # If fixed buff if obtain X orbs
            if state.orbCollection.getNumCategoryOrbs(self.orbType)[0] == 23: # If complete orb change then no uncertainty about meeting requirement
                effectFactor = 1
            else:
                effectFactor = 1 - np.prod(
                    [poisson.cdf(self.required - 1, state.orbCollection.getNumCategoryOrbs(self.orbType))]
                )
        buffToGo = self.max - self.applied
        cappedTurnBuff = min(buffToGo, self.effectiveBuff, key=abs)
        buffFromOrbs = cappedTurnBuff * effectFactor
        if self.effect in REGULAR_SUPPORT_EFFECTS:
            state.support += (
                supportFactorConversion[self.effect] * min(buffToGo, self.supportBuff[state.slot - 1]) * effectFactor
            )
        elif self.effect in state.buff.keys():
            state.buff[self.effect] += buffFromOrbs
        elif self.effect in state.p1Buff.keys():
            state.p1Buff[self.effect] += buffFromOrbs
        elif self.effect in MULTI_CHANCE_EFFECTS_NO_NULLIFY:
            state.multiChanceBuff[self.effect].updateChance("Start of Turn", buffFromOrbs, self.effect, state)
        else:
            match self.effect:
                case "Evasion":
                    state.multiChanceBuff["EvasionA"].updateChance("Start of Turn", buffFromOrbs, "EvasionA", state)
                    state.multiChanceBuff["EvasionB"].updateChance("Start of Turn", buffFromOrbs, "EvasionB", state)
                case "Dmg Red against Normals":
                    state.dmgRedNormalA += buffFromOrbs
                    state.dmgRedNormalB += buffFromOrbs
                case "Dmg Red against Supers":
                    state.dmgRedSuperA += buffFromOrbs
                    state.dmgRedSuperB += buffFromOrbs
                case "Guard":
                    state.guard += buffFromOrbs
                case "Dmg Red":
                    state.dmgRedSuperA += buffFromOrbs
                    state.dmgRedSuperB += buffFromOrbs
                    state.dmgRedNormalA += buffFromOrbs
                    state.dmgRedNormalB += buffFromOrbs
                case "Dmg Red A":
                    state.dmgRedSuperA += buffFromOrbs
                    state.dmgRedNormalA += buffFromOrbs
                case "Dmg Red B":
                    state.dmgRedSuperB += buffFromOrbs
                    state.dmgRedNormalB += buffFromOrbs
                case "AdditionalSuper":
                    state.aaPSuper.append(effectFactor)
                    state.aaPGuarantee.append(0)
                case "AAChance":
                    state.aaPGuarantee.append(effectFactor)
                    state.aaPSuper.append(effectFactor * self.superChance)
                case "P2 ATK":
                    state.p2Buff["ATK"] += buffFromOrbs
                case "P2 DEF B":
                    state.p2DefB += buffFromOrbs
                case "P2 DEF":
                    state.p2Buff["DEF"] += buffFromOrbs
                case _:
                    raise Exception(f"{self.effect} Ki Sphere dependent Buff Effect not implemented!")
        if not (yesNo2Bool[self.withinTheSameTurn]):
            state.form.carryOverBuffs[self.effect].add(buffFromOrbs)
            self.applied += buffFromOrbs


class Nullification(PassiveAbility):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args):
        super().__init__(form, activationProbability, knownApriori, effect, buff)
        self.hasCounter, self.healthFrac, self.p2AttackBuff, self.startTurn, self.endTurn = args

    def applyToState(self, state):
        if state.turn >= self.startTurn and state.turn <= self.endTurn:
            pNullify = self.activationProbability * aprioriProbMod(saFracConversion[self.effect], True)
            state.buff["Heal"] += self.healthFrac * pNullify / NUM_SLOTS * AVG_SA_DAM / AVG_HEALTH
            if yesNo2Bool[self.hasCounter]:
                state.multiChanceBuff["Nullify"].updateChance("SA Counter", pNullify, "Nullify", state)
                state.p2AtkBuffOnCounter += self.p2AttackBuff
            else:
                state.multiChanceBuff["Nullify"].updateChance("Nullification", pNullify, "Nullify", state)


class Condition:
    def __init__(self):
        # Just a default attributes so is always false upon itialisation
        self.formAttr = "numAttacksReceived"
        self.conditionValue = 0

    def isSatisfied(self, form):
        return round(getattr(form, self.formAttr)) >= self.conditionValue


class NextTurnCondition(Condition):
    def __init__(self, turnCondition):
        self.conditionValue = turnCondition
        self.formAttr = "nextTurnRelative"


class TurnCondition(Condition):
    def __init__(self, turnCondition):
        self.conditionValue = turnCondition
        self.formAttr = "turn"


class ProbabilityCondition(Condition):
    def __init__(self, conditionProbability):
        super().__init__()
        self.conditionProbability = conditionProbability
        # Mean of geometric distribution is 1/p
        self.conditionValue = round(1 / self.conditionProbability)
        self.turnCounter = 0

    def isSatisfied(self, form):
        self.turnCounter += 1
        return self.turnCounter >= self.conditionValue


class MaxHpCondition(ProbabilityCondition):
    def __init__(self, maxHpCondition):
        conditionProbability = maxHealthCDF(maxHpCondition)
        super().__init__(conditionProbability)


class MinHpCondition(ProbabilityCondition):
    def __init__(self, minHpCondition):
        conditionProbability = 1 - maxHealthCDF(minHpCondition)
        super().__init__(conditionProbability)


class EnemyMaxHpCondition(ProbabilityCondition):
    def __init__(self, enemyMaxHpCondition):
        conditionProbability = enemyMaxHpCondition
        super().__init__(conditionProbability)


class EnemyMinHpCondition(ProbabilityCondition):
    def __init__(self, enemyMinHpCondition):
        conditionProbability = 1 - enemyMinHpCondition
        super().__init__(conditionProbability)


class FinalBlowCondition(ProbabilityCondition):
    def __init__(self):
        conditionProbability = PROBABILITY_KILL_ENEMY_PER_TURN / NUM_SLOTS
        super().__init__(conditionProbability)


class AttacksPerformedCondition(Condition):
    def __init__(self, numAttacks):
        self.formAttr = "attacksPerformed"
        self.conditionValue = numAttacks


class SupersPerformedCondition(Condition):
    def __init__(self, numSupers):
        self.formAttr = "superAttacksPerformed"
        self.conditionValue = numSupers


class AttacksReceivedCondition(Condition):
    def __init__(self, numAttacks):
        self.formAttr = "numAttacksReceived"
        self.conditionValue = numAttacks


class AttacksEvadedCondition(Condition):
    def __init__(self, numAttacks):
        self.formAttr = "numAttacksEvaded"
        self.conditionValue = numAttacks


class FinishSkillActivatedCondition(Condition):
    def __init__(self, requiredCharge):
        self.formAttr = "charge"
        self.conditionValue = requiredCharge


class ReviveCondition(Condition):
    def __init__(self):
        self.formAttr = "revived"
        self.conditionValue = True


class ChanceEXSuperCondition:
    def __init__(self, chance):
        self.chance = chance

    def chanceSatisfied(self, args):
        return self.chance
        
        
class CritEXSuperCondition:
    def chanceSatisfied(self, args):
        critProb = args[0]
        assert 0 <= critProb <= 1, "Crit chance should be between 0 and 1"
        return critProb


class NumAttacksPerformedEXSuperCondition:
    def __init__(self, numAttacksPerformedCondition):
        self.numAttacksPerformedCondition = numAttacksPerformedCondition
        assert self.numAttacksPerformedCondition < 2, "Multiple attacks performed condition has not been implemented!"
    
    def chanceSatisfied(self, args):
        numAttacksPerformed = args[1]
        return 1 if numAttacksPerformed == self.numAttacksPerformedCondition else 0


class KiEXSuperCondition:
    def __init__(self, kiCondition):
        self.kiCondition = kiCondition
    
    def chanceSatisfied(self, args):
        constantKi, randomKi = args[2], args[3]
        return 1 - ZTP_CDF(max(self.kiCondition - 1 - constantKi, 0), randomKi)

class CompositeCondition:
    def __init__(self, operator, conditions):
        self.operator = operator
        self.conditions = conditions
        if self.operator == "AFTER":
            self.conditions[0].conditionValue += self.conditions[1].conditionValue - 1

    def isSatisfied(self, form):
        match self.operator:
            case "AND":
                return np.all([condition.isSatisfied(form) for condition in self.conditions])
            case "OR":
                return np.any([condition.isSatisfied(form) for condition in self.conditions])
            case "AFTER":
                return self.conditions[0].isSatisfied(form)
            case _:
                raise Exception(f"{self.operator} Composite Condition Operator not implemented!")
    
    def chanceSatisfied(self, args):
        match self.operator:
            case "AND":
                return np.prod([condition.chanceSatisfied(args) for condition in self.conditions])
            case "OR":
                return 1 - np.prod([1 - condition.chanceSatisfied(args) for condition in self.conditions])
            case "AFTER":
                return self.conditions[0].chanceSatisfied(args)
            case _:
                raise Exception(f"{self.operator} Composite Condition Operator not implemented!")


if __name__ == "__main__":
    unit = Unit(455, "F2P_AGL_Tamagami_1", 5, "ATK", "ADD", "CRT", [3, 1, 3, 3, 3, 3, 3, 3, 3, 3], "True")
