import datetime as dt
from dokkanUnitHelperFunctions import *
import xml.etree.ElementTree as ET

# TODO:
# - Try factor out some code within ability class into class functions
# - Add multi-processing
# - Make it ask if links have changed for a new form.
# - Change question from last turn buff ends on to duration as more explicit
# - Also might want to include attack all in atk calcs.
# - If ever do DPT, instead of APT, should use Lowers DEF in calcs. But most enemies are immunue to it anyway, so not a big deal.
# - Add some functionality that can update existing input .txt files with new questions (assuming not relevant to exisiting unit)
# - It would be awesome if after I have read in a unit I could reconstruct the passive description to compare it against the game
# - Instead of asking user how many of something, should ask until they enteran exit key ak a while loop instead of for loop
# - Should read up on python optimisation techniques once is running and se how long it takes. But try be efficient you go.
# - Should put at may not be relevant tag onto end of the prompts that may not always be relevant.
# - Ideally would just pull data from database, but not up in time for new units. Would be amazing for old units though.
# - Leader skill weight should decrease from 5 as new structure adds more variability between leader skills
# - Once calculate how many supers do on turn 1, use this in the SBR calculation for debuffs on super(). i.e. SBR should be one of the last things to be calculated

##################################################### Helper Functions ############################################################################


def abilityQuestionaire(form, abilityPrompt, abilityClass, parameterPrompts=[], types=[], defaults=[]):
    numAbilities = form.inputHelper.getAndSaveUserInput(abilityPrompt, default=0)
    abilities = []
    abilityTypeElement = form.inputHelper.parent
    for i in range(numAbilities):
        form.inputHelper.parent = form.inputHelper.getChildElement(abilityTypeElement, f"ability_{i + 1}")
        parameters = []
        for j, parameterPrompt in enumerate(parameterPrompts):
            if len(types) == 0:  # If don't care about prompt choices
                parameters.append(form.inputHelper.getAndSaveUserInput(parameterPrompt))
            else:
                parameters.append(
                    form.inputHelper.getAndSaveUserInput(parameterPrompt, type=types[j], default=defaults[j])
                )
        if issubclass(abilityClass, PassiveAbility):
            effect = form.inputHelper.getAndSaveUserInput(
                "What type of buff does the unit get?", type=clc.Choice(EFFECTS, case_sensitive=False), default="ATK"
            )
            activationProbability = form.inputHelper.getAndSaveUserInput(
                "What is the probability this ability activates?", default=1.0
            )
            # If the status of this ability is known beforehand, scale it to account for this fact.
            if activationProbability != 1:
                knownApriori = yesNo2Bool[
                    form.inputHelper.getAndSaveUserInput(
                        "Is the status of this ability known beforehand?",
                        type=clc.Choice(YES_NO, case_sensitive=False),
                        default="N",
                    )
                ]
            else:
                knownApriori = False
            buff = form.inputHelper.getAndSaveUserInput("What is the value of the buff?", default=1.0)
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
                turnCondition = inputHelper.getAndSaveUserInput(
                    "What is the ability turn condition (relative to the form's starting turn)?", default=5
                )
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
            case "Enemy Max HP":
                enemyMaxHpCondition = inputHelper.getAndSaveUserInput(
                    "What is the maximum enemy HP condition?", default=0.5
                )
                condition[i] = EnemyMaxHpCondition(enemyMaxHpCondition)
            case "Enemy Min HP":
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
            case "Finish Skill Activation":
                requiredCharge = inputHelper.getAndSaveUserInput("What is the required charge condition?", default=30)
                condition[i] = FinishSkillActivatedCondition(requiredCharge)
            case "Deliver Final Blow":
                condition[i] = FinalBlowCondition()
            case "Revive":
                condition[i] = ReviveCondition()
            case "NA":
                condition[i] = Condition()
    if numConditions == 2:
        return CompositeCondition(operator, condition)
    else:
        return condition[0]


# Overwrite this class function as has additional
def updateAttacksReceivedAndEvaded(self, state):
    pEvade = self.prob * (1 - DODGE_CANCEL_FACTOR)
    state.numAttacksReceived = NUM_ATTACKS_DIRECTED[state.slot - 1] * (1 - pEvade)
    state.numAttacksReceivedBeforeAttacking = NUM_ATTACKS_DIRECTED_BEFORE_ATTACKING[state.slot - 1] * (1 - pEvade)
    state.numAttacksEvaded = NUM_ATTACKS_DIRECTED[state.slot - 1] * pEvade
    state.numAttacksEvadedBeforeAttacking = NUM_ATTACKS_DIRECTED_BEFORE_ATTACKING[state.slot - 1] * pEvade


MultiChanceBuff.updateAttacksReceivedAndEvaded = updateAttacksReceivedAndEvaded


######################################################### Classes #################################################################


class InputHelper:
    def __init__(self, id, commonName):
        self.filePath = os.path.join(CWD, "DokkanKits", commonName + "_" + id + ".xml")
        if os.path.exists(self.filePath):
            self.tree = ET.parse(self.filePath)
            self.parent = self.tree.getroot()
        else:
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
    def __init__(self, id, commonName, nCopies, brz, HiPo1, HiPo2, slots, save=True):
        self.id = str(id)
        self.commonName = commonName
        self.nCopies = nCopies
        self.brz = brz
        self.HiPo1 = HiPo1
        self.HiPo2 = HiPo2
        self.save = save
        self.inputHelper = InputHelper(self.id, commonName)
        self.slots = slots
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
        self.jp_date = dt.datetime.strptime(
            self.inputHelper.getAndSaveUserInput(
                "When did the unit release on the Japanse version of Dokkan? (MM/YY)", default="01/24"
            ),
            "%m/%y",
        )
        self.gbl_date = dt.datetime.strptime(
            self.inputHelper.getAndSaveUserInput(
                "When did the unit release on the Global version of Dokkan? (MM/YY)", default="01/24"
            ),
            "%m/%y",
        )
        self.HP = self.inputHelper.getAndSaveUserInput("What is the unit's Max Level HP stat?", default=0)
        self.ATK = self.inputHelper.getAndSaveUserInput("What is the unit's Max Level ATK stat?", default=0)
        self.DEF = self.inputHelper.getAndSaveUserInput("What is the unit's Max Level DEF stat?", default=0)
        self.leaderSkill = leaderSkillConversion[
            self.inputHelper.getAndSaveUserInput(
                "How would you rate the unit's leader skill on a scale of 1-10? 200% limited - e.g. LR Hatchiyak Goku 200% small - e.g. LR Metal Cooler 200% medium - e.g. PHY God Goku 200% large - e.g. LR Vegeta and Trunks",
                type=clc.Choice(leaderSkillConversion.keys(), case_sensitive=False),
                default="<150%",
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
            default=0,
        )

    def getHiPo(self):
        HiPoStats = hiddenPotentalStatsConverter[self._type][:, self.nCopies - 1]
        HiPoAbilities = np.array(HIPO_D0[self._type]) + HIPO_BRZ[self.brz] + HIPO_SLV[self.HiPo1]
        if self.nCopies > 1:
            HiPoAbilities += HIPO_D1[(self.HiPo1, self.HiPo2)]
        if self.nCopies > 2:
            HiPoAbilities += np.array(HIPO_D2[(self.HiPo1, self.HiPo2)]) + HIPO_GLD[(self.HiPo1, self.HiPo2)]
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
        self.stacks = dict(zip(STACK_EFFECTS, [[], []]))  # Dict mapping STACK_EFFECTS to list of Stack objects
        self.inputHelper.parent = self.inputHelper.getChildElement(self.inputHelper.tree.getroot(), "forms")
        self.formsElement = self.inputHelper.parent
        self.numForms = self.inputHelper.getAndSaveUserInput("How many forms does the unit have?", default=1)
        turn = 1
        formIdx = 0
        stateIdx = -1
        self.transformationTriggered = False
        self.fightPeak = False
        # Only non-zero in between activating the stanby finish skill attack and applying to subsequent state
        self.transformationAttackAPT = 0
        self.nextForm = 1
        applyTransformationAttackAPT = False
        self.critMultiplier = (CRIT_MULTIPLIER + self.TAB * CRIT_TAB_INC) * BYPASS_DEFENSE_FACTOR
        while turn <= MAX_TURN:
            stateIdx += 1
            slot = self.slots[stateIdx]
            formIdx += self.nextForm
            if self.nextForm == 1:
                # Ignore case where turn == 1 as this is when nextForm == True doesn't mean transformation
                if turn != 1:
                    form.transformed = True
                self.inputHelper.parent = self.inputHelper.getChildElement(self.formsElement, f"form_{formIdx}")
                form = Form(self.inputHelper, turn, self.rarity, self.EZA, formIdx, self.numForms, self.giantRageDuration)
                self.forms.append(form)
            elif self.nextForm == -1:
                form = self.forms[-2]
            self.nextForm = 0
            form.turn = turn
            nextTurn = turn + RETURN_PERIOD_PER_SLOT[slot - 1]
            form.nextTurnRelative = nextTurn - form.initialTurn + 1
            if abs(PEAK_TURN - turn) < abs(nextTurn - PEAK_TURN) and not (self.fightPeak):
                self.fightPeak = True
            state = State(self, form, slot, turn)
            state.setState(self, form)
            # If have finished a standby
            if self.transformationTriggered:
                # If the trigger condition for the finish is a revive, apply APT this turn, otherwise next.
                try:
                    hasReviveCounter = form.abilities["Attack Enemy"][-1].finishSkillChargeCondition == "Revive"
                except:
                    hasReviveCounter = False
                if hasReviveCounter:
                    applyTransformationAttackAPT = True
                    self.nextForm = -1
                if applyTransformationAttackAPT:
                    state.attributes["APT"] += self.transformationAttackAPT
                    turn = nextTurn
                    self.transformationAttackAPT = 0
                    state.attacksPerformed += 1
                    state.superAttacksPerformed += 1
                    self.states.append(state)
                else:  # Set this to True so apply APT in next state (e.g. Buu Bois)
                    applyTransformationAttackAPT = True
                    stateIdx -= 1
            else:
                form.numAttacksReceived += state.numAttacksReceived
                form.numAttacksEvaded += state.numAttacksEvaded
                self.nextForm = form.checkCondition(
                    form.formChangeCondition,
                    form.transformed,
                    form.newForm,
                )
                self.states.append(state)
                turn = nextTurn

    def getAttributes(self):
        attributes = [None] * len(self.states)
        for i, state in enumerate(self.states):
            attributes[i] = list(state.attributes.values())
        return np.array(attributes)

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
        attributes = self.getAttributes()
        interpAttrs = np.array([np.interp(EVAL_TURNS, stateTurns, attributes[:, i]) for i in range(NUM_ATTRIBUTES)]).T
        self.setAttributes(interpAttrs)

    def saveUnit(self):
        if self.save:
            # Output the unit's attributes to a .txt file
            outputFilePath = os.path.join(
                CWD, "DokkanKitOutputs", HIPO_DUPES[self.nCopies - 1], self.commonName + "_" + self.id + ".txt"
            )
            outputFile = open(outputFilePath, "w")
            for i, state in enumerate(self.states):
                outputFile.write(f"State # {i} / Turn # {state.turn} \n \n")
                for j, attributeName in enumerate(ATTTRIBUTE_NAMES):
                    outputFile.write(f"{attributeName}: {state.attributes[attributeName]} \n")
                outputFile.write("\n")


class Form:
    def __init__(self, inputHelper, initialTurn, rarity, eza, formIdx, numForms, giantRageDuration=0, giantRageMode=False):
        self.formElement = inputHelper.parent
        self.inputHelper = inputHelper
        self.initialTurn = initialTurn
        self.rarity = rarity
        self.EZA = eza
        self.formIdx = formIdx
        self.giantRageDuration = giantRageDuration
        self.giantRageMode = giantRageMode
        self.linkNames = [""] * MAX_NUM_LINKS
        self.linkCommonality = 0
        self.carryOverBuffs = dict(zip(EXTRA_BUFF_EFFECTS, [CarryOverBuff(effect) for effect in EXTRA_BUFF_EFFECTS]))
        self.linkEffects = dict(zip(LINK_EFFECT_NAMES, np.zeros(len(LINK_EFFECT_NAMES))))
        self.numAttacksReceived = 0  # Number of attacks received so far in this form.
        self.numAttacksEvaded = 0
        self.attacksPerformed = 0
        self.superAttacksPerformed = 0
        self.charge = 0
        self.superAttacks = {}  # Will be a list of SuperAttack objects
        # This will be a list of Ability objects which will be iterated through each state to call applyToState.
        self.abilities = dict(zip(PHASES, [[] for i in range(len(PHASES))]))
        self.transformed = False
        self.newForm = True
        self.intentional12Ki = False
        self.revived = False
        self.canAttack = yesNo2Bool[self.inputHelper.getAndSaveUserInput("Can this form attack?", default="Y")]
        if self.rarity == "LR":
            self.intentional12Ki = yesNo2Bool[
                self.inputHelper.getAndSaveUserInput("Should a 12 Ki be targetted for this form?", default="N")
            ]
        self.normalCounterMult = counterAttackConversion[
            self.inputHelper.getAndSaveUserInput(
                "What is the unit's normal counter multiplier?",
                type=clc.Choice(counterAttackConversion.keys(), case_sensitive=False),
                default="NA",
            )
        ]
        self.saCounterMult = counterAttackConversion[
            self.inputHelper.getAndSaveUserInput(
                "What is the unit's super attack counter multiplier?",
                type=clc.Choice(counterAttackConversion.keys(), case_sensitive=False),
                default="NA",
            )
        ]
        self.getLinks()
        #assert len(np.unique(self.linkNames)) == MAX_NUM_LINKS , "Duplicate links"
        self.getSuperAttacks(self.rarity, self.EZA)
        ################################################ Turn Start #####################################################
        self.inputHelper.parent = self.inputHelper.getChildElement(self.formElement, "default")
        self.abilities["Start of Turn"].extend(
            abilityQuestionaire(
                self,
                "How many unconditional buffs does the form have?",
                Buff,
            )
        )
        self.inputHelper.parent = self.inputHelper.getChildElement(self.formElement, "turn_dpendent")
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
        self.inputHelper.parent = self.inputHelper.getChildElement(self.formElement, "slot_dependent")
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
        self.inputHelper.parent = self.inputHelper.getChildElement(self.formElement, "health_dependent")
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
        self.inputHelper.parent = self.inputHelper.getChildElement(self.formElement, "health_scale")
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
        self.inputHelper.parent = self.inputHelper.getChildElement(self.formElement, "per_turn")
        self.abilities["Start of Turn"].extend(
            abilityQuestionaire(
                self,
                "How many different buffs does the form get per turn?",
                PerTurn,
                ["What is the maximum buff?"],
                [None],
                [1.0],
            )
        )
        self.inputHelper.parent = self.inputHelper.getChildElement(self.formElement, "attacks_received_threshold")
        self.abilities["Start of Turn"].extend(
            abilityQuestionaire(
                self,
                "How many different buffs does the form get after multiple attacks received?",
                AttackReceivedThreshold,
                ["How many attacks need to be received?"],
                [None],
                [5],
            )
        )
        self.inputHelper.parent = self.inputHelper.getChildElement(self.formElement, "attacks_performed_threshold")
        self.abilities["Start of Turn"].extend(
            abilityQuestionaire(
                self,
                "How many different buffs does the form get after multiple attacks performed?",
                AttackPerformedThreshold,
                ["How many attacks need to be performed?", "Requires super attack?"],
                [None, clc.Choice(YES_NO)],
                [5, "Y"],
            )
        )
        self.inputHelper.parent = self.inputHelper.getChildElement(self.formElement, "domain")
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
        self.inputHelper.parent = self.inputHelper.getChildElement(self.formElement, "active_skill_buffs")
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
        self.inputHelper.parent = self.inputHelper.getChildElement(self.formElement, "offensive_on_super")
        self.abilities["Active / Finish Attacks"].extend(
            abilityQuestionaire(
                self,
                "How many different offensive buffs does the form get when performing a super attack / attacking?",
                PerformingSuperAttackOffence,
            )
        )
        if self.giantRageDuration > 0:
            self.inputHelper.parent = self.inputHelper.getChildElement(self.formElement, "giant_rage_mode")
            giantRageModeATK = self.inputHelper.getAndSaveUserInput("What is the giant/rage mode attack stat?", default=60000)
            self.abilities["Active / Finish Attacks"].append(GiantRageMode(self, [giantRageModeATK]))
        self.inputHelper.parent = self.inputHelper.getChildElement(self.formElement, "active_skill_attack")
        self.abilities["Active / Finish Attacks"].extend(
            abilityQuestionaire(
                self,
                "How many active skill attacks does the form have?",
                ActiveSkillAttack,
                [
                    "What is the attack multiplier?",
                    "What is the additional attack buff when performing the attack?",
                    "Does this active skill trigger a transformation?",
                ],
                [clc.Choice(SPECIAL_ATTACK_MULTIPLIER_NAMES, case_sensitive=False), None, clc.Choice(YES_NO)],
                ["Ultimate", 0.0, "N"],
            )
        )
        self.inputHelper.parent = self.inputHelper.getChildElement(self.formElement, "standby_finish_attack")
        self.abilities["Active / Finish Attacks"].extend(
            abilityQuestionaire(
                self,
                "How many Non-Revival Counterattack Standby Finish Skills does the form have?",
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
        self.inputHelper.parent = self.inputHelper.getChildElement(self.formElement, "defensive_on_super")
        self.abilities["Active / Finish Attacks"].extend(
            abilityQuestionaire(
                self,
                "How many different defensive buffs does the form get when performing a super attack / attacking?",
                PerformingSuperAttackDefence,
            )
        )
        ############################################## Collect Ki ##################################################
        self.inputHelper.parent = self.inputHelper.getChildElement(self.formElement, "ki_sphere_dependent")
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
                    "What is the maximum buff?"
                ],
                [clc.Choice(ORB_REQUIREMENTS), None, clc.Choice(YES_NO), clc.Choice(YES_NO), None],
                ["Any", 0, "N", "Y", 99.0],
            )
        )
        self.inputHelper.parent = self.inputHelper.getChildElement(self.formElement, "ki_dependent")
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
        ############################################## Receive Attacks ##################################################
        self.inputHelper.parent = self.inputHelper.getChildElement(self.formElement, "after_receive_attack")
        self.abilities["Receive Attacks"].extend(
            abilityQuestionaire(
                self,
                "How many different buffs does the form get after receiving an attack?",
                AfterAttackReceived,
                ["How many turns does the buff last?"],
                [None],
                [1],
            )
        )
        self.inputHelper.parent = self.inputHelper.getChildElement(self.formElement, "after_guard_attack")
        self.abilities["Receive Attacks"].extend(
            abilityQuestionaire(
                self,
                "How many different buffs does the form get after guarding an attack?",
                AfterGuardActivated,
                ["How many turns does the buff last?"],
                [None],
                [1],
            )
        )
        self.inputHelper.parent = self.inputHelper.getChildElement(self.formElement, "after_evade_attack")
        self.abilities["Receive Attacks"].extend(
            abilityQuestionaire(
                self,
                "How many different buffs does the form get after evading attacks?",
                AfterAttackEvaded,
                ["How many turns does the buff last?", "How many evasions are required?", "Does the buff start from the next attacking turn?"],
                [None, None, clc.Choice(YES_NO)],
                [1, 1, "N"],
            )
        )
        self.inputHelper.parent = self.inputHelper.getChildElement(self.formElement, "per_attack_received")
        self.abilities["Receive Attacks"].extend(
            abilityQuestionaire(
                self,
                "How many different buffs does the form get on attacks received?",
                PerAttackReceived,
                ["What is the maximum buff?"],
                [None],
                [1.0],
            )
        )
        self.inputHelper.parent = self.inputHelper.getChildElement(self.formElement, "per_attack_guarded")
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
        self.inputHelper.parent = self.inputHelper.getChildElement(self.formElement, "per_attack_evaded")
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
        ############################################## Attack Enemy ##################################################
        self.inputHelper.parent = self.inputHelper.getChildElement(self.formElement, "per_attack_super_performed")
        self.abilities["Attack Enemy"].extend(
            abilityQuestionaire(
                self,
                "How many different buffs does the form get per attack / super performed?",
                PerAttackPerformed,
                ["What is the maximum buff?", "Requires super attack?", "Within the same turn?"],
                [None, clc.Choice(YES_NO, case_sensitive=False), clc.Choice(YES_NO, case_sensitive=False)],
                [1.0, "N", "N"],
            )
        )
        self.inputHelper.parent = self.inputHelper.getChildElement(self.formElement, "nullification")
        self.abilities["Receive Attacks"].extend(
            abilityQuestionaire(
                self,
                "How many different nullification abilities does the form have?",
                Nullification,
                ["Does this nullification have counter?", "How much health is restored if nullified?"],
                [clc.Choice(YES_NO), None],
                ["N", 0.0],
            )
        )
        self.inputHelper.parent = self.inputHelper.getChildElement(self.formElement, "revive")
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
        self.inputHelper.parent = self.inputHelper.getChildElement(self.formElement, "revival_counter")
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
        ################################################ Turn End #####################################################
        self.inputHelper.parent = self.inputHelper.getChildElement(self.formElement, f"form_{self.formIdx}_change_condition")
        self.formChangeCondition = getCondition(self.inputHelper)
        if self.formIdx < numForms:
            self.newForm = True
        else:
            self.newForm = False

    def getLinks(self):
        linksElement = self.inputHelper.getChildElement(self.inputHelper.parent, "links")
        for linkIndex in range(MAX_NUM_LINKS):
            self.inputHelper.parent = self.inputHelper.getChildElement(linksElement, f"link_{linkIndex + 1}")
            self.linkNames[linkIndex] = self.inputHelper.getAndSaveUserInput(
                f"What is the form's link # {linkIndex+1}",
                type=clc.Choice(LINKS, case_sensitive=False),
                default="Fierce Battle",
            )
            linkCommonality = self.inputHelper.getAndSaveUserInput(
                "If has an ideal linking partner, what is the chance this link is active?",
                default=-1,
            )
            link = Link(self.linkNames[linkIndex], linkCommonality)
            for linkEffectName in LINK_EFFECT_NAMES:
                self.linkEffects[linkEffectName] += link.effects[linkEffectName]
        self.linkEffects["Commonality"] /= MAX_NUM_LINKS
        self.inputHelper.parent = self.formElement

    def getSuperAttacks(self, rarity, eza):
        superAttacksElement = self.inputHelper.getChildElement(self.inputHelper.parent, "super_attack")
        for superAttackType in SUPER_ATTACK_CATEGORIES:
            self.inputHelper.parent = self.inputHelper.getChildElement(
                superAttacksElement, f"{superAttackNameConversion[superAttackType]}"
            )
            if superAttackType == "12 Ki" or (rarity == "LR" and not (self.intentional12Ki)):
                multiplier = superAttackConversion[
                    self.inputHelper.getAndSaveUserInput(
                        f"What is the form's {superAttackType} super attack multiplier?",
                        type=clc.Choice(SUPER_ATTACK_MULTIPLIER_NAMES, case_sensitive=False),
                        default=DEFAULT_SUPER_ATTACK_MULTIPLIER_NAMES[superAttackType],
                    )
                ][superAttackLevelConversion[rarity][eza]]
                avgSuperAttack = SuperAttack(superAttackType, multiplier)
                defaultSuperAttack = copy.deepcopy(avgSuperAttack)
                numSuperAttacks = self.inputHelper.getAndSaveUserInput(
                    f"How many different {superAttackType} super attacks does this form have?",
                    default=1,
                )
                superFracTotal = 0
                superAttackVariationsElement = self.inputHelper.getChildElement(
                    self.inputHelper.parent, f"{superAttackNameConversion[superAttackType]}_variations"
                )
                for i in range(numSuperAttacks):
                    self.inputHelper.parent = self.inputHelper.getChildElement(
                        superAttackVariationsElement, f"{superAttackNameConversion[superAttackType]}_variation_{i + 1}"
                    )
                    if numSuperAttacks > 1:
                        superFrac = self.inputHelper.getAndSaveUserInput(
                            f"What is the probability of this {superAttackType} super attack variant from occuring?",
                            default=1.0,
                        )
                    else:
                        superFrac = 1
                    numEffects = self.inputHelper.getAndSaveUserInput(
                        f"How many effects does this form's {superAttackType} super attack have?",
                        default=1,
                    )
                    superAttackEffectsElement = self.inputHelper.getChildElement(
                        self.inputHelper.parent,
                        f"{superAttackNameConversion[superAttackType]}_variation_{i + 1}_effects",
                    )
                    for j in range(numEffects):
                        self.inputHelper.parent = self.inputHelper.getChildElement(
                            superAttackEffectsElement,
                            f"{superAttackNameConversion[superAttackType]}_variation_{i + 1}_effect_{j + 1}",
                        )
                        effectType = self.inputHelper.getAndSaveUserInput(
                            "What type of effect does the unit get on super?",
                            type=clc.Choice(SUPER_ATTACK_EFFECTS, case_sensitive=False),
                            default="ATK",
                        )
                        activationProbability = self.inputHelper.getAndSaveUserInput(
                            "What is the probability this effect activates when supering?",
                            default=1.0,
                        )
                        buff = self.inputHelper.getAndSaveUserInput("What is the value of the buff?", default=0.0)
                        duration = self.inputHelper.getAndSaveUserInput(
                            "How many turns does it last for?", default=99
                        )
                        avgSuperAttack.addEffect(effectType, activationProbability, buff, duration, superFrac)
                        if i == 0:
                            defaultSuperAttack.addEffect(effectType, activationProbability, buff, duration, 1)
                    superFracTotal += superFrac
                    self.inputHelper.parent = superAttackVariationsElement
                assert superFracTotal == 1, "Invald super attack variant probabilities entered"
                self.inputHelper.parent = superAttacksElement
            self.superAttacks[superAttackType] = avgSuperAttack
            if superAttackType == "12 Ki":
                self.superAttacks["AS"] = defaultSuperAttack
        self.inputHelper.parent = self.formElement

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
                        orbChangeConversion["Type Orb Change"]["Same"]
                        + orbChangeConversion["Type Orb Change"]["Rainbow"]
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
                    self.attacksPerformed
                    + (NUM_SLOTS - 1)
                    - PROBABILITY_KILL_ENEMY_BEFORE_ATTACKING[1]
                    - PROBABILITY_KILL_ENEMY_BEFORE_ATTACKING[2]
                    + (NUM_ATTACKS_PERFORMED_PER_UNIT_PER_TURN - 1)
                    * (
                        (NUM_SLOTS - 1)
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
        if self.value != []:
            if self.effect in ADDITIONAL_ATTACK_PARAMETERS:
                self.value.remove(value)
            else:
                self.value -= value


class Link:
    def __init__(self, name, commonality):
        self.name = name
        i = LINK_NAMES.index(self.name) + 1
        self.effects = {}
        for j in range(len(LINK_EFFECT_NAMES) - 1):
            self.effects[LINK_EFFECT_NAMES[j]] = float(LINK_DATA[i, 10 + j])
        if commonality == -1:
            self.effects[LINK_EFFECT_NAMES[-1]] = float(LINK_DATA[i, 9])
        else:
            self.effects[LINK_EFFECT_NAMES[-1]] = float(commonality)


class SuperAttack:
    def __init__(self, superAttackType, multiplier):
        self.superAttackType = superAttackType
        self.multiplier = multiplier
        self.effects = dict(
            zip(SUPER_ATTACK_EFFECTS, [SuperAttackEffectParams() for i in range(len(SUPER_ATTACK_EFFECTS))])
        )

    def addEffect(self, effectType, activationProbability, buff, duration, superFrac):
        self.effects[effectType].updateParams(activationProbability, buff, duration, superFrac)


class SuperAttackEffectParams:
    def __init__(self):
        self.buff = 0
        self.duration = 0

    def updateParams(self, activationProbability, buff, duration, superFrac):
        # superFrac accounts for unit supers
        self.buff += activationProbability * buff * superFrac
        self.duration += duration * superFrac


class State:
    def __init__(self, unit, form, slot, turn):
        self.slot = slot  # Slot no.
        self.turn = turn
        # Dictionary for variables which have a 1-1 relationship with Buff EFFECTS
        self.buff = {
            "Ki": LEADER_SKILL_KI + form.carryOverBuffs["Ki"].get(),
            "AEAAT": 0,
            "Guard": 0,
            "Disable Guard": 0,
            "Dmg Red against Normals": form.carryOverBuffs["Dmg Red"].get(),
            "Heal": 0,
            "Attacks Guaranteed to Hit": 0
        }
        self.p1Buff = {}
        self.p2Buff = {}
        self.p3Buff = {}
        for effect in STACK_EFFECTS:
            if form.giantRageMode:
                self.p1Buff[effect] = 0
            else:
                self.p1Buff[effect] = ATK_DEF_SUPPORT
            self.p2Buff[effect] = form.carryOverBuffs[effect].get()
            self.p3Buff[effect] = 0
        self.p2Buff["ATK"] += form.linkEffects["On Super ATK"]
        self.multiChanceBuff = {}
        for effect in MULTI_CHANCE_EFFECTS:
            self.multiChanceBuff[effect] = MultiChanceBuff(effect)
            if effect in MULTI_CHANCE_EFFECTS_NO_NULLIFY:
                inputEffect = "Evasion" if "Evasion" in effect else effect
                self.multiChanceBuff[effect].updateChance("HiPo", unit.pHiPo[inputEffect], effect, self)
                self.multiChanceBuff[effect].updateChance("Links", form.linkEffects[inputEffect], effect, self)
                self.multiChanceBuff[effect].updateChance("On Super", form.carryOverBuffs[inputEffect].get(), effect, self)
        self.aaPSuper = form.carryOverBuffs["aaPSuper"].get()
        self.aaPGuarantee = form.carryOverBuffs["aaPGuarantee"].get()
        self.kiPerOtherTypeOrb = 1
        self.kiPerSameTypeOrb = KI_PER_SAME_TYPE_ORB
        self.kiPerRainbowKiSphere = 1  # Ki per orb
        self.numRainbowOrbs = orbChangeConversion["No Orb Change"]["Rainbow"]
        self.numOtherTypeOrbs = orbChangeConversion["No Orb Change"]["Other"]
        self.numSameTypeOrbs = orbChangeConversion["No Orb Change"]["Same"]
        self.p2DefB = 0
        self.support = 0  # Support score
        self.dmgRedA = form.carryOverBuffs["Dmg Red"].get()
        self.dmgRedB = form.carryOverBuffs["Dmg Red"].get()
        self.attacksPerformed = 0
        self.superAttacksPerformed = 0
        # Required for getting APTs for individual attacks
        self.atkPerAttackPerformed = np.zeros(MAX_TURN)
        self.atkPerSuperPerformed = np.zeros(MAX_TURN)
        self.critPerAttackPerformed = np.zeros(MAX_TURN)
        self.critPerSuperPerformed = np.zeros(MAX_TURN)
        self.APT = 0
        self.activeSkillAttackActivated = False
        self.stackedStats = dict(zip(STACK_EFFECTS, np.zeros(len(STACK_EFFECTS))))
        self.randomKi = self.getRandomKi(form)

    def setState(self, unit, form):
        self.updateStackedStats(unit)
        for ability in form.abilities["Start of Turn"]:
            ability.applyToState(self, unit, form)
        self.atkModifier = self.getAvgAtkMod(form, unit)

        for ability in form.abilities["Active / Finish Attacks"]:
            ability.applyToState(self, unit, form)

        for ability in form.abilities["Collect Ki"]:
            ability.applyToState(self, unit, form)
        avgDefStartOfTurn = getDefStat(
            unit.DEF,
            self.p1Buff["DEF"],
            form.linkEffects["DEF"],
            form.carryOverBuffs["DEF"].get(),
            self.p3Buff["DEF"],
            self.stackedStats["DEF"],
        )
        for ability in form.abilities["Receive Attacks"]:
            ability.applyToState(self, unit, form)
        self.atkModifier = self.getAvgAtkMod(form, unit)
        self.ki = min(round(self.buff["Ki"] + self.randomKi), rarity2MaxKi[unit.rarity])
        self.pN, self.pSA, self.pUSA = getAttackDistribution(
            self.buff["Ki"], self.randomKi, form.intentional12Ki, unit.rarity
        )
        self.aaSA = branchAS(
            -1, len(self.aaPSuper), unit.pHiPo["AA"], 1, self.aaPSuper, self.aaPGuarantee, unit.pHiPo["AA"]
        )
        self.aa = branchAA(
            -1, len(self.aaPSuper), unit.pHiPo["AA"], 1, self.aaPSuper, self.aaPGuarantee, unit.pHiPo["AA"]
        )
        pAttack = 1 - PROBABILITY_KILL_ENEMY_BEFORE_ATTACKING[self.slot - 1]
        pNextAttack = pAttack - PROBABILITY_KILL_ENEMY_PER_ATTACK
        self.attacksPerformed += pAttack + self.aa * pNextAttack
        # Assume Binomial distribution for aaSA for the expected value
        self.superAttacksPerformed += pAttack + self.aaSA * pNextAttack
        self.addStacks(form, unit)
        # Compute support bonuses from super attack effects
        for superAttackType in form.superAttacks.keys():
            match superAttackType:
                case "18 Ki":
                    numSupers = pAttack * self.pUSA
                case "12 Ki":
                    numSupers = pAttack * self.pSA
                case "AS":
                    numSupers = pAttack * self.aaSA * pNextAttack
            for superAttackEFfect in SUPPORT_SUPER_ATTACK_EFFECTS:
                supportFactor = (
                    superAttackSupportFactorConversion[superAttackEFfect]
                    * form.superAttacks[superAttackType].effects[superAttackEFfect].buff
                    * (
                        form.superAttacks[superAttackType].effects[superAttackEFfect].duration
                        - 1
                        + (NUM_SLOTS - self.slot) / (NUM_SLOTS - 1)
                    )
                )
                self.support += supportFactor * numSupers
            self.multiChanceBuff["Nullify"].updateChance(
                "Disable Action",
                numSupers
                * P_NULLIFY_FROM_DISABLE_SUPER[self.slot - 1]
                * form.superAttacks[superAttackType].effects["Disable Action"].buff,
                "Nullify",
            )
        self.buff["Guard"] = min(self.buff["Guard"], 1)
        self.avgDefPreSuper = getDefStat(
            unit.DEF,
            self.p1Buff["DEF"],
            form.linkEffects["DEF"],
            self.p2Buff["DEF"],
            self.p3Buff["DEF"],
            self.stackedStats["DEF"],
        )
        self.normalDamageTakenPreSuper = getDamageTaken(
            0,
            self.multiChanceBuff["EvasionA"].prob,
            self.buff["Guard"],
            MAX_NORMAL_DAM_PER_TURN[self.turn - 1],
            unit.TDB,
            self.buff["Dmg Red against Normals"],
            self.avgDefPreSuper,
        )
        self.saDamageTakenPreSuper = getDamageTaken(
            self.multiChanceBuff["Nullify"].prob,
            self.multiChanceBuff["EvasionA"].prob,
            self.buff["Guard"],
            MAX_SA_DAM_PER_TURN[self.turn - 1],
            unit.TDB,
            self.dmgRedA,
            self.avgDefPreSuper,
        )
        for ability in form.abilities["Attack Enemy"]:
            ability.applyToState(self, unit, form)
        self.normal = getNormal(
            unit.kiMod12,
            self.ki,
            unit.ATK,
            self.p1Buff["ATK"],
            self.stackedStats["ATK"],
            form.linkEffects["SoT ATK"],
            self.p2Buff["ATK"],
            self.p3Buff["ATK"],
        )
        self.SA = getSA(
            unit.kiMod12,
            unit.ATK,
            self.p1Buff["ATK"],
            self.stackedStats["ATK"],
            form.linkEffects["SoT ATK"],
            self.p2Buff["ATK"],
            self.p3Buff["ATK"],
            form.superAttacks["12 Ki"].multiplier,
            unit.nCopies,
            form.superAttacks["12 Ki"].effects["ATK"].duration,
            form.superAttacks["12 Ki"].effects["ATK"].buff,
        )
        self.addSA = getSA(
            unit.kiMod12,
            unit.ATK,
            self.p1Buff["ATK"],
            self.stackedStats["ATK"],
            form.linkEffects["SoT ATK"],
            self.p2Buff["ATK"],
            self.p3Buff["ATK"],
            form.superAttacks["AS"].multiplier,
            unit.nCopies,
            form.superAttacks["AS"].effects["ATK"].duration,
            form.superAttacks["AS"].effects["ATK"].buff,
        )
        self.USA = getUSA(
            unit.kiMod12,
            self.ki,
            unit.ATK,
            self.p1Buff["ATK"],
            self.stackedStats["ATK"],
            form.linkEffects["SoT ATK"],
            self.p2Buff["ATK"],
            self.p3Buff["ATK"],
            form.superAttacks["18 Ki"].multiplier,
            unit.nCopies,
            form.superAttacks["18 Ki"].effects["ATK"].duration,
            form.superAttacks["18 Ki"].effects["ATK"].buff,
        )
        self.APT += getAPT(
            self.aaPSuper,
            form.superAttacks["12 Ki"].multiplier,
            unit.nCopies,
            form.superAttacks["AS"].effects["ATK"].duration,
            form.superAttacks["AS"].effects["ATK"].buff,
            form.superAttacks["12 Ki"].effects["ATK"].buff,
            form.superAttacks["18 Ki"].effects["ATK"].buff,
            self.stackedStats["ATK"],
            self.p1Buff["ATK"],
            self.p2Buff["ATK"],
            self.normal,
            self.addSA,
            self.SA,
            self.USA,
            unit.pHiPo["AA"],
            self.aaPGuarantee,
            self.multiChanceBuff["Nullify"].chances["SA Counter"],
            form.normalCounterMult,
            form.saCounterMult,
            self.pN,
            self.pSA,
            self.pUSA,
            unit.rarity,
            self.slot,
            form.canAttack,
            copy.copy(self.multiChanceBuff["Crit"]),
            unit.critMultiplier,
            self.atkModifier,
            self.atkPerAttackPerformed,
            self.atkPerSuperPerformed,
            self.critPerAttackPerformed,
            self.critPerSuperPerformed,
            form.superAttacks["AS"].effects["Crit"].buff,
            form.superAttacks["12 Ki"].effects["Crit"].buff,
            form.superAttacks["18 Ki"].effects["Crit"].buff,
        )
        self.getAvgDefMult(form, unit)
        self.p2Buff["DEF"] += self.p2DefB
        self.avgDefPostSuper = getDefStat(
            unit.DEF,
            self.p1Buff["DEF"],
            form.linkEffects["DEF"],
            self.p2Buff["DEF"],
            self.p3Buff["DEF"],
            self.avgDefMult,
        )
        self.normalDamageTakenPostSuper = getDamageTaken(
            0,
            self.multiChanceBuff["EvasionB"].prob,
            self.buff["Guard"],
            MAX_NORMAL_DAM_PER_TURN[self.turn - 1],
            unit.TDB,
            self.buff["Dmg Red against Normals"],
            self.avgDefPostSuper,
        )
        self.saDamageTakenPostSuper = getDamageTaken(
            self.multiChanceBuff["Nullify"].prob,
            self.multiChanceBuff["EvasionB"].prob,
            self.buff["Guard"],
            MAX_SA_DAM_PER_TURN[self.turn - 1],
            unit.TDB,
            self.dmgRedB,
            self.avgDefPostSuper,
        )
        self.buff["Heal"] += (
            form.linkEffects["Heal"]
            + form.superAttacks["18 Ki"].effects["Heal"].buff * self.pUSA
            + form.superAttacks["12 Ki"].effects["Heal"].buff * self.pSA
            + form.superAttacks["AS"].effects["Heal"].buff * self.aaSA
            + (0.03 + 0.0015 * HIPO_RECOVERY_BOOST[unit.nCopies - 1])
            * avgDefStartOfTurn
            * self.numSameTypeOrbs
            / AVG_HEALTH
        )
        self.normalDamageTaken = (
            NUM_NORMAL_ATTACKS_DIRECTED_BEFORE_ATTACKING[self.slot - 1] * self.normalDamageTakenPreSuper
            + NUM_NORMAL_ATTACKS_DIRECTED_AFTER_ATTACKING[self.slot - 1] * self.normalDamageTakenPostSuper
        ) / (NUM_NORMAL_ATTACKS_DIRECTED[self.slot - 1])
        self.saDamageTaken = (
            NUM_SUPER_ATTACKS_DIRECTED_BEFORE_ATTACKING[self.slot - 1] * self.saDamageTakenPreSuper
            + NUM_SUPER_ATTACKS_DIRECTED_AFTER_ATTACKING[self.slot - 1] * self.saDamageTakenPostSuper
        ) / (NUM_SUPER_ATTACKS_DIRECTED[self.slot - 1])
        self.slotFactor = self.slot**SLOT_FACTOR_POWER
        self.useability = (
            unit.teams
            / NUM_TEAMS_MAX
            * (1 + USEABILITY_SUPPORT_FACTOR * self.support + form.linkEffects["Commonality"])
        )
        attributeValues = [
            unit.leaderSkill,
            unit.SBR,
            unit.HP,
            self.useability,  # Requires user input, should make a version that loads from file
            self.buff["Heal"],
            self.support,
            self.APT,
            self.normalDamageTaken,
            self.saDamageTaken,
            self.slotFactor,
        ]
        self.attributes = dict(zip(ATTTRIBUTE_NAMES, attributeValues))
        form.attacksPerformed += self.attacksPerformed
        form.superAttacksPerformed += self.superAttacksPerformed

    def updateStackedStats(self, unit):
        # Removes stacks from previous states if worn out
        for stat in STACK_EFFECTS:
            # Update previous stack durations
            for stack in unit.stacks[stat]:
                stack.duration -= RETURN_PERIOD_PER_SLOT[unit.states[-1].slot - 1]
            # Remove them if expired
            unit.stacks[stat] = [stack for stack in unit.stacks[stat] if stack.duration > 0]
            # Apply stacks
            for stack in unit.stacks[stat]:
                self.stackedStats[stat] += stack.buff

    def addStacks(self, form, unit):
        for stat in STACK_EFFECTS:
            if unit.rarity == "LR":
                # If stack for long enough to last to next turn
                if form.superAttacks["18 Ki"].effects[stat].duration > RETURN_PERIOD_PER_SLOT[self.slot - 1]:
                    unit.stacks[stat].append(
                        Stack(
                            stat,
                            self.pUSA * form.superAttacks["18 Ki"].effects[stat].buff,
                            form.superAttacks["18 Ki"].effects[stat].duration,
                        )
                    )
            if form.superAttacks["12 Ki"].effects[stat].duration > RETURN_PERIOD_PER_SLOT[self.slot - 1]:
                unit.stacks[stat].append(
                    Stack(
                        stat,
                        self.pSA * form.superAttacks["12 Ki"].effects[stat].buff,
                        form.superAttacks["12 Ki"].effects[stat].duration,
                    )
                )
            if form.superAttacks["AS"].effects[stat].duration > RETURN_PERIOD_PER_SLOT[self.slot - 1]:
                unit.stacks[stat].append(
                    Stack(
                        stat,
                        self.aaSA * form.superAttacks["AS"].effects[stat].buff,
                        form.superAttacks["AS"].effects[stat].duration,
                    )
                )

    def getAvgDefMult(self, form, unit):
        self.avgDefMult = (
            self.stackedStats["DEF"] + (self.pSA + self.aaSA) * form.superAttacks["12 Ki"].effects["DEF"].buff
        )
        if unit.rarity == "LR":  # If unit is a LR
            self.avgDefMult += self.pUSA * form.superAttacks["18 Ki"].effects["DEF"].buff

    def getAvgAtkMod(self, form, unit):
        return self.multiChanceBuff["Crit"].prob * unit.critMultiplier + (1 - self.multiChanceBuff["Crit"].prob) * (
            self.buff["AEAAT"] * (AEAAT_MULTIPLIER + unit.TAB * AEAAT_TAB_INC)
            + (1 - self.buff["AEAAT"])
            * (
                self.buff["Disable Guard"] * (DISABLE_GUARD_MULTIPLIER + unit.TAB * DISABLE_GUARD_TAB_INC)
                + (1 - self.buff["Disable Guard"]) * (AVG_TYPE_ADVANATGE + unit.TAB * DEFAULT_TAB_INC)
            ) * (1 - ENEMY_DODGE_CHANCE + ENEMY_DODGE_CHANCE * self.buff["Attacks Guaranteed to Hit"])
        )

    def getRandomKi(self, form):
        return (
            (0 if form.giantRageMode else KI_SUPPORT)
            + self.kiPerOtherTypeOrb * self.numOtherTypeOrbs
            + self.kiPerSameTypeOrb * self.numSameTypeOrbs
            + self.kiPerOtherTypeOrb * self.numRainbowOrbs
            + form.linkEffects["Ki"]
        )


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
        self.condition = getCondition(form.inputHelper)
        self.activated = False


class GiantRageMode(SingleTurnAbility):
    def __init__(self, form, args):
        super().__init__(form)
        self.ATK = args[0]
        form.inputHelper.parent = form.inputHelper.parentMap[form.inputHelper.parent]        
        self.giantRageForm = Form(form.inputHelper, 1, form.rarity, form.EZA, form.formIdx + 1, 0, giantRageMode=True)

    def applyToState(self, state, unit=None, form=None):
        if form.checkCondition(self.condition, self.activated, True) and unit.fightPeak:
            self.activated = True
            # Create a State so can get access to setState for damage calc
            self.giantRageModeState = State(unit, self.giantRageForm, state.slot, state.turn)
            giantRageUnit = copy.deepcopy(unit)
            giantRageUnit.ATK = self.ATK
            self.giantRageModeState.setState(giantRageUnit, self.giantRageForm)  # Calculate the APT of the state
            state.APT += self.giantRageModeState.APT * NUM_SLOTS * giantRageUnit.giantRageDuration
            state.support += GIANT_RAGE_SUPPORT


class Revive(SingleTurnAbility):
    def __init__(self, form, args):
        super().__init__(form)
        self.hpRegen, self.isThisCharacterOnly = args
        form.inputHelper.parent = form.inputHelper.parentMap[form.inputHelper.parent]
        self.abilities = abilityQuestionaire(form, "How many additional constant buffs does this revive have?", Buff)

    def applyToState(self, state, unit=None, form=None):
        if form.checkCondition(self.condition, self.activated, True) and unit.fightPeak:
            self.activated = True
            state.buff["Heal"] = min(state.buff["Heal"] + self.hpRegen, 1)
            if self.isThisCharacterOnly:
                state.support += REVIVE_UNIT_SUPPORT_BUFF
            else:
                state.support += REVIVE_ROTATION_SUPPORT_BUFF
            form.abilities["Start of Turn"].extend(self.abilities)
            form.revived = True


class Domain(SingleTurnAbility):
    def __init__(self, form, args):
        super().__init__(form)
        self.domainType, buff, prop, self.duration = args
        self.effectiveBuff = buff * aprioriProbMod(prop, True)
        form.inputHelper.parent = form.inputHelper.parentMap[form.inputHelper.parent]
        self.abilities = abilityQuestionaire(
            form, "How many additional buffs are there when this Domain is active?", TurnDependent
        )

    def applyToState(self, state, unit=None, form=None):
        if form.checkCondition(self.condition, self.activated, True):
            self.activated = True
            start = state.turn
            end = start + self.duration - 1
            params = [start, end]
            match self.domainType:
                case "Increase Damage Received":
                    self.abilities.append(
                        TurnDependent(
                            form, 1, False, "ATK Support", self.effectiveBuff * AVG_SOT_STATS, self.duration, params
                        )
                    )
                    self.abilities.append(TurnDependent(form, 1, False, "P3 ATK", self.effectiveBuff, 1, params))
            form.abilities["Start of Turn"].extend(self.abilities)


class ActiveSkillBuff(SingleTurnAbility):
    def __init__(self, form, args):
        super().__init__(form)
        self.effect, self.buff, self.duration, self.maxActivations = args
        self.activations = 0

    def applyToState(self, state, unit=None, form=None):
        if form.checkCondition(self.condition, self.activations == self.maxActivations, True) and unit.fightPeak:
            self.activations += 1
            start = state.turn
            end = start + self.duration - 1
            params = [start, end]
            if self.effect in P3_EFFECTS_SUFFIX:
                self.effect = "P3 " + self.effect
            ability = TurnDependent(form, 1, False, self.effect, self.buff, effectDuration=self.duration, args=params)
            form.abilities["Start of Turn"].append(ability)


class ActiveSkillAttack(SingleTurnAbility):
    def __init__(self, form, args):
        super().__init__(form)
        attackMultiplier, attackBuff, self.triggersTransformation = args
        self.activeMult = specialAttackConversion[attackMultiplier] + attackBuff

    def applyToState(self, state, unit=None, form=None):
        if form.checkCondition(self.condition, self.activated, True) and unit.fightPeak:
            self.activated = True
            state.attacksPerformed += 1  # Parameter should be used to determine buffs from per attack performed buffs
            state.superAttacksPerformed += 1
            state.activeSkillAttackActivated = True
            activeAtk = (
                getActiveAtk(
                    unit.kiMod12,
                    rarity2MaxKi[unit.rarity],
                    unit.ATK,
                    state.p1Buff["ATK"],
                    state.stackedStats["ATK"],
                    self.form.linkEffects["SoT ATK"],
                    state.p2Buff["ATK"],
                    state.p3Buff["ATK"],
                    self.activeMult,
                    unit.nCopies,
                )
                * state.atkModifier
            )
            if yesNo2Bool[self.triggersTransformation]:
                unit.transformationAttackAPT = activeAtk
                unit.transformationTriggered = True
                unit.nextForm = 1
            else:
                state.APT += activeAtk


# This skill is to apply to a unit already in it's standby mode.
# The condition to enter & exit the standy mode will be controlled by regular form changes.
class StandbyFinishSkill(SingleTurnAbility):
    def __init__(self, form, args):
        super().__init__(form)
        self.finishSkillChargeCondition, attackMultiplier, self.attackBuff, self.buffPerCharge = args
        self.activeMult = specialAttackConversion[attackMultiplier]

    def applyToState(self, state, unit=None, form=None):
        form.charge += form.getCharge(self.finishSkillChargeCondition)
        if form.checkCondition(self.condition, self.activated, True):
            self.activated = True
            self.activeMult += self.buffPerCharge * form.charge
            unit.transformationAttackAPT = (
                getActiveAtk(
                    unit.kiMod12,
                    rarity2MaxKi[unit.rarity],
                    unit.ATK,
                    state.p1Buff["ATK"],
                    state.stackedStats["ATK"],
                    self.form.linkEffects["SoT ATK"],
                    state.p2Buff["ATK"],
                    state.p3Buff["ATK"],
                    self.activeMult * (1 + self.attackBuff),
                    unit.nCopies,
                )
                * state.atkModifier
            )
            unit.transformationTriggered = True
            unit.nextForm = -1


class RevivalCounterFinishSkill(StandbyFinishSkill):
    def __init__(self, form, args):
        args = ["Revive"] + args + [0]
        super().__init__(form, args)


class PassiveAbility(Ability):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, effectDuration=None):
        super().__init__(form)
        self.activationProbability = aprioriProbMod(activationProbability, knownApriori)
        self.effect = effect
        self.effectDuration = effectDuration if effectDuration != None else 1
        self.effectiveBuff = buff * self.activationProbability
        if effect == "AAChance":
            self.superChance = form.inputHelper.getAndSaveUserInput(
                "What is the chance for this to become a super?", default=0.0
            )
        if effect in SUPPORT_EFFECTS and effectDuration == None:
            self.effectDuration = form.inputHelper.getAndSaveUserInput(
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

    def applyToState(self, state, unit=None, form=None):
        # Need to update in case one of the relevant variables has been updated
        if state.activeSkillAttackActivated:
            pHaveKi = 1
        else:
            pHaveKi = 1 - ZTP_CDF(self.ki - 1 - state.buff["Ki"], state.randomKi)
        effectiveBuff = self.effectiveBuff * pHaveKi
        supportBuff = self.supportBuff[state.slot - 1] * pHaveKi
        activationProbability = self.activationProbability * pHaveKi
        # Check if state is elligible for ability
        if state.turn >= self.start and state.turn <= self.end and state.slot in self.slots:
            # If a support ability
            if self.effect in REGULAR_SUPPORT_EFFECTS:
                state.support += supportFactorConversion[self.effect] * supportBuff
            elif self.effect in ORB_CHANGING_EFFECTS:
                state.support += supportFactorConversion[self.effect] * supportBuff
                state.numOtherTypeOrbs = orbChangeConversion[self.effect][
                    "Other"
                ] * activationProbability + state.numOtherTypeOrbs * (1 - activationProbability)
                state.numSameTypeOrbs = orbChangeConversion[self.effect][
                    "Same"
                ] * activationProbability + state.numSameTypeOrbs * (1 - activationProbability)
                state.numRainbowOrbs = orbChangeConversion[self.effect][
                    "Rainbow"
                ] * activationProbability + state.numRainbowOrbs * (1 - activationProbability)
            elif self.effect in state.buff.keys():
                state.buff[self.effect] += effectiveBuff
            elif self.effect in state.p1Buff.keys():
                state.p1Buff[self.effect] += effectiveBuff
            elif self.effect in MULTI_CHANCE_EFFECTS_NO_NULLIFY:
                state.multiChanceBuff[self.effect].updateChance("Start of Turn", effectiveBuff, self.effect, state)
            else:  # Edge cases
                match self.effect:
                    case "Dmg Red":
                        state.dmgRedA += effectiveBuff
                        state.dmgRedB += effectiveBuff
                        state.buff["Dmg Red against Normals"] += effectiveBuff
                    case "Dmg Red B":
                        state.dmgRedB += effectiveBuff
                    case "Evasion":
                        state.multiChanceBuff["EvasionA"].updateChance("Start of Turn", effectiveBuff, "Evasion", state)
                        state.multiChanceBuff["EvasionB"].updateChance("Start of Turn", effectiveBuff, "Evasion", state)
                    case "AdditionalSuper":
                        state.aaPSuper.append(activationProbability)
                        state.aaPGuarantee.append(0)
                    case "AAChance":
                        state.aaPGuarantee.append(activationProbability)
                        state.aaPSuper.append(activationProbability * self.superChance)
                    case "Ki (Type Ki Sphere)":
                        state.kiPerOtherTypeOrb += effectiveBuff
                        state.kiPerSameTypeOrb += effectiveBuff
                    case "Ki (Ki Sphere)":
                        state.kiPerOtherTypeOrb += effectiveBuff
                        state.kiPerSameTypeOrb += effectiveBuff
                        state.kiPerRainbowKiSphere += effectiveBuff
                    case "Ki (Same Type Ki Sphere)":
                        state.kiPerSameTypeOrb += effectiveBuff
                    case "Ki (Rainbow Ki Sphere)":
                        state.kiPerRainbowKiSphere += effectiveBuff
                    case "P2 ATK":
                        state.p2Buff["ATK"] += effectiveBuff
                    case "P2 DEF":
                        state.p2Buff["DEF"] += effectiveBuff
                    case "P3 ATK":
                        state.p3Buff["ATK"] += effectiveBuff
                    case "P3 DEF":
                        state.p3Buff["DEF"] += effectiveBuff
                    case "P3 Crit":
                        state.multiChanceBuff["Crit"].updateChance("Active Skill", effectiveBuff, "Crit", state)
                        state.atkModifier = state.getAvgAtkMod(form, unit)
                    case "P3 Evasion":
                        state.multiChanceBuff["EvasionA"].updateChance("Active Skill", effectiveBuff, "Evasion", state)
                        state.multiChanceBuff["EvasionB"].updateChance("Active Skill", effectiveBuff, "Evasion", state)
                    case "P3 Disable Action":
                        state.multiChanceBuff["Nullify"].updateChance(
                            "Disable Action", P_NULLIFY_FROM_DISABLE_ACTIVE, "Nullify", state
                        )
                    case "Delay Target":
                        state.support += supportFactorConversion[self.effect] * supportBuff
                        state.dmgRedA = 1
                        state.dmgRedB = 1
                        state.buff["Dmg Red against Normals"] = 1
            state.randomKi = state.getRandomKi(form)


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


class AttackReceivedThreshold(PassiveAbility):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args):
        super().__init__(form, activationProbability, knownApriori, effect, buff)
        self.threshold = args[0]

    def applyToState(self, state, unit=None, form=None):
        if form.numAttacksReceived >= self.threshold:
            match self.effect:
                case "Ki":
                    state.buff["Ki"] += self.effectiveBuff
                case "ATK":
                    state.p2Buff["ATK"] += self.effectiveBuff
                case "DEF":
                    state.p2Buff["DEF"] += self.effectiveBuff
                case "AdditionalSuper":
                    state.aaPSuper.append(self.effectiveBuff)
                    state.aaPGuarantee.append(0)
                case "Scouter":
                    state.support += supportFactorConversion[self.effect] * self.supportBuff[state.slot - 1]


class AttackPerformedThreshold(PassiveAbility):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args):
        super().__init__(form, activationProbability, knownApriori, effect, buff)
        self.threshold, self.requiresSuperAttack = args

    def applyToState(self, state, unit=None, form=None):
        if self.requiresSuperAttack:
            numPerformed = form.superAttacksPerformed
        else:
            numPerformed = form.attacksPerformed
        if numPerformed >= self.threshold:
            match self.effect:
                case "ATK":
                    state.p2Buff[self.effect] += self.effectiveBuff


class PerEvent(PassiveAbility):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, max):
        super().__init__(form, activationProbability, knownApriori, effect, buff)
        self.max = max
        self.applied = 0


class PerTurn(PerEvent):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args):
        super().__init__(form, activationProbability, knownApriori, effect, buff, args[0])

    def applyToState(self, state, unit=None, form=None):
        turnBuff = self.effectiveBuff
        buffToGo = self.max - self.applied
        cappedTurnBuff = min(buffToGo, turnBuff)
        form.carryOverBuffs[self.effect].add(cappedTurnBuff)
        match self.effect:
            case "Ki":
                state.buff["Ki"] += cappedTurnBuff
            case "ATK":
                state.p1Buff["ATK"] += cappedTurnBuff
            case "DEF":
                state.p1Buff["DEF"] += cappedTurnBuff
            case "Crit":
                state.multiChanceBuff["Crit"].updateChance("On Super", cappedTurnBuff, "Crit", state)
                state.atkModifier = state.getAvgAtkMod(form, unit)
            case "Dmg Red":
                state.dmgRedA += cappedTurnBuff
                state.dmgRedB += cappedTurnBuff
                state.buff["Dmg Red against Normals"] += cappedTurnBuff
        self.applied += cappedTurnBuff


class PerAttackPerformed(PerEvent):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args):
        super().__init__(form, activationProbability, knownApriori, effect, buff, args[0])
        self.requiresSuperAttack = yesNo2Bool[args[1]]
        self.withinTheSameTurn = yesNo2Bool[args[2]]

    def applyToState(self, state, unit=None, form=None):
        buffPerAttack = self.effectiveBuff * (np.arange(len(state.aaPSuper) + 1) + 1)
        if self.requiresSuperAttack:
            turnBuff = self.effectiveBuff * state.superAttacksPerformed
        else:
            turnBuff = self.effectiveBuff * state.attacksPerformed
        buffToGo = self.max - self.applied
        cappedTurnBuff = min(buffToGo, turnBuff)
        cappedBuffPerAttack = np.minimum(buffPerAttack, buffToGo)
        if not (self.requiresSuperAttack):
            match self.effect:
                case "ATK":
                    state.atkPerAttackPerformed = cappedBuffPerAttack
                case "Crit":
                    state.critPerAttackPerformed = cappedBuffPerAttack
        match self.effect:
            case "ATK":
                state.atkPerSuperPerformed = cappedBuffPerAttack
            case "DEF":
                state.p2DefB += cappedTurnBuff
            case "Crit":
                state.critPerSuperPerformed = cappedBuffPerAttack
            case "Dmg Red":
                state.dmgRedB += cappedTurnBuff
                state.buff["Dmg Red against Normals"] += cappedTurnBuff
            case "Evasion":
                state.multiChanceBuff["EvasionB"].updateChance("On Super", cappedTurnBuff, self.effect, state)
        if not (self.withinTheSameTurn):
            form.carryOverBuffs[self.effect].add(cappedTurnBuff)
            self.applied += cappedTurnBuff


class PerAttackReceived(PerEvent):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args):
        super().__init__(form, activationProbability, knownApriori, effect, buff, args[0])

    def applyToState(self, state, unit=None, form=None):
        turnBuff = self.effectiveBuff * state.numAttacksReceived
        buffToGo = self.max - self.applied
        cappedTurnBuff = min(buffToGo, turnBuff)
        form.carryOverBuffs[self.effect].add(cappedTurnBuff)
        match self.effect:
            case "Ki":
                state.buff["Ki"] += min(self.effectiveBuff * state.numAttacksReceivedBeforeAttacking, buffToGo)
            case "ATK":
                state.p2Buff["ATK"] += min(self.effectiveBuff * state.numAttacksReceivedBeforeAttacking, buffToGo)
            case "DEF":
                state.p2Buff["DEF"] += min((state.numAttacksReceived - 1) * self.effectiveBuff / 2, buffToGo)
            case "Crit":
                state.multiChanceBuff["Crit"].updateChance("On Super", min(self.effectiveBuff * state.numAttacksReceivedBeforeAttacking, buffToGo), "Crit", state)
                state.atkModifier = state.getAvgAtkMod(form, unit)
        self.applied += cappedTurnBuff


class PerAttackGuarded(PerEvent):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args):
        super().__init__(form, activationProbability, knownApriori, effect, buff, args[0])

    def applyToState(self, state, unit=None, form=None):
        turnBuff = self.effectiveBuff * state.numAttacksReceived * state.buff["Guard"]
        buffToGo = self.max - self.applied
        cappedTurnBuff = min(buffToGo, turnBuff)
        form.carryOverBuffs[self.effect].add(cappedTurnBuff)
        match self.effect:
            case "Ki":
                state.buff["Ki"] += min(self.effectiveBuff * state.numAttacksReceivedBeforeAttacking, buffToGo)
            case "ATK":
                state.p2Buff["ATK"] += min(self.effectiveBuff * state.numAttacksReceivedBeforeAttacking, buffToGo)
            case "DEF":
                state.p2Buff["DEF"] += min((state.numAttacksReceived - 1) * self.effectiveBuff / 2, buffToGo)
            case "Crit":
                state.multiChanceBuff["Crit"].updateChance("On Super", min(self.effectiveBuff * state.numAttacksReceivedBeforeAttacking, buffToGo), "Crit", state)
                state.atkModifier = state.getAvgAtkMod(form, unit)
        self.applied += cappedTurnBuff


class PerAttackEvaded(PerEvent):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args):
        super().__init__(form, activationProbability, knownApriori, effect, buff, args[0])
        self.withinTheSameTurn = yesNo2Bool[args[1]]

    def applyToState(self, state, unit=None, form=None):
        turnBuff = self.effectiveBuff * state.numAttacksEvaded
        buffToGo = self.max - self.applied
        cappedTurnBuff = min(buffToGo, turnBuff)
        match self.effect:
            case "Ki":
                state.buff["Ki"] += min(self.effectiveBuff * state.numAttacksEvadedBeforeAttacking, buffToGo)
            case "ATK":
                state.p2Buff["ATK"] += min(self.effectiveBuff * state.numAttacksEvadedBeforeAttacking, buffToGo)
            case "DEF":
                pEvade = state.multiChanceBuff["EvasionA"].prob * (1 - DODGE_CANCEL_FACTOR)
                state.p2Buff["DEF"] += min((NUM_ATTACKS_DIRECTED[state.slot - 1] - 1) * pEvade * (1 - pEvade) * self.effectiveBuff / 2, buffToGo)
            case "Crit":
                state.multiChanceBuff["Crit"].updateChance("On Super", min(self.effectiveBuff * state.numAttacksEvadedBeforeAttacking, buffToGo), "Crit", state)
                state.atkModifier = state.getAvgAtkMod(form, unit)
            case "Evasion":
                evasionA = copy.deepcopy(state.multiChanceBuff["EvasionA"])
                numAttacksDirectedBeforeAttacking = round(NUM_ATTACKS_DIRECTED_BEFORE_ATTACKING[state.slot - 1])
                evasionAChance = [0] * numAttacksDirectedBeforeAttacking
                evasionB = copy.deepcopy(state.multiChanceBuff["EvasionB"])
                numAttacksDirected = round(NUM_ATTACKS_DIRECTED[state.slot - 1])
                evasionBChance = [0] * numAttacksDirected
                for i in range(numAttacksDirected):
                    if i < numAttacksDirectedBeforeAttacking:
                        evasionAChance[i] = evasionA.prob * (1 - DODGE_CANCEL_FACTOR)
                        evasionA.updateChance("On Super", evasionAChance[i] * self.effectiveBuff, "Evasion", state)
                    evasionBChance[i] = evasionB.prob * (1 - DODGE_CANCEL_FACTOR)
                    evasionB.updateChance("On Super", evasionBChance[i] * self.effectiveBuff, "Evasion", state)
                state.multiChanceBuff["EvasionA"].updateChance("On Super", min(np.mean(evasionAChance), buffToGo), "Evasion", state)
                state.multiChanceBuff["EvasionB"].updateChance("On Super", min(np.mean(evasionBChance), buffToGo), "Evasion", state)
                cappedTurnBuff = min(buffToGo, self.effectiveBuff * state.numAttacksEvaded)
        if not (self.withinTheSameTurn):
            form.carryOverBuffs[self.effect].add(cappedTurnBuff)
            self.applied += cappedTurnBuff


class AfterEvent(PassiveAbility):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, effectDuration):
        super().__init__(form, activationProbability, knownApriori, effect, buff)
        self.effectDuration = effectDuration
        self.turnsSinceActivated = 0
        if effect in ADDITIONAL_ATTACK_EFFECTS:
            self.applied = [0, 0]
        else:
            self.applied = 0
        self.eventFactor = 1
    
    def updateBuffToGo(self):
        if self.effect in ADDITIONAL_ATTACK_EFFECTS:
            self.buffToGo = 1.0
        else:
            self.buffToGo = self.effectiveBuff - self.applied

    def resetAppliedBuffs(self, form, state):
        if self.effectDuration < (self.turnsSinceActivated + 1) * RETURN_PERIOD_PER_SLOT[state.slot - 1]:
            if self.effect in ADDITIONAL_ATTACK_EFFECTS:
                form.carryOverBuffs["aaPSuper"].sub(self.applied[0])
                form.carryOverBuffs["aaPGuarantee"].sub(self.applied[1])
                self.applied = [0, 0]
            else:
                form.carryOverBuffs[self.effect].sub(self.applied)
                self.applied = 0
    
    def setTurnBuff(self, state):
        # geometric cdf
        turnBuff = self.effectiveBuff * self.eventFactor
        cappedTurnBuff = min(self.buffToGo, turnBuff)
        if self.effect in state.buff.keys():
            state.buff[self.effect] += cappedTurnBuff
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

    def nextTurnUpdate(self, form, state):
        # If abiltiy going to be active next turn
        if self.effectDuration >= (self.turnsSinceActivated + 1) * RETURN_PERIOD_PER_SLOT[state.slot - 1] and not(np.any(self.applied)):
            if self.effect in ADDITIONAL_ATTACK_EFFECTS:
                form.carryOverBuffs["aaPSuper"].add(state.aaPSuper[-1])
                form.carryOverBuffs["aaPGuarantee"].add(state.aaPGuarantee[-1])
                self.applied = [state.aaPSuper[-1], state.aaPGuarantee[-1]]
            else:
                nextTurnBuff = min(self.buffToGo, self.effectiveBuff)
                form.carryOverBuffs[self.effect].add(nextTurnBuff)
                self.applied += nextTurnBuff
            self.turnsSinceActivated += 1
        else:
            self.turnsSinceActivated = 0


class AfterAttackReceived(AfterEvent):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args=[]):
        super().__init__(form, activationProbability, knownApriori, effect, buff, args[0])

    def applyToState(self, state, unit=None, form=None):
        self.updateBuffToGo()
        # Check if ability will be active next turn
        if np.any(self.applied):
            self.resetAppliedBuffs(form, state)
        # If abiltiy not already active
        else:
            # If buff is a defensive one
            if self.effect in ["DEF", "Dmg Red"]:
                self.eventFactor = (
                    state.numAttacksReceived - 1
                ) / state.numAttacksReceived  # Factor to account for not having the buff on the fist hit
            else:
                self.eventFactor = min(state.numAttacksReceivedBeforeAttacking, 1)
            self.setTurnBuff(state)
        self.nextTurnUpdate(form, state)
            

class AfterGuardActivated(AfterEvent):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args=[]):
        super().__init__(form, activationProbability, knownApriori, effect, buff, args[0])

    def applyToState(self, state, unit=None, form=None):
        self.updateBuffToGo()
        if np.any(self.applied):
            self.resetAppliedBuffs(form, state)
        else:
            # If buff is a defensive one
            if self.effect in ["DEF", "Dmg Red"]:
                self.eventFactor = (
                    state.numAttacksReceived - (1 - state.buff["Guard"]) / state.buff["Guard"]
                ) / state.numAttacksReceived
            else:
                self.eventFactor = min(state.numAttacksReceivedBeforeAttacking * state.buff["Guard"], 1)
            self.setTurnBuff(state)
        self.nextTurnUpdate(form, state)


class AfterAttackEvaded(AfterEvent):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args=[]):
        super().__init__(form, activationProbability, knownApriori, effect, buff, args[0])
        self.required = args[1]
        self.nextAttackingTurn = yesNo2Bool[args[2]]

    def applyToState(self, state, unit=None, form=None):
        self.updateBuffToGo()
        if np.any(self.applied):
            self.resetAppliedBuffs(form, state)
        else:
            if self.required > 1:
                self.eventFactor = 1 - poisson.cdf(self.required - 1, state.numAttacksEvaded)
            # If buff is a defensive one
            elif self.effect in ["DEF", "Dmg Red", "Evasion"]:
                pEvade = state.multiChanceBuff["EvasionA"].prob * (1 - DODGE_CANCEL_FACTOR)
                self.eventFactor = max(
                    state.numAttacksReceived - (1 - pEvade) / pEvade
                , 0) / state.numAttacksReceived
            else:
                self.eventFactor = min(state.numAttacksEvadedBeforeAttacking, 1)
            self.setTurnBuff(state)
        self.nextTurnUpdate(form, state)


class PerformingSuperAttackOffence(PassiveAbility):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args=[]):
        super().__init__(form, activationProbability, knownApriori, effect, buff)

    def applyToState(self, state, unit=None, form=None):
        match self.effect:
            case "ATK":
                state.p2Buff["ATK"] += self.effectiveBuff


class PerformingSuperAttackDefence(PassiveAbility):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args=[]):
        super().__init__(form, activationProbability, knownApriori, effect, buff)

    def applyToState(self, state, unit=None, form=None):
        match self.effect:
            case "DEF":
                # If have activated active skill attack this turn
                if state.superAttacksPerformed > 0:
                    state.p2Buff["DEF"] += self.effectiveBuff
                else:
                    state.p2DefB += self.effectiveBuff
            case "Dmg Red":
                state.dmgRedB += self.effectiveBuff
                state.buff["Dmg Red against Normals"] += self.effectiveBuff
                # If have activated active skill attack this turn
                if state.superAttacksPerformed > 0:
                    state.dmgRedA += self.effectiveBuff


class KiSphereDependent(PerEvent):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args):
        self.orbType, self.required, self.whenAttacking, self.withinTheSameTurn, max = args
        super().__init__(form, activationProbability, knownApriori, effect, buff, max)
        
    def applyToState(self, state, unit=None, form=None):
        match self.orbType:
            case "Any":
                numOrbs = state.numSameTypeOrbs + state.numOtherTypeOrbs + state.numRainbowOrbs
            case "Type":
                numOrbs = state.numSameTypeOrbs + state.numOtherTypeOrbs
            case "Rainbow":
                numOrbs = state.numRainbowOrbs
            case "Same Type":
                numOrbs = state.numSameTypeOrbs
            case "Other Type":
                numOrbs = state.numOtherTypeOrbs
        if self.required == 0:  # If buff per orb
            effectFactor = numOrbs
        else:  # If fixed buff if obtain X orbs
            effectFactor = 1 - poisson.cdf(self.required - 1, numOrbs)
        buffToGo = self.max - self.applied
        cappedTurnBuff = min(buffToGo, self.effectiveBuff)
        buffFromOrbs = cappedTurnBuff * effectFactor
        if self.effect in REGULAR_SUPPORT_EFFECTS:
            state.support += supportFactorConversion[self.effect] * min(buffToGo, self.supportBuff[state.slot - 1]) * effectFactor
        elif self.effect in state.buff.keys():
            state.buff[self.effect] += buffFromOrbs
        elif self.effect in state.p1Buff.keys():
            state.p1Buff[self.effect] += buffFromOrbs
        elif self.effect in MULTI_CHANCE_EFFECTS_NO_NULLIFY:
            state.multiChanceBuff[self.effect].updateChance("Start of Turn", buffFromOrbs, self.effect, state)
        else:
            match self.effect:
                case "Dmg Red":
                    state.dmgRedA += buffFromOrbs
                    state.dmgRedB += buffFromOrbs
                    state.buff["Dmg Red against Normals"] += buffFromOrbs
                case "AdditionalSuper":
                    state.aaPSuper.append(effectFactor)
                    state.aaPGuarantee.append(0)
                case "AAChance":
                    state.aaPGuarantee.append(effectFactor)
                    state.aaPSuper.append(effectFactor * self.superChance)
                case "P2 ATK":
                    state.p2Buff["ATK"] += buffFromOrbs
                case "P2 DEF":
                    state.p2Buff["DEF"] += buffFromOrbs
        if not (yesNo2Bool[self.withinTheSameTurn]):
            form.carryOverBuffs[self.effect].add(buffFromOrbs)
            self.applied += buffFromOrbs


class Nullification(PassiveAbility):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, args):
        super().__init__(form, activationProbability, knownApriori, effect, buff)
        self.hasCounter, self.healthFrac = args

    def applyToState(self, state, unit=None, form=None):
        pNullify = self.activationProbability * aprioriProbMod(saFracConversion[self.effect], True)
        state.buff["Heal"] += self.healthFrac * pNullify / NUM_SLOTS * AVG_SA_DAM / AVG_HEALTH
        if yesNo2Bool[self.hasCounter]:
            state.multiChanceBuff["Nullify"].updateChance("SA Counter", pNullify, "Nullify")
        else:
            state.multiChanceBuff["Nullify"].updateChance("Nullification", pNullify, "Nullify")


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


class FinishSkillActivatedCondition(Condition):
    def __init__(self, requiredCharge):
        self.formAttr = "charge"
        self.conditionValue = requiredCharge


class ReviveCondition(Condition):
    def __init__(self):
        self.formAttr = "revived"
        self.conditionValue = True


# Too niche to conform to a generalised case because there is no formAttr for the charge condtion
class DoubleSameRainbowKiSphereCondition(Condition):
    def __init__(self, chargeCondition):
        self.conditionValue = chargeCondition
        self.currentValue = 0

    def isSatisfied(self, form):
        # NB: this line only works because the chargeCondition does not rely on form.attacksPerformed as that value will increase per turn, wheras here we are assuming the getCharge in constant
        self.currentValue += form.getCharge(self.conditionValue)
        return self.currentValue >= self.conditionValue


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


if __name__ == "__main__":
    unit = Unit(36, "DF_TEQ_WT_Goku", 1, "DEF", "DGE", "ADD", SLOT_1)
