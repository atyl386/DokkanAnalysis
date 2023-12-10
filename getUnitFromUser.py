import datetime as dt
from dokkanUnitHelperFunctions import *
import copy
import pickle

# TODO:
# - Bug with random ki being too high for golden bois
# - Need to make new ability class "PerSuperAttackPerformed"
# - It might make sense to factor out the big if statemnet in the StartOfTurn class so it can apply to P3 buffs too. Then it wouldn't look so weird for ActiveSkillBuff to call StartOfTurn and instead could just call that new function.
# - Previously I was determining the single turn ability turns before applying to State so could use turnDependent Class to apply single turn buffs.
# - i.e. will just have to determine the form start and end turns once at a time within the form for loop, and assert at the end that the numFomrs given by the user matches the number found by the endTurn determinations
# - Add some functionality that can update existing input .txt files with new questions (assuming not relevant to exisiting unit)
# - Need to incorporate standby skills
# - Whenever I update Evasion change in abilities, I need to reocompute evasion chance using self.buff["Evade"] = self.buff["Evade"] + (1 - self.buff["Evade"]) * (unit.pHiPoDodge + (1 - unit.pHiPoDodge) * form.linkDodge)
# - It would be awesome if after I have read in a unit I could reconstruct the passive description to compare it against the game
# - Instead of asking user how many of something, should ask until they enteran exit key aka while loop instead of for loop
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
            buff = form.inputHelper.getAndSaveUserInput("What is the value of the buff?", default=1.0)
            effectDuration = form.inputHelper.getAndSaveUserInput(
                "How many turns does it last for? Only applicable to abilities with a time limit.", default=1
            )
            ability = abilityClass(form, activationProbability, effect, buff, effectDuration, args=parameters)
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
    operator = None
    if numConditions > 1:
        operator = inputHelper.getAndSaveUserInput(
            "Are the condtions ORs or ANDs?", type=clc.Choice(OR_AND), default="AND"
        )
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
            case "Num Attacks":
                numAttacksCondition = inputHelper.getAndSaveUserInput("How many attacks are required?", default=6)
                conditions[i] = NumAttacksCondition(numAttacksCondition)
            case "Finish Skill Activated":
                conditions[i] = FinishSkillActivatedCondition()
            case "x2 same / rainbow or x1 other":  # LR INT Majuub -> SFPS4 Goku
                chargeCondition = inputHelper.getAndSaveUserInput("What is the maximum charge condition?", default=30)
                conditions[i] = DoubleSameRainbowKiSphereCondition(chargeCondition)

    return operator, conditions


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
    def __init__(self, id, nCopies, brz, HiPo1, HiPo2, inputMode=False):
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
                    default="0",
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
                self.inputHelper.self.inputHelper.getAndSaveUserInput(
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
                    default="None",
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
        self.finishSkillActivated = False
        nextForm = True
        while turn <= MAX_TURN:
            if nextForm:
                formIdx += 1
                # If finish stanby phase with a finish skill attack, go back to previous form.
                if self.finishSkillActivated:
                    form = self.forms[-2]
                else:
                    form = Form(self.inputHelper, turn, self.rarity, self.EZA, formIdx, self.numForms)
                    self.forms.append(form)
                slot = form.slot
                nextForm = False
            form.turn = turn
            nextTurn = turn + RETURN_PERIOD_PER_SLOT[slot - 1]
            if abs(PEAK_TURN - turn) < abs(nextTurn - PEAK_TURN):
                self.fightPeak = True
            state = State(self, form, slot, turn)
            state.setState(self, form)
            form.numAttacksReceived += state.numAttacksReceived
            nextForm = form.checkConditions(form.formChangeConditionOperator, form.formChangeConditions)
            self.states.append(state)
            turn = nextTurn

    def saveUnit(self):
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
        self.superAttacks = {}  # Will be a list of SuperAttack objects
        # This will be a list of Ability objects which will be iterated through each state to call applyToState.
        self.abilities = []
        self.formChangeConditionOperator = None
        self.formChangeConditions = [Condition()]
        # This will list active skill attacks and finish skills (as have to be applied after state.setState())
        self.specialAttacks = []
        self.slot = int(
            self.inputHelper.getAndSaveUserInput(f"Which slot is form # {formIdx} best suited for?", default=2)
        )
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
        self.abilities.extend(
            abilityQuestionaire(
                self,
                "How many unconditional buffs does the form have?",
                StartOfTurn,
            )
        )
        self.abilities.extend(
            abilityQuestionaire(
                self,
                "How many turn dependent buffs does the form have?",
                TurnDependent,
                [
                    "What turn does the buff start from?",
                    "What turn does the buff end on?",
                ],
                [None, None],
                [self.initialTurn, MAX_TURN],
            )
        )
        self.abilities.extend(
            abilityQuestionaire(
                self,
                "How many slot specific buffs does the form have?",
                SlotDependent,
                ["Which slot is required?"],
                [None],
                [[2, 3]],
            )
        )
        self.abilities.extend(
            abilityQuestionaire(
                self,
                "How many different buffs does the form get after receiving an attack?",
                AfterAttackReceived,
            )
        )
        self.abilities.extend(
            abilityQuestionaire(
                self,
                "How many different buffs does the form get on attacks received?",
                PerAttackReceived,
                ["What is the maximum buff?"],
                [None],
                [1.0],
            )
        )
        self.abilities.extend(
            abilityQuestionaire(
                self,
                "How many ki dependent buffs does the form have?",
                KiDependent,
                ["What is the required ki?"],
                [None],
                [24],
            )
        )
        self.abilities.extend(
            abilityQuestionaire(
                self,
                "How many different nullification abilities does the form have?",
                Nullification,
                ["Does this nullification have counter?"],
                [YES_NO],
                ["N"],
            )
        )
        self.abilities.extend(
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
        self.specialAttacks.extend(
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
        self.abilities.extend(
            abilityQuestionaire(
                self,
                "How many active skill buffs does the form have?",
                ActiveSkillBuff,
            )
        )
        # The SingleTurnAbility ability will get us the turn condition to activate this ability.
        self.abilities.extend(
            abilityQuestionaire(
                self,
                "How many Standby Finish Skills does the form have?",
                StandbyFinshSkill,
                [
                    "What is the type of the Finish Effect condition",
                    "What is the attack multiplier",
                    "What is the buff per charge?",
                ],
                [
                    clc.Choice(FINISH_EFFECT_CONDITIONS, case_sensitive=False),
                    clc.Choice(SPECIAL_ATTACK_MULTIPLIER_NAMES, case_sensitive=False),
                    None,
                ],
                ["Revive", "Super-Ultimate", 0],
            )
        )

        # If have another form left
        if formIdx < numForms:
            self.formChangeConditionOperator, self.formChangeConditions = getConditions(self.inputHelper)

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
        superAttackTypes = ["12 Ki", "18 Ki"]
        for superAttackType in superAttackTypes:
            multiplier = superAttackConversion[
                self.inputHelper.getAndSaveUserInput(
                    f"What is the form's {superAttackType} super attack multiplier?",
                    type=clc.Choice(SUPER_ATTACK_MULTIPLIER_NAMES, case_sensitive=False),
                    default=DEFAULT_SUPER_ATTACK_MULTIPLIER_NAMES[superAttackType],
                )
            ][superAttackLevelConversion[rarity][eza]]
            avgSuperAttack = SuperAttack(superAttackType, multiplier)
            if superAttackType == "12 Ki" or (rarity == "LR" and not (self.intentional12Ki)):
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
                assert superFracTotal == 1, "Invald super attack variant proabilities entered"
            self.superAttacks[superAttackType] = avgSuperAttack

    def checkConditions(self, operator, conditions):
        match operator:
            case None:
                result = conditions[0].isSatisfied(self)
            case "AND":
                result = np.all([condition.isSatisfied(self) for condition in conditions])
            case "OR":
                result = np.any([condition.isSatisfied(self) for condition in conditions])
        return result

    # Get charge per turn for a standby finish skill
    def getCharge(self, chargeCondition):
        charge = 0
        match chargeCondition:
            case "x2 same / rainbow or x1 other":
                charge = (
                    (
                        self.numSameTypeOrbs
                        + self.numRainbowOrbs
                        + (NUM_SLOTS - 1) * (NUM_SAME_TYPE_ORBS_NO_ORB_CHANGING + NUM_RAINBOW_ORBS_NO_ORB_CHANGING)
                    )
                    * 2
                    + self.numOtherTypeOrbs
                    + (NUM_SLOTS - 1) * NUM_OTHER_TYPE_ORBS_NO_ORB_CHANGING
                )
            case "Ki sphere Obtained by allies":
                # Currently assumes have rainbow orb changing
                charge = (
                    self.numSameTypeOrbs
                    + self.numRainbowOrbs
                    + self.numOtherTypeOrbs
                    + (NUM_SLOTS - 1)
                    * (
                        NUM_SAME_TYPE_ORBS_RAINBOW_ORB_CHANGING
                        + NUM_RAINBOW_ORBS_RAINBOW_ORB_CHANGING
                        + NUM_OTHER_TYPE_ORBS_RAINBOW_ORB_CHANGING
                    )
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
        # Dictionary for variables which have a 1-1 relationship with StartOfTurn EFFECTS
        self.buff = {
            "Ki": LEADER_SKILL_KI,
            "AEAAT": 0,
            "Guard": 0,
            "Crit": unit.pHiPoCrit + (1 - unit.pHiPoCrit) * form.linkCrit,
            "Disable Guard": 0,
            "Evade": unit.pHiPoDodge + (1 - unit.pHiPoDodge) * form.linkDodge,
            "Dmg Red against Normals": 0,
        }
        self.p1Buff = {"ATK": ATK_DEF_SUPPORT, "DEF": ATK_DEF_SUPPORT}
        self.p2Buff = {"ATK": form.linkAtkOnSuper, "DEF": 0}
        self.p3Buff = {"ATK": 0, "DEF": 0}
        self.kiPerOtherTypeOrb = 1
        self.kiPerSameTypeOrb = KI_PER_SAME_TYPE_ORB
        self.kiPerRainbowKiSphere = 1  # Ki per orb
        self.numRainbowOrbs = NUM_RAINBOW_ORBS_NO_ORB_CHANGING
        self.numOtherTypeOrbs = NUM_OTHER_TYPE_ORBS_NO_ORB_CHANGING
        self.numSameTypeOrbs = NUM_SAME_TYPE_ORBS_NO_ORB_CHANGING  # num of orbs
        self.p2DefA = 0
        self.p2DefB = 0
        self.healing = 0  # Fraction of health healed every turn
        self.support = 0  # Support score
        self.pNullify = 0  # Probability of nullifying all enemy super attacks
        self.aaPSuper = []  # Probabilities of doing additional super attacks and guaranteed additionals
        self.aaPGuarantee = []
        self.dmgRedA = 0
        self.dmgRedB = 0  # Dmg Red before and after attacking
        self.pCounterSA = 0  # Probability of countering an enemy super attack
        # Initialising these here, but will need to be updated everytime self.buff["Evade"] is increased, best to make a function to update evade
        self.numAttacksReceived = NUM_ATTACKS_DIRECTED[self.slot - 1] * (1 - self.buff["Evade"])
        self.numAttacksReceivedBeforeAttacking = NUM_ATTACKS_DIRECTED_BEFORE_ATTACKING[self.slot - 1] * (
            1 - self.buff["Evade"]
        )
        self.stackedStats = dict(zip(STACK_EFFECTS, np.zeros(len(STACK_EFFECTS))))

    def setState(self, unit, form):
        for ability in form.abilities:
            ability.applyToState(self, unit, form)
        self.p1Buff["ATK"] = np.maximum(self.p1Buff["ATK"], -1)
        self.p2Buff["DEF"] = self.p2DefA + self.p2DefB
        self.pNullify = self.pNullify + (1 - self.pNullify) * self.pCounterSA
        self.buff["Ki"] = min(round(self.buff["Ki"] + self.randomKi), rarity2MaxKi[unit.rarity])
        self.pN, self.pSA, self.pUSA = getAttackDistribution(
            self.buff["Ki"], self.randomKi, form.intentional12Ki, unit.rarity
        )
        self.aaSA = branchAA(-1, len(self.aaPSuper), unit.pHiPoAA, 1, self.aaPSuper, self.aaPGuarantee, unit.pHiPoAA)
        # Assume Binomial distribution for aaSA
        form.attacksPerformed += (1 - PROBABILITY_KILL_ENEMY_BEFORE_ATTACKING[self.slot - 1]) + self.aaSA * (
            1 - PROBABILITY_KILL_ENEMY_BEFORE_ATTACKING[self.slot - 1] - PROBABILITY_KILL_ENEMY_PER_ATTACK
        )
        self.updateStackedStats(form, unit)
        self.normal = getNormal(
            unit.kiMod12,
            self.buff["Ki"],
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
            self.buff["Ki"],
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
        self.avgAtk = getAvgAtk(
            self.aaPSuper,
            form.superAttacks["12 Ki"].multiplier,
            unit.nCopies,
            form.superAttacks["12 Ki"].effects["ATK"].duration,
            form.superAttacks["12 Ki"].effects["ATK"].buff,
            form.superAttacks["18 Ki"].effects["ATK"].buff,
            self.stackedStats["ATK"],
            self.p1Buff["ATK"],
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
        )
        # Apply active skill and finish skill attacks
        for specialAttack in form.specialAttacks:
            specialAttack.applyToState(self, unit, form)
        self.avgAtkModifer = self.buff["Crit"] * (CRIT_MULTIPLIER + unit.TAB * CRIT_TAB_INC) * BYPASS_DEFENSE_FACTOR + (
            1 - self.buff["Crit"]
        ) * (
            self.buff["AEAAT"] * (AEAAT_MULTIPLIER + unit.TAB * AEAAT_TAB_INC)
            + (1 - self.buff["AEAAT"])
            * (
                self.buff["Disable Guard"] * (DISABLE_GUARD_MULTIPLIER + unit.TAB * DISABLE_GUARD_TAB_INC)
                + (1 - self.buff["Disable Guard"]) * (AVG_TYPE_ADVANATGE + unit.TAB * DEFAULT_TAB_INC)
            )
        )
        self.apt = self.avgAtk * self.avgAtkModifer
        self.getAvgDefMult(form, unit)
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
            * self.avgDefPreSuper
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
        self.attributes = [
            unit.leaderSkill,
            unit.SBR,
            unit.HP,
            self.useability,  # Requires user input, should make a version that loads from file
            self.healing,
            self.support,
            self.apt,
            self.normalDamageTaken,
            self.saDamageTaken,
            self.slotFactor,
        ]

    def updateStackedStats(self, form, unit):
        # Needs to do two things, remove stacked attack from previous states if worn out and apply new buffs
        # If want the stacking of initial turn and transform later
        for stat in STACK_EFFECTS:
            # Update previous stack durations
            for stack in unit.stacks[stat]:
                stack.duration -= RETURN_PERIOD_PER_SLOT[unit.states[-1].slot]
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
                StartOfTurn,
            )
        )

    def applyToState(self, state, unit=None, form=None):
        if form.checkConditions(self.operator, self.conditions) and unit.fightPeak and not self.activated:
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


class ActiveSkillBuff(SingleTurnAbility):
    def __init__(self, form, args=[]):
        super().__init__(form)
        self.abilities = abilityQuestionaire(form, "How many different buffs does the active skill have?", StartOfTurn)

    def applyToState(self, state, unit=None, form=None):
        if form.checkConditions(self.operator, self.conditions) and unit.fightPeak and not self.activated:
            self.activated = True
            for ability in self.abilities:
                ability.end = state.turn + ability.effectDuration
                ability.applyToState(state, unit, form)


class ActiveSkillAttack(SingleTurnAbility):
    def __init__(self, form, args):
        super().__init__(form)
        attackMultiplier, attackBuff = args
        self.activeMult = specialAttackConversion[attackMultiplier] + attackBuff

    def applyToState(self, state, unit=None, form=None):
        if form.checkConditions(self.operator, self.conditions) and unit.fightPeak and not self.activated:
            self.activated = True
            form.attacksPerformed += 1  # Parameter should be used to determine buffs from per attack performed buffs
            state.avgAtk += getActiveAttack(
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


# This skill is to apply to a unit already in it's standyby mode.
# The condition to enter & exit the standy mode will be controlled by regular form changes.
class StandbyFinshSkill(SingleTurnAbility):
    def __init__(self, form, args):
        super().__init__(form)
        finishSkillChargeCondition, attackMultiplier, attackBuff = args
        self.activeMult = specialAttackConversion[attackMultiplier] * (1 + attackBuff)
        self.chargePerTurn = form.getCharge(finishSkillChargeCondition)
        self.charge = 0

    def applyToState(self, state, unit=None, form=None):
        self.charge += self.chargePerTurn
        if form.checkConditions(self.operator, self.conditions) and not unit.finishSkillActivated:
            unit.finishSkillActivated = True
            form.attacksPerformed += 1  # Parameter should be used to determine buffs from per attack performed buffs
            state.avgAtk += getActiveAttack(
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


class Revive(SingleTurnAbility):
    def __init__(self, form, args):
        super().__init__(form)
        self.hpRegen, self.isThisCharacterOnly = args
        self.abilities = abilityQuestionaire(
            form, "How many additional constant buffs does this revive have?", StartOfTurn
        )

    def applyToState(self, state, unit=None, form=None):
        if form.checkConditions(self.operator, self.conditions) and unit.fightPeak and not self.activated:
            self.activated = True
            state.healing = min(state.healing + self.hpRegen, 1)
            if self.isThisCharacterOnly:
                state.support += REVIVE_UNIT_SUPPORT_BUFF
            else:
                state.support += REVIVE_ROTATION_SUPPORT_BUFF
            for ability in self.abilities:
                ability.applyToState(state, unit, form)


class PassiveAbility(Ability):
    def __init__(self, form, activationProbability, effect, buff, effectDuration):
        super().__init__(form)
        self.activationProbability = activationProbability
        self.effect = effect
        self.effectDuration = effectDuration
        self.effectiveBuff = buff * activationProbability


class StartOfTurn(PassiveAbility):
    def __init__(
        self,
        form,
        activationProbability,
        effect,
        buff,
        effectDuration,
        start=1,
        end=MAX_TURN,
        ki=0,
        slots=SLOTS,
        args=[],
    ):
        super().__init__(form, activationProbability, effect, buff, effectDuration)
        self.start = start
        self.end = end
        self.ki = ki
        self.slots = slots
        self.effectiveBuff = buff * activationProbability * effectDuration

    def applyToState(self, state, unit=None, form=None):
        # Need to update in case one of the relevant variables has been updated
        state.randomKi = (
            KI_SUPPORT
            + state.kiPerOtherTypeOrb * state.numOtherTypeOrbs
            + state.kiPerSameTypeOrb * state.numSameTypeOrbs
            + state.numRainbowOrbs * state.kiPerRainbowKiSphere
            + form.linkKi
        )
        pHaveKi = 1 - ZTP_CDF(self.ki - 1 - state.buff["Ki"], state.randomKi)
        self.effectiveBuff = self.effectiveBuff * pHaveKi
        self.activationProbability *= pHaveKi
        # Check if state is elligible for ability
        if state.turn >= self.start and state.turn <= self.end and state.slot in self.slots:
            # If a support ability
            if self.effect in SUPPORT_EFFECTS:
                state.support += SUPPORT_FACTOR_DICT[self.effect] * self.effectiveBuff
            elif self.effect in state.buff.keys():
                state.buff[self.effect] += self.effectiveBuff
            elif self.effect in state.p1Buff.keys():
                state.p1Buff[self.effect] += self.effectiveBuff
            else:  # Edge cases
                match self.effect:
                    case "Disable Action":
                        state.pNullify = (
                            P_NULLIFY_FROM_DISABLE_ACTIVE * (1 - state.pNullify)
                            + (1 - P_NULLIFY_FROM_DISABLE_ACTIVE) * state.pNullify
                        )
                    case "AdditionalSuper":
                        state.aaPSuper.append(self.activationProbability)
                        state.aaPGuarantee.append(0)
                    case "AAChance":
                        state.aaPGuarantee.append(self.activationProbability)
                    case "SuperChance":
                        state.aaPSuper.append(self.activationProbability)
                    case "Ki (Type Ki Sphere)":
                        state.kiPerOtherTypeOrb += self.effectiveBuff
                        state.kiPerSameTypeOrb += self.effectiveBuff
                    case "Ki (Ki Sphere)":
                        state.kiPerOtherTypeOrb += self.effectiveBuff
                        state.kiPerSameTypeOrb += self.effectiveBuff
                        state.kiPerRainbowKiSphere += self.effectiveBuff
                    case "Ki (Same Type Ki Sphere)":
                        state.kiPerSameTypeOrb += self.effectiveBuff
                    case "Ki (Rainbow Ki Sphere)":
                        state.kiPerRainbowKiSphere += self.effectiveBuff


class TurnDependent(StartOfTurn):
    def __init__(self, form, activationProbability, effect, buff, effectDuration, args):
        start, end = args
        super().__init__(form, activationProbability, effect, buff, effectDuration, start=start, end=end)


class KiDependent(StartOfTurn):
    def __init__(self, form, activationProbability, effect, buff, effectDuration, args):
        ki = args[0]
        super().__init__(form, activationProbability, effect, buff, effectDuration, ki=ki)


class SlotDependent(StartOfTurn):
    def __init__(self, form, activationProbability, effect, buff, effectDuration, args):
        slots = args[0]
        super().__init__(form, activationProbability, effect, buff, effectDuration, slots=slots)


class PerAttackReceived(PassiveAbility):
    def __init__(self, form, activationProbability, effect, buff, effectDuration, args):
        super().__init__(form, activationProbability, effect, buff, effectDuration)
        self.max = args[0]

    def applyToState(self, state, unit=None, form=None):
        if self.effect in state.buff.keys():
            state.buff[self.effect] += min(
                self.effectiveBuff * (state.numAttacksReceivedBeforeAttacking + form.numAttacksReceived),
                self.max,
            )
        else:
            match self.effect:
                case "ATK":
                    state.p2Buff["ATK"] += min(
                        self.effectiveBuff * (state.numAttacksReceivedBeforeAttacking + form.numAttacksReceived),
                        self.max,
                    )
                case "DEF":
                    state.p2DefA += min(
                        (2 * form.numAttacksReceived + state.numAttacksReceivedBeforeAttacking - 1)
                        * self.effectiveBuff
                        / 2,
                        self.max,
                    )


class AfterAttackReceived(PassiveAbility):
    def __init__(self, form, activationProbability, effect, buff, effectDuration, turnsSinceActivated=0, args=[]):
        super().__init__(form, activationProbability, effect, buff, effectDuration)
        self.turnsSinceActivated = turnsSinceActivated

    def applyToState(self, state, unit=None, form=None):
        hitFactor = 1
        if self.turnsSinceActivated == 0:
            # If buff is a defensive one
            if self.effect in ["DEF", "Dmg Red"]:
                hitFactor = (
                    state.numAttacksReceived - 1
                ) / state.numAttacksReceived  # Factor to account for not having the buff on the fist hit
            else:
                hitFactor = min(state.numAttacksReceivedBeforeAttacking, 1)
        # geometric cdf
        effectiveBuff = (
            self.effectiveBuff * hitFactor * (1 - (1 - self.activationProbability) ** (self.turnsSinceActivated + 1))
        )
        if self.effect in state.buff.keys():
            state.buff[self.effect] += effectiveBuff
        else:
            match self.effect:
                case "DEF":
                    state.p2DefA += effectiveBuff
        self.turnsSinceActivated += 1
        # If not still going to be active next turn
        if self.effectDuration < self.turnsSinceActivated * RETURN_PERIOD_PER_SLOT[state.slot]:
            # Reset it to not be active
            self.turnsSinceActivated = 0


class PerRainbowOrb(PassiveAbility):
    def __init__(self, form, activationProbability, effect, buff, effectDuration, args=[]):
        super().__init__(form, activationProbability, effect, buff, effectDuration)

    def applyToState(self, state, unit=None, form=None):
        buffFromRainbowOrbs = self.effectiveBuff * state.numRainbowOrbs
        if self.effect in state.buff.keys():
            state.buff[self.effect] += buffFromRainbowOrbs
        else:
            match self.effect:
                case "Dmg Red":
                    state.dmgRedA += buffFromRainbowOrbs
                    state.dmgRedB += buffFromRainbowOrbs
                    state.buff["Dmg Red against Normals"] += buffFromRainbowOrbs


class Nullification(PassiveAbility):
    def __init__(self, form, activationProbability, effect, buff, effectDuration, args):
        super().__init__(form, activationProbability, effect, buff, effectDuration)
        self.hasCounter = args[0]

    def applyToState(self, state, unit=None, form=None):
        pNullify = self.activationProbability * (1 - (1 - saFracConversion[self.effect]) ** 2)
        state.pNullify = (1 - state.pNullify) * pNullify + (1 - pNullify) * state.pNullify
        if self.hasCounter:
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


class NumAttacksCondition(Condition):
    def __init__(self, numAttacks):
        self.formAttr = "attacksPerformed"
        self.conditionValue = numAttacks


class FinishSkillActivatedCondition(Condition):
    def __init__(self):
        self.formAttr = "finishSkillActivated"
        self.conditionValue = True


# Too niche to conform to a generalised case
class DoubleSameRainbowKiSphereCondition(Condition):
    def __init__(self, chargeCondition):
        self.conditionValue = chargeCondition
        self.currentValue = 0

    def isSatisfied(self, form):
        self.currentValue += form.getCharge(self.conditionValue)
        return self.currentValue >= self.conditionValue


if __name__ == "__main__":
    # InputModes = {manual, fromTxt, fromPickle, fromWeb}
    # unit = Unit(1, 1, "DEF", "ADD", "DGE", inputMode="fromTxt")
    unit = Unit(105, 1, "DEF", "ADD", "DGE", inputMode="fromTxt")
