import datetime as dt
from dokkanUnitHelperFunctions import *
import copy
import pickle

# TODO:
# - Maybe make a function which takes in a bunch of independent probability events and returns the overall probability.
# - Also might want to include attack all in atk calcs.
# - If ever do DPT, instead of APT, should use Lowers DEF in calcs. But most enemies are immunue to it anyway, so not a big deal.
# - Add some functionality that can update existing input .txt files with new questions (assuming not relevant to exisiting unit)
# - Whenever I update Evasion change in abilities, I need to reocompute evasion chance using self.buff["Evade"] = self.buff["Evade"] + (1 - self.buff["Evade"]) * (unit.pHiPoDodge + (1 - unit.pHiPoDodge) * form.linkDodge)
# - It would be awesome if after I have read in a unit I could reconstruct the passive description to compare it against the game
# - Instead of asking user how many of something, should ask until they enteran exit key ak a while loop instead of for loop
# - Should read up on python optimisation techniques once is running and se how long it takes. But try be efficient you go.
# - I think the 20x3 state matrix needs to be used to compute the best path
# - Whilst the state matrix is the ideal way, for now just assume a user inputed slot for each form
# - Should put at may not be relevant tag onto end of the prompts that may not always be relevant.
# - Ideally would just pull data from database, but not up in time for new units. Would be amazing for old units though.
# - Leader skill weight should decrease from 5 as new structure adds more variability between leader skills
# - Once calculate how many supers do on turn 1, use this in the SBR calculation for debuffs on super(). i.e. SBR should be one of the last things to be calculated

##################################################### Helper Functions ############################################################################


def abilityQuestionaire(form, abilityPrompt, abilityClass, parameterPrompts=[], types=[], defaults=[]):
    numAbilities = form.inputHelper.getAndSaveUserInput(abilityPrompt, default=0)
    abilities = []
    for i in range(numAbilities):
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
            effectDuration = form.inputHelper.getAndSaveUserInput(
                "How many turns does it last for? Only applicable to abilities with a time limit?.", default=1
            )
            ability = abilityClass(
                form, activationProbability, knownApriori, effect, buff, effectDuration, args=parameters
            )
        elif issubclass(abilityClass, SingleTurnAbility):
            ability = abilityClass(form, parameters)
        abilities.append(ability)
    return abilities


def getConditions(inputHelper):
    """
    Askes the user questions to determine which Condition class(es) apply and returns them. Only want once per condition set.
    """
    numConditions = inputHelper.getAndSaveUserInput("How many conditions have to met?", default=0)
    conditions = [None] * numConditions
    operator = [None]
    if numConditions < 0:
        return ["NOT"], [[None]]
    if  numConditions > 1:
        operator[0] = inputHelper.getAndSaveUserInput(
            "What is the condition logic?", type=clc.Choice(CONDITION_LOGIC), default="AND"
        )
    if numConditions > 2:
        operatorA, conditionsA = getConditions(inputHelper)
        operatorB, conditionsB = getConditions(inputHelper)
        return operator + operatorA + operatorB, conditionsA + conditionsB

    for i in range(numConditions):
        conditionType = inputHelper.getAndSaveUserInput(
            f"What type of condition is # {i + 1}?", type=clc.Choice(CONDITIONS, case_sensitive=False), default="Turn"
        )
        match conditionType:
            case "Turn":
                turnCondition = inputHelper.getAndSaveUserInput(
                    "What is the turn condition (relative to the form's starting turn)?", default=5
                )
                conditions[i] = TurnCondition(turnCondition)
            case "Max HP":
                maxHpCondition = inputHelper.getAndSaveUserInput("What is the maximum HP condition?", default=0.7)
                conditions[i] = MaxHpCondition(maxHpCondition)
            case "Min HP":
                minHpCondition = inputHelper.getAndSaveUserInput("What is the minimum HP condition?", default=0.7)
                conditions[i] = MinHpCondition(minHpCondition)
            case "Enemy Max HP":
                enemyMaxHpCondition = inputHelper.getAndSaveUserInput(
                    "What is the maximum enemy HP condition?", default=0.5
                )
                conditions[i] = EnemyMaxHpCondition(enemyMaxHpCondition)
            case "Enemy Min HP":
                enemyMinHpCondition = inputHelper.getAndSaveUserInput(
                    "What is the minimum enemy HP condition?", default=0.5
                )
                conditions[i] = EnemyMinHpCondition(enemyMinHpCondition)
            case "Num Attacks Performed":
                numAttacksPerformedCondition = inputHelper.getAndSaveUserInput(
                    "How many performed attacks are required?", default=5
                )
                conditions[i] = AttacksPerformedCondition(numAttacksPerformedCondition)
            case "Num Attacks Received":
                numAttacksReceivedCondition = inputHelper.getAndSaveUserInput(
                    "How many received attacks are required?", default=5
                )
                conditions[i] = AttacksReceivedCondition(numAttacksReceivedCondition)
            case "Finish Skill Activation":
                requiredCharge = inputHelper.getAndSaveUserInput("What is the required charge condition?", default=30)
                conditions[i] = FinishSkillActivatedCondition(requiredCharge)

    return operator, [conditions]


######################################################### Classes #################################################################


class InputHelper:
    def __init__(self, mode, id):
        self.mode = mode
        self.filePath = os.path.join(CWD, "DokkanKits", id + ".txt")

    def setInputFile(self, finishedReading=False):
        if self.mode == "manual":
            if finishedReading:
                specifier = "a"
            else:
                specifier = "w"
        elif self.mode == "fromTxt":
            specifier = "r"
        self.file = open(self.filePath, specifier, 1)

    def getAndSaveUserInput(self, prompt, type=None, default=None):
        if self.mode == "fromTxt":
            response = simplest_type(next(self.file, END_OF_FILE_STRING).rstrip())
            # Ignore lines with COMMENT_CHAR
            try:
                if response[0] == COMMENT_CHAR:
                    return self.getAndSaveUserInput(prompt, type=type, default=default)
            except:
                pass
            if response == END_OF_FILE_STRING:
                self.mode = "manual"
                self.setInputFile(finishedReading=True)
        if self.mode == "manual" or response == END_OF_FILE_STRING:
            if type == None and default == None:
                response = clc.prompt(prompt)
            elif type == None:
                response = clc.prompt(prompt, default=default)
            else:
                response = clc.prompt(prompt, type=type, default=default)
            self.file.write(COMMENT_CHAR + " " + prompt.replace("\n", "") + "\n")
            self.file.write(str(response) + "\n")
        return response


class Unit:
    def __init__(self, id, nCopies, brz, HiPo1, HiPo2, inputMode="fromTxt"):
        self.id = str(id)
        self.nCopies = nCopies
        self.brz = brz
        self.HiPo1 = HiPo1
        self.HiPo2 = HiPo2
        self.inputMode = inputMode
        self.picklePath = CWD + "\\DokkanUnits\\" + HIPO_DUPES[nCopies - 1] + "\\unit_" + self.id + ".pkl"
        self.inputHelper = InputHelper(inputMode, self.id)
        if inputMode == "manual" or inputMode == "fromTxt":
            self.inputHelper.setInputFile()
            self.getConstants()  # Requires user input, should make a version that loads from file
            self.getHiPo()  # Requires user input, should make a version that loads from file
            self.getSBR()  # Requires user input, should make a version that loads from file
            self.getStates()
            self.inputHelper.file.close()
        # elif inputMode == "fromPickle":
        # self = pickle.load(open(self.picklePath, "rb"))
        elif inputMode == "fromWeb":
            print(f"inputMode: {inputMode} not implemented yet. Bailing out.")
            exit()
        else:
            print("Incorrect inputMode: {inputMpde} given. Bailing out.")
            exit()
        self.saveUnit()

    def getConstants(self):
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
                "How would you rate the unit's leader skill on a scale of 1-10?\n200% limited - e.g. LR Hatchiyak Goku\n 200% small - e.g. LR Metal Cooler\n 200% medium - e.g. PHY God Goku\n 200% large - e.g. LR Vegeta & Trunks\n",
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
        self.pHiPoAA = HiPoAbilities[2]
        self.pHiPoCrit = HiPoAbilities[3]
        self.pHiPoDodge = HiPoAbilities[4]
        self.TAB = HIPO_TYPE_ATK_BOOST[self.nCopies - 1]
        self.TDB = HIPO_TYPE_DEF_BOOST[self.nCopies - 1]

    def getSBR(self):
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
                    type=clc.Choice(sealTurnConversion.keys()),
                    default=0,
                )
            ]
            if seal != 0:
                seal *= self.inputHelper.getAndSaveUserInput(
                    "What is the unit's chance to seal?", default=0.0
                )  # Scale by number of enemies for all enemy seal, same for stun

            stun = stunTurnConversion[
                self.inputHelper.getAndSaveUserInput(
                    "How many turns does the unit stun for?",
                    type=clc.Choice(stunTurnConversion.keys()),
                    default="0",
                )
            ]
            if stun != 0:
                stun *= self.inputHelper.getAndSaveUserInput("What is the unit's chance to stun?", default=0.0)

            attDebuffOnAtk = attDebuffTurnConversion[
                self.inputHelper.getAndSaveUserInput(
                    "How many turns does the unit lower the enemy attack by attacking?",
                    type=clc.Choice(attDebuffTurnConversion.keys()),
                    default="0",
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
                    type=clc.Choice(attDebuffTurnConversion.keys()),
                    default="0",
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
                sbrActiveSkillEffect = self.getSBR()
                sbrActiveSkillBuff += SBR_DF ** (sbrActiveSkillTurn - 1) * sbrActiveSkillEffect

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
        self.numForms = self.inputHelper.getAndSaveUserInput("How many forms does the unit have?", default=1)
        turn = 1
        formIdx = 0
        self.fightPeak = False
        # Only non-zero in between activating the stanby finish skill attack and applying to subsequent state
        self.standbyFinishSkillAPT = 0
        nextForm = 1
        applyFinishSkillAPT = False
        self.critMultiplier = (CRIT_MULTIPLIER + self.TAB * CRIT_TAB_INC) * BYPASS_DEFENSE_FACTOR
        while turn <= MAX_TURN:
            formIdx += nextForm
            if nextForm == 1:
                # Ignore case where turn == 1 as this is when nextForm == True doesn't mean transformation
                if turn != 1:
                    form.transformed = True
                form = Form(self.inputHelper, turn, self.rarity, self.EZA, formIdx, self.numForms)
                self.forms.append(form)
            elif nextForm == -1:
                form = self.forms[-2]
            nextForm = 0
            slot = form.slot
            form.turn = turn
            nextTurn = turn + RETURN_PERIOD_PER_SLOT[slot - 1]
            form.nextTurnRelative = nextTurn - form.initialTurn + 1
            if abs(PEAK_TURN - turn) < abs(nextTurn - PEAK_TURN) and not (self.fightPeak):
                self.fightPeak = True
            state = State(self, form, slot, turn)
            state.setState(self, form)
            # If have finished a standby
            if self.standbyFinishSkillAPT != 0:
                # If the trigger condition for the finish is a revive, apply APT this turn, otherwise next.
                try:
                    hasReviveCounter = form.abilities["Attack Enemy"][-1].finishSkillChargeCondition == "Revive"
                except:
                    hasReviveCounter = False
                if hasReviveCounter:
                    applyFinishSkillAPT = True
                    nextForm = -1
                if applyFinishSkillAPT:
                    state.attributes["APT"] += self.standbyFinishSkillAPT
                    turn = nextTurn
                    self.standbyFinishSkillAPT = 0
                    state.attacksPerformed += 1
                    state.superAttacksPerformed += 1
                    self.states.append(state)
                else:  # Set this to True so apply APT in next turn (e.g. Buu Bois)
                    applyFinishSkillAPT = True
                    nextForm = -1
            else:
                form.numAttacksReceived += state.numAttacksReceived
                nextForm = form.checkConditions(
                    form.formChangeConditionOperator,
                    form.formChangeConditions,
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
        for i, state in enumerate(self.states):
            for j, attributeName in enumerate(ATTTRIBUTE_NAMES):
                state.attributes[attributeName] = attributes[i, j]

    def saveUnit(self):
        # Output the unit's attributes to a .txt file
        outputFilePath = os.path.join(CWD, "DokkanKitOutputs", HIPO_DUPES[self.nCopies - 1], self.id + ".txt")
        outputFile = open(outputFilePath, "w")
        for i, state in enumerate(self.states):
            outputFile.write(f"State # {i} / Turn # {state.turn} \n \n")
            for j, attributeName in enumerate(ATTTRIBUTE_NAMES):
                outputFile.write(f"{attributeName}: {state.attributes[attributeName]} \n")
            outputFile.write("\n")
        # Can't pickle this for some reason, but ok as only needed for inputting data.
        self.inputHelper.file = None
        with open(self.picklePath, "wb") as outp:  # Overwrites any existing file.
            pickle.dump(self, outp, pickle.HIGHEST_PROTOCOL)
        outp.close()


class Form:
    def __init__(self, inputHelper, initialTurn, rarity, eza, formIdx, numForms):
        self.inputHelper = inputHelper
        self.initialTurn = initialTurn
        self.rarity = rarity
        self.EZA = eza
        self.linkNames = [""] * MAX_NUM_LINKS
        self.linkCommonality = 0
        self.extraBuffs = dict(zip(EXTRA_BUFF_EFFECTS, [0] * len(EXTRA_BUFF_EFFECTS)))
        self.linkKi = 0
        self.linkAtkSoT = 0
        self.linkDef = 0
        self.linkCrit = 0
        self.linkAtkOnSuper = 0
        self.linkDodge = 0
        self.linkDmgRed = 0
        self.linkHealing = 0
        self.numAttacksReceived = 0  # Number of attacks received so far in this form.
        self.attacksPerformed = 0
        self.superAttacksPerformed = 0
        self.charge = 0
        self.superAttacks = {}  # Will be a list of SuperAttack objects
        # This will be a list of Ability objects which will be iterated through each state to call applyToState.
        self.abilities = dict(zip(PHASES, [[] for i in range(len(PHASES))]))
        self.formChangeConditionOperator = None
        self.transformed = False
        self.newForm = True
        self.formChangeConditions = [Condition()]
        self.slot = int(
            self.inputHelper.getAndSaveUserInput(f"Which slot is form # {formIdx} best suited for?", default=2)
        )
        self.canAttack = yesNo2Bool[self.inputHelper.getAndSaveUserInput("Can this form attack?", default="Y")]
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
        assert len(np.unique(self.linkNames)) == MAX_NUM_LINKS, "Duplicate links"
        self.getSuperAttacks(self.rarity, self.EZA)
        ################################################ Turn Start #####################################################
        self.abilities["Start of Turn"].extend(
            abilityQuestionaire(
                self,
                "How many unconditional buffs does the form have?",
                Buff,
            )
        )
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
        self.abilities["Start of Turn"].extend(
            abilityQuestionaire(
                self,
                "How many Domain skills does the form have?",
                Domain,
                [
                    "What is the Domain type?",
                    "How much is the effect?",
                    "What proportion does it effect?",
                    "How many turns does it last?"
                ],
                [clc.Choice(DOMAIN_TYPES), None, None, None],
                ["Increase Damage Received", 0.3, 0.5, 5],
            )
        )
        ############################################ Active / Finish Skills ###############################################
        self.abilities["Active / Finish Skills"].extend(
            abilityQuestionaire(
                self,
                "How many active skill attacks does the form have?",
                ActiveSkillAttack,
                [
                    "What is the attack multiplier?",
                    "What is the additional attack buff when performing the attack?",
                ],
                [clc.Choice(SPECIAL_ATTACK_MULTIPLIER_NAMES, case_sensitive=False), None],
                ["Ultimate", 0.0],
            )
        )
        self.abilities["Active / Finish Skills"].extend(
            abilityQuestionaire(
                self,
                "How many active skill buffs does the form have?",
                ActiveSkillBuff,
            )
        )
        self.abilities["Active / Finish Skills"].extend(
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
        ############################################## Collect Ki ##################################################
        self.abilities["Collect Ki"].extend(
            abilityQuestionaire(
                self,
                "How many ki sphere dependent buffs does the form have?",
                KiSphereDependent,
                [
                    "What type of ki spheres are required?",
                    "What is the required amount?",
                    "Is buff applied when attacking?",
                ],
                [clc.Choice(ORB_REQUIREMENTS), None, clc.Choice(YES_NO)],
                ["Any", 0, "N"],
            )
        )
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
        self.abilities["Receive Attacks"].extend(
            abilityQuestionaire(
                self,
                "How many different buffs does the form get after receiving an attack?",
                AfterAttackReceived,
            )
        )
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
        ############################################## Attack Enemy ##################################################
        self.abilities["Attack Enemy"].extend(
            abilityQuestionaire(
                self,
                "How many different buffs does the form get when performing a super attack?",
                PerformingSuperAttack,
            )
        )
        self.abilities["Attack Enemy"].extend(
            abilityQuestionaire(
                self,
                "How many different buffs does the form get per attack performed?",
                PerAttackPerformed,
                ["What is the maximum buff?"],
                [None],
                [1.0],
            )
        )
        self.abilities["Attack Enemy"].extend(
            abilityQuestionaire(
                self,
                "How many different buffs does the form get per super attack performed?",
                PerSuperAttackPerformed,
                ["What is the maximum buff?"],
                [None],
                [1.0],
            )
        )
        self.abilities["Attack Enemy"].extend(
            abilityQuestionaire(
                self,
                "How many different nullification abilities does the form have?",
                Nullification,
                ["Does this nullification have counter?"],
                [clc.Choice(YES_NO)],
                ["N"],
            )
        )
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
        self.formChangeConditionOperator, self.formChangeConditions = getConditions(self.inputHelper)
        if formIdx < numForms:
            self.newForm = True
        else:
            self.newForm = False

    def getLinks(self):
        for linkIndex in range(MAX_NUM_LINKS):
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
            self.linkCommonality += link.commonality
            self.linkKi += link.ki
            self.linkAtkSoT += link.atkSoT
            self.linkDef += link.defence
            self.linkCrit += link.crit
            self.linkAtkOnSuper += link.atkOnSuper
            self.linkDodge += link.dodge
            self.linkDmgRed += link.dmgRed
            self.linkHealing += link.healing
        self.linkCommonality /= MAX_NUM_LINKS

    def getSuperAttacks(self, rarity, eza):
        for superAttackType in SUPER_ATTACK_CATEGORIES:
            if superAttackType == "12 Ki" or (rarity == "LR" and not (self.intentional12Ki)):
                multiplier = superAttackConversion[
                    self.inputHelper.getAndSaveUserInput(
                        f"What is the form's {superAttackType} super attack multiplier?",
                        type=clc.Choice(SUPER_ATTACK_MULTIPLIER_NAMES, case_sensitive=False),
                        default=DEFAULT_SUPER_ATTACK_MULTIPLIER_NAMES[superAttackType],
                    )
                ][superAttackLevelConversion[rarity][eza]]
                avgSuperAttack = SuperAttack(superAttackType, multiplier)
                numSuperAttacks = self.inputHelper.getAndSaveUserInput(
                    f"How many different {superAttackType} super attacks does this form have?",
                    default=1,
                )
                superFracTotal = 0
                for i in range(numSuperAttacks):
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
                    for j in range(numEffects):
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
                            "How many turns does it last for?", default=MAX_TURN
                        )
                        avgSuperAttack.addEffect(effectType, activationProbability, buff, duration, superFrac)
                    superFracTotal += superFrac
                assert superFracTotal == 1, "Invald super attack variant probabilities entered"
            self.superAttacks[superAttackType] = avgSuperAttack

    def checkConditions(self, operator, conditions, activated, newForm):
        if activated:
            nextForm = 0
        elif len(conditions[0]) == 0:
            nextForm = 1
        elif len(operator) == 3:
            operator, operatorA, operatorB = operator
            conditionsA, conditionsB = conditions
            A = self.checkConditions([operatorA], [conditionsA], activated, newForm)
            B = self.checkConditions([operatorB], [conditionsB], activated, newForm)
            match operator:
                case "AND":
                    if A == B:
                        return A
                    else:
                        return 0
                case "OR":
                    if A != 0:
                        return A
                    else:
                        return B
        else:
            operator = operator[0]
            conditions = conditions[0]
            match operator:
                case None:
                    result = conditions[0].isSatisfied(self)
                case "AND":
                    result = np.all([condition.isSatisfied(self) for condition in conditions])
                case "OR":
                    result = np.any([condition.isSatisfied(self) for condition in conditions])
                case "NOT":
                    result = False
                case "AFTER":
                    conditions[0].conditionValue += conditions[1].conditionValue
                    result = conditions[0].isSatisfied(self)
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


class Link:
    def __init__(self, name, commonality):
        self.name = name
        i = LINK_NAMES.index(self.name)
        self.ki = float(LINK_DATA[i, 10])
        self.atkSoT = float(LINK_DATA[i, 11])
        self.defence = float(LINK_DATA[i, 12])
        self.atkOnSuper = float(LINK_DATA[i, 13])
        self.crit = float(LINK_DATA[i, 14])
        self.dmgRed = float(LINK_DATA[i, 15])
        self.dodge = float(LINK_DATA[i, 16])
        self.healing = float(LINK_DATA[i, 17])
        if commonality == -1:
            self.commonality = float(LINK_DATA[i, 9])
        else:
            self.commonality = float(commonality)


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
            "Ki": LEADER_SKILL_KI + form.extraBuffs["Ki"],
            "AEAAT": 0,
            "Guard": 0,
            "Crit": unit.pHiPoCrit
            + (1 - unit.pHiPoCrit) * (form.linkCrit + (1 - form.linkCrit) * form.extraBuffs["Crit"]),
            "Disable Guard": 0,
            "Evade": unit.pHiPoDodge + (1 - unit.pHiPoDodge) * form.linkDodge,
            "Dmg Red against Normals": form.extraBuffs["Dmg Red"],
        }
        self.p1Buff = {"ATK": ATK_DEF_SUPPORT, "DEF": ATK_DEF_SUPPORT}
        self.p2Buff = {"ATK": form.linkAtkOnSuper + form.extraBuffs["ATK"], "DEF": form.extraBuffs["DEF"]}
        self.p3Buff = {"ATK": 0, "DEF": 0}
        self.kiPerOtherTypeOrb = 1
        self.kiPerSameTypeOrb = KI_PER_SAME_TYPE_ORB
        self.kiPerRainbowKiSphere = 1  # Ki per orb
        self.numRainbowOrbs = orbChangeConversion["No Orb Change"]["Rainbow"]
        self.numOtherTypeOrbs = orbChangeConversion["No Orb Change"]["Other"]
        self.numSameTypeOrbs = orbChangeConversion["No Orb Change"]["Same"]
        self.p2DefA = 0
        self.p2DefB = 0
        self.healing = 0  # Fraction of health healed every turn
        self.support = 0  # Support score
        self.pNullify = 0  # Probability of nullifying all enemy super attacks
        self.aaPSuper = []  # Probabilities of doing additional super attacks and guaranteed additionals
        self.aaPGuarantee = []
        self.dmgRedA = form.extraBuffs["Dmg Red"]
        self.dmgRedB = form.extraBuffs["Dmg Red"]
        self.pCounterSA = 0  # Probability of countering an enemy super attack
        # Initialising these here, but will need to be updated everytime self.buff["Evade"] is increased, best to make a function to update evade
        self.numAttacksReceived = NUM_ATTACKS_DIRECTED[self.slot - 1] * (1 - self.buff["Evade"])
        self.numAttacksReceivedBeforeAttacking = NUM_ATTACKS_DIRECTED_BEFORE_ATTACKING[self.slot - 1] * (
            1 - self.buff["Evade"]
        )
        self.attacksPerformed = 0
        self.superAttacksPerformed = 0
        # Required for getting APTs for individual attacks
        self.atkPerAttackPerformed = np.zeros(MAX_TURN)
        self.atkPerSuperPerformed = np.zeros(MAX_TURN)
        self.critPerAttackPerformed = np.zeros(MAX_TURN)
        self.critPerSuperPerformed = np.zeros(MAX_TURN)
        self.APT = 0
        self.stackedStats = dict(zip(STACK_EFFECTS, np.zeros(len(STACK_EFFECTS))))

    def setState(self, unit, form):
        for ability in form.abilities["Start of Turn"]:
            ability.applyToState(self, unit, form)
        self.pNullify = self.pNullify + (1 - self.pNullify) * self.pCounterSA
        self.atkModifier = self.getAvgAtkMod(form, unit)

        for ability in form.abilities["Active / Finish Skills"]:
            ability.applyToState(self, unit, form)

        for ability in form.abilities["Collect Ki"]:
            ability.applyToState(self, unit, form)

        for ability in form.abilities["Receive Attacks"]:
            ability.applyToState(self, unit, form)
        self.atkModifier = self.getAvgAtkMod(form, unit)
        self.p2Buff["DEF"] = self.p2DefA + self.p2DefB
        self.ki = min(round(self.buff["Ki"] + self.randomKi), rarity2MaxKi[unit.rarity])
        self.pN, self.pSA, self.pUSA = getAttackDistribution(
            self.buff["Ki"], self.randomKi, form.intentional12Ki, unit.rarity
        )
        self.aaSA = branchAS(-1, len(self.aaPSuper), unit.pHiPoAA, 1, self.aaPSuper, self.aaPGuarantee, unit.pHiPoAA)
        self.aa = branchAA(-1, len(self.aaPSuper), unit.pHiPoAA, 1, self.aaPSuper, self.aaPGuarantee, unit.pHiPoAA)
        pAttack = 1 - PROBABILITY_KILL_ENEMY_BEFORE_ATTACKING[self.slot - 1]
        pNextAttack = pAttack - PROBABILITY_KILL_ENEMY_PER_ATTACK
        self.attacksPerformed += pAttack + self.aa * pNextAttack
        # Assume Binomial distribution for aaSA for the expected value
        self.superAttacksPerformed += pAttack + self.aaSA * pNextAttack
        form.attacksPerformed += self.attacksPerformed
        form.superAttacksPerformed += self.superAttacksPerformed
        self.updateStackedStats(form, unit)
        # Compute support bonuses from super attack effects
        for superAttackType in SUPER_ATTACK_CATEGORIES:
            if superAttackType == "18 Ki":
                numSupers = pAttack * self.pUSA
            else:
                numSupers = pAttack * self.pSA + self.aaSA * pNextAttack
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
            self.pNullify += (
                (1 - self.pNullify)
                * numSupers
                * P_NULLIFY_FROM_DISABLE
                * form.superAttacks[superAttackType].effects["Disable Action"].buff
            )

        for ability in form.abilities["Attack Enemy"]:
            ability.applyToState(self, unit, form)
        self.normal = getNormal(
            unit.kiMod12,
            self.ki,
            unit.ATK,
            self.p1Buff["ATK"],
            self.stackedStats["ATK"],
            form.linkAtkSoT,
            self.p2Buff["ATK"],
            self.p3Buff["ATK"],
        )
        self.sa = getSA(
            unit.kiMod12,
            unit.ATK,
            self.p1Buff["ATK"],
            self.stackedStats["ATK"],
            form.linkAtkSoT,
            self.p2Buff["ATK"],
            self.p3Buff["ATK"],
            form.superAttacks["12 Ki"].multiplier,
            unit.nCopies,
            form.superAttacks["12 Ki"].effects["ATK"].duration,
            form.superAttacks["12 Ki"].effects["ATK"].buff,
        )
        self.usa = getUSA(
            unit.kiMod12,
            self.ki,
            unit.ATK,
            self.p1Buff["ATK"],
            self.stackedStats["ATK"],
            form.linkAtkSoT,
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
            form.superAttacks["12 Ki"].effects["ATK"].duration,
            form.superAttacks["12 Ki"].effects["ATK"].buff,
            form.superAttacks["18 Ki"].effects["ATK"].buff,
            self.stackedStats["ATK"],
            self.p1Buff["ATK"],
            self.p2Buff["ATK"],
            self.normal,
            self.sa,
            self.usa,
            unit.pHiPoAA,
            self.aaPGuarantee,
            self.pCounterSA,
            form.normalCounterMult,
            form.saCounterMult,
            self.pN,
            self.pSA,
            self.pUSA,
            unit.rarity,
            self.slot,
            form.canAttack,
            self.buff["Crit"],
            unit.critMultiplier,
            self.atkModifier,
            self.atkPerAttackPerformed,
            self.atkPerSuperPerformed,
            self.critPerAttackPerformed,
            self.critPerSuperPerformed,
            form.superAttacks["12 Ki"].effects["Crit"].buff,
            form.superAttacks["18 Ki"].effects["Crit"].buff,
        )
        self.getAvgDefMult(form, unit)
        avgDefStartOfTurn = getDefStat(
            unit.DEF,
            self.p1Buff["DEF"],
            form.linkDef,
            form.extraBuffs["DEF"],
            self.p3Buff["DEF"],
            self.stackedStats["DEF"],
        )
        self.avgDefPreSuper = getDefStat(
            unit.DEF, self.p1Buff["DEF"], form.linkDef, self.p2DefA, self.p3Buff["DEF"], self.stackedStats["DEF"]
        )
        self.avgDefPostSuper = getDefStat(
            unit.DEF, self.p1Buff["DEF"], form.linkDef, self.p2Buff["DEF"], self.p3Buff["DEF"], self.avgDefMult
        )
        self.normalDamageTakenPreSuper = getDamageTaken(
            self.buff["Evade"],
            self.buff["Guard"],
            MAX_NORMAL_DAM_PER_TURN[self.turn - 1],
            unit.TDB,
            self.buff["Dmg Red against Normals"],
            self.avgDefPreSuper,
        )
        self.normalDamageTakenPostSuper = getDamageTaken(
            self.buff["Evade"],
            self.buff["Guard"],
            MAX_NORMAL_DAM_PER_TURN[self.turn - 1],
            unit.TDB,
            self.buff["Dmg Red against Normals"],
            self.avgDefPostSuper,
        )
        self.saDamageTakenPreSuper = getDamageTaken(
            self.buff["Evade"],
            self.buff["Guard"],
            MAX_SA_DAM_PER_TURN[self.turn - 1],
            unit.TDB,
            self.dmgRedA,
            self.avgDefPreSuper,
        )
        self.saDamageTakenPostSuper = getDamageTaken(
            self.buff["Evade"],
            self.buff["Guard"],
            MAX_SA_DAM_PER_TURN[self.turn - 1],
            unit.TDB,
            self.dmgRedB,
            self.avgDefPostSuper,
        )
        self.healing += (
            form.linkHealing
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
            unit.teams / NUM_TEAMS_MAX * (1 + USEABILITY_SUPPORT_FACTOR * self.support + form.linkCommonality)
        )
        attributeValues = [
            unit.leaderSkill,
            unit.SBR,
            unit.HP,
            self.useability,  # Requires user input, should make a version that loads from file
            self.healing,
            self.support,
            self.APT,
            self.normalDamageTaken,
            self.saDamageTaken,
            self.slotFactor,
        ]
        self.attributes = dict(zip(ATTTRIBUTE_NAMES, attributeValues))

    def updateStackedStats(self, form, unit):
        # Needs to do two things, remove stacked attack from previous states if worn out and apply new buffs
        # If want the stacking of initial turn and transform later
        for stat in STACK_EFFECTS:
            # Update previous stack durations
            for stack in unit.stacks[stat]:
                stack.duration -= RETURN_PERIOD_PER_SLOT[unit.states[-1].slot - 1]
            # Remove them if expired
            unit.stacks[stat] = [stack for stack in unit.stacks[stat] if stack.duration > 0]
            # Apply stacks
            for stack in unit.stacks[stat]:
                self.stackedStats[stat] += stack.buff
            # Add new stacks. Has to be after apply otherwise will double count the stacks in each turn
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
                        (self.pSA + self.aaSA) * form.superAttacks["12 Ki"].effects[stat].buff,
                        form.superAttacks["12 Ki"].effects[stat].duration,
                    )
                )

    def getAvgDefMult(self, form, unit):
        self.avgDefMult = (
            self.stackedStats["DEF"] + (self.pSA + self.aaSA) * form.superAttacks["12 Ki"].effects["DEF"].buff
        )
        if unit.rarity == "LR":  # If unit is a LR
            self.avgDefMult += self.pUSA * form.superAttacks["18 Ki"].effects["DEF"].buff

    def getAvgAtkMod(self, form, unit):
        return self.buff["Crit"] * unit.critMultiplier + (1 - self.buff["Crit"]) * (
            self.buff["AEAAT"] * (AEAAT_MULTIPLIER + unit.TAB * AEAAT_TAB_INC)
            + (1 - self.buff["AEAAT"])
            * (
                self.buff["Disable Guard"] * (DISABLE_GUARD_MULTIPLIER + unit.TAB * DISABLE_GUARD_TAB_INC)
                + (1 - self.buff["Disable Guard"]) * (AVG_TYPE_ADVANATGE + unit.TAB * DEFAULT_TAB_INC)
            )
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
        self.operator, self.conditions = getConditions(form.inputHelper)
        self.activated = False


class GiantRageMode(SingleTurnAbility):
    def __init__(self, form, args):
        super().__init__(form)
        self.ATK = args[0]
        self.support = GIANT_RAGE_SUPPORT
        slot = 1  # Arbitarary choice, could also be 2 or 3
        # Create a form so can get access to abilityQuestionaire to ask user questions
        self.giantRageForm = Form(form.inputHelper, slot)
        self.giantRageForm.abilities.extend(
            abilityQuestionaire(
                self.giantRageForm,
                "How many buffs does this giant/rage mode have?",
                Buff,
            )
        )

    def applyToState(self, state, unit=None, form=None):
        if form.checkConditions(self.operator, self.conditions, self.activated, True) and unit.fightPeak:
            self.activated = True
            # Create a State so can get access to setState for damage calc
            self.giantRageModeState = State(unit, form, state.slot, state.turn)
            for ability in self.giantRageForm.abilities:  # Apply the giant/form abilities
                ability.applyToState(self.giantRageModeState)
            giantRageUnit = copy(unit)
            giantRageUnit.ATK = self.ATK
            self.giantRageModeState.setState(self.giantRageForm, giantRageUnit)  # Calculate the APT of the state
            state.APT += self.giantRageModeState.APT * NUM_SLOTS * giantRageUnit.giantRageDuration
            state.support += self.support


class Revive(SingleTurnAbility):
    def __init__(self, form, args):
        super().__init__(form)
        self.hpRegen, self.isThisCharacterOnly = args
        self.abilities = abilityQuestionaire(
            form, "How many additional constant buffs does this revive have?", Buff
        )

    def applyToState(self, state, unit=None, form=None):
        if form.checkConditions(self.operator, self.conditions, self.activated, True) and unit.fightPeak:
            self.activated = True
            state.healing = min(state.healing + self.hpRegen, 1)
            if self.isThisCharacterOnly:
                state.support += REVIVE_UNIT_SUPPORT_BUFF
            else:
                state.support += REVIVE_ROTATION_SUPPORT_BUFF
            form.abilities["Start of Turn"].extend(self.abilities)


class Domain(SingleTurnAbility):
    def __init__(self, form, args):
        super().__init__(form)
        self.domainType, buff, prop, self.duration  = args
        self.effectiveBuff = buff * aprioriProbMod(prop, True)
        self.abilities = abilityQuestionaire(form, "How many additional buffs are there when this Domain is active?", TurnDependent)

    def applyToState(self, state, unit=None, form=None):
        if form.checkConditions(self.operator, self.conditions, self.activated, True):
            self.activated = True
            start = state.turn
            end = start + self.duration - 1
            params = [start, end]
            match self.domainType:
                case "Increase Damage Received":
                    self.abilities.append(TurnDependent(form, 1, False, "ATK Support", self.effectiveBuff * AVG_SOT_STATS, 1, params))
                    self.abilities.append(TurnDependent(form, 1, False, "P3 ATK", self.effectiveBuff, 1, params))
            form.abilities["Start of Turn"].extend(self.abilities)


class ActiveSkillBuff(SingleTurnAbility):
    def __init__(self, form, args=[]):
        super().__init__(form)
        self.abilities = abilityQuestionaire(form, "How many different buffs does the active skill have?", Buff)

    def applyToState(self, state, unit=None, form=None):
        if form.checkConditions(self.operator, self.conditions, False, True) and unit.fightPeak:
            for ability in self.abilities:
                ability.end = state.turn + ability.effectDuration
                ability.applyToState(state, unit, form)


class ActiveSkillAttack(SingleTurnAbility):
    def __init__(self, form, args):
        super().__init__(form)
        attackMultiplier, attackBuff = args
        self.activeMult = specialAttackConversion[attackMultiplier] + attackBuff

    def applyToState(self, state, unit=None, form=None):
        if form.checkConditions(self.operator, self.conditions, self.activated, True) and unit.fightPeak:
            self.activated = True
            state.attacksPerformed += 1  # Parameter should be used to determine buffs from per attack performed buffs
            state.superAttacksPerformed += 1
            state.APT += (
                getActiveAtk(
                    unit.kiMod12,
                    rarity2MaxKi[unit.rarity],
                    unit.ATK,
                    state.p1Buff["ATK"],
                    state.stackedStats["ATK"],
                    self.form.linkAtkSoT,
                    state.p2Buff["ATK"],
                    state.p3Buff["ATK"],
                    self.activeMult,
                    unit.nCopies,
                )
                * state.atkModifier
            )


# This skill is to apply to a unit already in it's standby mode.
# The condition to enter & exit the standy mode will be controlled by regular form changes.
class StandbyFinishSkill(SingleTurnAbility):
    def __init__(self, form, args):
        super().__init__(form)
        self.finishSkillChargeCondition, attackMultiplier, self.attackBuff, self.buffPerCharge = args
        self.activeMult = specialAttackConversion[attackMultiplier]

    def applyToState(self, state, unit=None, form=None):
        form.charge += form.getCharge(self.finishSkillChargeCondition)
        if form.checkConditions(self.operator, self.conditions, self.activated, True):
            self.activated = True
            self.activeMult += self.buffPerCharge * form.charge
            unit.standbyFinishSkillAPT = (
                getActiveAtk(
                    unit.kiMod12,
                    rarity2MaxKi[unit.rarity],
                    unit.ATK,
                    state.p1Buff["ATK"],
                    state.stackedStats["ATK"],
                    self.form.linkAtkSoT,
                    state.p2Buff["ATK"],
                    state.p3Buff["ATK"],
                    self.activeMult * (1 + self.attackBuff),
                    unit.nCopies,
                )
                * state.atkModifier
            )


class RevivalCounterFinishSkill(StandbyFinishSkill):
    def __init__(self, form, args):
        args = ["Revive"] + args + [0]
        super().__init__(form, args)


class PassiveAbility(Ability):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, effectDuration):
        super().__init__(form)
        self.activationProbability = aprioriProbMod(activationProbability, knownApriori)
        self.effect = effect
        self.effectDuration = effectDuration
        self.effectiveBuff = buff * self.activationProbability


class Buff(PassiveAbility):
    def __init__(
        self,
        form,
        activationProbability,
        knownApriori,
        effect,
        buff,
        effectDuration,
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
        self.effectiveBuff = buff * activationProbability

    def applyToState(self, state, unit=None, form=None):
        # Need to update in case one of the relevant variables has been updated
        state.randomKi = (
            KI_SUPPORT
            + state.kiPerOtherTypeOrb * state.numOtherTypeOrbs
            + state.kiPerSameTypeOrb * state.numSameTypeOrbs
            + state.kiPerOtherTypeOrb * state.numRainbowOrbs
            + form.linkKi
        )
        pHaveKi = 1 - ZTP_CDF(self.ki - 1 - state.buff["Ki"], state.randomKi)
        effectiveBuff = self.effectiveBuff * pHaveKi * min(self.effectDuration, RETURN_PERIOD_PER_SLOT[state.slot - 1])
        activationProbability = self.activationProbability * pHaveKi
        # Check if state is elligible for ability
        if state.turn >= self.start and state.turn <= self.end and state.slot in self.slots:
            # If a support ability
            if self.effect in REGULAR_SUPPORT_EFFECTS:
                state.support += supportFactorConversion[self.effect] * effectiveBuff
            elif self.effect in ORB_CHANGING_EFFECTS:
                state.support += supportFactorConversion[self.effect] * effectiveBuff
                state.numOtherTypeOrbs = orbChangeConversion[self.effect]["Other"]
                state.numSameTypeOrbs = orbChangeConversion[self.effect]["Same"]
                state.numRainbowOrbs = orbChangeConversion[self.effect]["Rainbow"]
            elif self.effect in state.buff.keys():
                state.buff[self.effect] += effectiveBuff
            elif self.effect in state.p1Buff.keys():
                state.p1Buff[self.effect] += effectiveBuff
            else:  # Edge cases
                match self.effect:
                    case "Dmg Red":
                        state.dmgRedA += effectiveBuff
                        state.dmgRedB += effectiveBuff
                        state.buff["Dmg Red against Normals"] += effectiveBuff
                    case "Disable Action":
                        state.pNullify = (
                            P_NULLIFY_FROM_DISABLE * (1 - state.pNullify)
                            + (1 - P_NULLIFY_FROM_DISABLE) * state.pNullify
                        )
                    case "AdditionalSuper":
                        state.aaPSuper.append(activationProbability)
                        state.aaPGuarantee.append(0)
                    case "AAChance":
                        state.aaPGuarantee.append(activationProbability)
                    case "SuperChance":
                        state.aaPSuper.append(activationProbability)
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
                    case "P3 ATK":
                        state.p3Buff["ATK"] += effectiveBuff


class TurnDependent(Buff):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, effectDuration, args):
        start, end = args
        super().__init__(form, activationProbability, knownApriori, effect, buff, effectDuration, start=start, end=end)


class KiDependent(Buff):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, effectDuration, args):
        ki = args[0]
        super().__init__(form, activationProbability, knownApriori, effect, buff, effectDuration, ki=ki)


class SlotDependent(Buff):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, effectDuration, args):
        slots = args[0]
        super().__init__(form, activationProbability, knownApriori, effect, buff, effectDuration, slots=slots)


class HealthDependent(Buff):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, effectDuration, args):
        health, isMaxHpCondition = args
        p = maxHealthCDF(health)
        if yesNo2Bool[isMaxHpCondition]:
            activationProbability *= p
        else:
            activationProbability *= 1 - p
        super().__init__(form, activationProbability, True, effect, buff, effectDuration)


class PerEvent(PassiveAbility):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, effectDuration, max):
        super().__init__(form, activationProbability, knownApriori, effect, buff, effectDuration)
        self.max = max
        self.applied = 0


class PerAttackPerformed(PerEvent):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, effectDuration, args):
        super().__init__(form, activationProbability, knownApriori, effect, buff, effectDuration, args[0])

    def applyToState(self, state, unit=None, form=None):
        buffPerAttack = self.effectiveBuff * (np.arange(len(state.aaPSuper) + 1) + 1)
        turnBuff = self.effectiveBuff * state.attacksPerformed
        buffToGo = self.max - self.applied
        cappedTurnBuff = min(buffToGo, turnBuff)
        form.extraBuffs[self.effect] += cappedTurnBuff
        cappedBuffPerAttack = np.minimum(buffPerAttack, buffToGo)
        match self.effect:
            case "ATK":
                state.atkPerAttackPerformed = cappedBuffPerAttack
                state.atkPerSuperPerformed = state.atkPerAttackPerformed[:]
            case "DEF":
                state.p2DefB += cappedTurnBuff
            case "Crit":
                state.critPerAttackPerformed = cappedBuffPerAttack
                state.critPerSuperPerformed = state.critPerAttackPerformed[:]
        self.applied += cappedTurnBuff


class PerSuperAttackPerformed(PerEvent):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, effectDuration, args):
        super().__init__(form, activationProbability, knownApriori, effect, buff, effectDuration, args[0])

    def applyToState(self, state, unit=None, form=None):
        buffPerSuper = self.effectiveBuff * (np.arange(len(state.aaPSuper) + 1) + 1)
        turnBuff = self.effectiveBuff * state.superAttacksPerformed
        buffToGo = self.max - self.applied
        cappedTurnBuff = min(buffToGo, turnBuff)
        form.extraBuffs[self.effect] += cappedTurnBuff
        cappedBuffPerSuper = np.minimum(buffPerSuper, buffToGo)
        match self.effect:
            case "ATK":
                state.atkPerAttackPerformed = cappedBuffPerSuper
            case "DEF":
                state.p2DefB += cappedTurnBuff
            case "Crit":
                state.critPerAttackPerformed = cappedBuffPerSuper
            case "Dmg Red":
                state.dmgRedB += cappedTurnBuff
                state.buff["Dmg Red against Normals"] += cappedTurnBuff
        self.applied += cappedTurnBuff


class PerAttackReceived(PerEvent):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, effectDuration, args):
        super().__init__(form, activationProbability, knownApriori, effect, buff, effectDuration, args[0])

    def applyToState(self, state, unit=None, form=None):
        turnBuff = self.effectiveBuff * state.numAttacksReceived
        buffToGo = self.max - self.applied
        cappedTurnBuff = min(buffToGo, turnBuff)
        form.extraBuffs[self.effect] += cappedTurnBuff
        match self.effect:
            case "Ki":
                state.buff["Ki"] += min(self.effectiveBuff * state.numAttacksReceivedBeforeAttacking, buffToGo)
            case "ATK":
                state.p2Buff["ATK"] += min(self.effectiveBuff * state.numAttacksReceivedBeforeAttacking, buffToGo)
            case "DEF":
                state.p2DefA += min((state.numAttacksReceived - 1) * self.effectiveBuff / 2, buffToGo)
        self.applied += cappedTurnBuff


class AfterAttackReceived(PassiveAbility):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, effectDuration, args=[]):
        super().__init__(form, activationProbability, knownApriori, effect, buff, effectDuration)
        self.turnsSinceActivated = 0
        self.applied = 0
        self.hitFactor = 1

    def applyToState(self, state, unit=None, form=None):
        if self.turnsSinceActivated == 0:
            if self.applied > 0:
                form.extraBuffs[self.effect] -= self.applied
                self.applied = 0
            # If buff is a defensive one
            if self.effect in ["DEF", "Dmg Red"]:
                self.hitFactor = (
                    state.numAttacksReceived - 1
                ) / state.numAttacksReceived  # Factor to account for not having the buff on the fist hit
            else:
                self.hitFactor = min(state.numAttacksReceivedBeforeAttacking, 1)
        # geometric cdf
        turnBuff = self.effectiveBuff * self.hitFactor
        buffToGo = self.effectiveBuff - self.applied
        cappedTurnBuff = min(buffToGo, turnBuff)
        if self.effect in state.buff.keys():
            state.buff[self.effect] += cappedTurnBuff
        else:
            match self.effect:
                case "DEF":
                    state.p2DefA += cappedTurnBuff
                # These addiotnal super abilities won't be applied correctly if self.effectDuration > 2.
                case "AdditionalSuper":
                    state.aaPSuper.append(cappedTurnBuff)
                    state.aaPGuarantee.append(0)
                case "AAChance":
                    state.aaPGuarantee.append(cappedTurnBuff)
                case "SuperChance":
                    state.aaPSuper.append(cappedTurnBuff)
        self.turnsSinceActivated += 1
        # If not still going to be active next turn
        if self.effectDuration < self.turnsSinceActivated * RETURN_PERIOD_PER_SLOT[state.slot]:
            # Reset it to not be active
            self.turnsSinceActivated = 0
        else:
            form.extraBuffs[self.effect] += cappedTurnBuff
            self.applied += cappedTurnBuff
            self.hitFactor = 1


class PerformingSuperAttack(PassiveAbility):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, effectDuration, args=[]):
        super().__init__(form, activationProbability, knownApriori, effect, buff, effectDuration)

    def applyToState(self, state, unit=None, form=None):
        match self.effect:
            case "ATK":
                state.p2Buff["ATK"] = self.effectiveBuff
            case "DEF":
                state.p2DefB += self.effectiveBuff


class KiSphereDependent(PassiveAbility):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, effectDuration, args):
        super().__init__(form, activationProbability, knownApriori, effect, buff, effectDuration)
        self.orbType, self.required, self.whenAttacking = args

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
        buffFromOrbs = self.effectiveBuff * effectFactor
        if self.effect in state.buff.keys():
            state.buff[self.effect] += buffFromOrbs
        else:
            match self.effect:
                case "Dmg Red":
                    state.dmgRedA += buffFromOrbs
                    state.dmgRedB += buffFromOrbs
                    state.buff["Dmg Red against Normals"] += buffFromOrbs


class Nullification(PassiveAbility):
    def __init__(self, form, activationProbability, knownApriori, effect, buff, effectDuration, args):
        super().__init__(form, activationProbability, knownApriori, effect, buff, effectDuration)
        self.hasCounter = args[0]

    def applyToState(self, state, unit=None, form=None):
        pNullify = self.activationProbability * aprioriProbMod(saFracConversion[self.effect], True)
        state.pNullify = (1 - state.pNullify) * pNullify + (1 - pNullify) * state.pNullify
        if yesNo2Bool[self.hasCounter]:
            state.pCounterSA = (1 - state.pCounterSA) * pNullify + (1 - pNullify) * state.pCounterSA


class Condition:
    def __init__(self):
        # Just a default attributes so is always false upon itialisation
        self.formAttr = "numAttacksReceived"
        self.conditionValue = LARGE_INT

    def isSatisfied(self, form):
        return getattr(form, self.formAttr) >= self.conditionValue


class TurnCondition(Condition):
    def __init__(self, turnCondition):
        self.conditionValue = turnCondition
        self.formAttr = "nextTurnRelative"


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


class AttacksPerformedCondition(Condition):
    def __init__(self, numAttacks):
        self.formAttr = "attacksPerformed"
        self.conditionValue = numAttacks


class AttacksReceivedCondition(Condition):
    def __init__(self, numAttacks):
        self.formAttr = "numAttacksReceived"
        self.conditionValue = numAttacks


class FinishSkillActivatedCondition(Condition):
    def __init__(self, requiredCharge):
        self.formAttr = "charge"
        self.conditionValue = requiredCharge


# Too niche to conform to a generalised case because there is no formAttr for the charge condtion
class DoubleSameRainbowKiSphereCondition(Condition):
    def __init__(self, chargeCondition):
        self.conditionValue = chargeCondition
        self.currentValue = 0

    def isSatisfied(self, form):
        # NB: this line only works because the chargeCondition does not rely on form.attacksPerformed as that value will increase per turn, wheras here we are assuming the getCharge in constant
        self.currentValue += form.getCharge(self.conditionValue)
        return self.currentValue >= self.conditionValue


if __name__ == "__main__":
    # InputModes = {manual, fromTxt, fromPickle, fromWeb}
    unit = Unit(5, 1, "DEF", "ADD", "DGE", inputMode="fromTxt")
    
