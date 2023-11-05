import datetime as dt
from dokkanUnitHelperFunctions import *
from scipy.stats import geom
import copy

# TODO:
# - It would be awesome if after I have read in a unit I could reconstruct the passive description to compare it against the game
# - Make sure to include TYPE DEF BOOST correctly (HiPo & lowering Guard modifier)
# - Instead of asking user how many of something, should ask until they enteran exit key aka while loop instead of for loop
# - How are we dealing with unit-super attacks? I think this works if user specifies the correct activation probabilities
# - Should read up on python optimisation techniques once is running and se how long it takes. But try be efficient you go.
# - I think the 20x3 state matrix needs to be used to compute the best path
# - Whilst the state matrix is the ideal way, for now just assume a user inputed slot for each form
# - Should put at may not be relevant tag onto end of the prompts that may not always be relevant.
# - Should print out relavant parameters back to user, like activationTurn for special ability
# - Ideally would just pull data from database, but not up in time for new units. Would be amazing for old units though.
# - Leader skill weight should decrease from 5 as new structure adds more variability between leader skills
# - Make the outputted variables get saved to a file that can be modified later. Also record the inputs if transformed to unrecognizable form. Or can set defaults of quiz as previously input values.
# - Once calculate how many supers do on turn 1, use this in the SBR calculation for debuffs on super. i.e. SBR should be one of the last things to be calculated

##################################################### Helper Functions ############################################################################


def restrictionQuestionaire():
    numRestrictions = clc.prompt("How many different restrictions does this ability have?", default=0)
    totalRestrictionProbability = 0.0
    turnRestriction = MAX_TURN
    for restriction in range(numRestrictions):
        restrictionProbability = 0.0
        restrictionType = clc.prompt(
            "What type of restriction is it?",
            type=clc.Choice(RESTRICTIONS, case_sensitive=False),
            default="Turn",
        )
        if restrictionType == "Turn":
            turnRestriction = min(
                clc.prompt(
                    "What is the turn restriction (relative to the form's starting turn)?",
                    default=3,
                ),
                turnRestriction,
            )
        elif restrictionType == "Max HP":
            restrictionProbability = 1.0 - maxHealthCDF(clc.prompt("What is the maximum HP restriction?", default=0.7))
        elif restrictionType == "Min HP":
            restrictionProbability = maxHealthCDF(clc.prompt("What is the minimum HP restriction?", default=0.7))
        elif restrictionType == "Enemy Max HP":
            restrictionProbability = 1.0 - clc.prompt("What is the maximum enemy HP restriction?", default=0.5)
        elif restrictionType == "Enemy Min HP":
            restrictionProbability = clc.prompt("What is the minimum enemy HP restriction?", default=0.5)
        # Assume independence
        totalRestrictionProbability = (1.0 - totalRestrictionProbability) * restrictionProbability + (
            1.0 - restrictionProbability
        ) * totalRestrictionProbability
    return 1.0 - totalRestrictionProbability, turnRestriction


def abilityQuestionaire(form, abilityPrompt, abilityClass, parameterPrompts=[], types=[], defaults=[]):
    parameters = []
    numAbilities = clc.prompt(abilityPrompt, default=0)
    abilities = []
    for i in range(numAbilities):
        for j, parameterPrompt in enumerate(parameterPrompts):
            if len(types) == 0:  # If don't care about prompt choices
                parameters.append(clc.prompt(parameterPrompt))
            else:
                parameters.append(clc.prompt(parameterPrompt, type=types[j], default=defaults[j]))
        if issubclass(abilityClass, PassiveAbility):
            effect = clc.prompt(
                "What type of buff does the unit get?",
                type=clc.Choice(EFFECTS, case_sensitive=False),
                default="Raise ATK",
            )
            activationProbability = clc.prompt("What is the probability this ability activates?", default=1.0)
            buff = clc.prompt("What is the value of the buff?", default=0.0)
            effectDuration = clc.prompt("How many turns does it last for?", default=1)
            ability = abilityClass(form, activationProbability, effect, buff, effectDuration, parameters)
        elif issubclass(abilityClass, SingleTurnAbility):
            ability = abilityClass(form, parameters)
        abilities.append(ability)
    return abilities


######################################################### Classes #################################################################


class Unit:
    def __init__(self, id, nCopies, brz, HiPo1, HiPo2):
        self.id = str(id)
        self.nCopies = nCopies
        self.brz = brz
        self.HiPo1 = HiPo1
        self.HiPo2 = HiPo2
        self.getConstants()  # Requires user input, should make a version that loads from file
        self.getHiPo()
        self.getForms()  # Requires user input, should make a version that loads from file
        self.getStates()
        self.getSBR()  # Requires user input, should make a version that loads from file
        self.useability = (
            self.teams
            / NUM_TEAMS_MAX
            * (
                1
                + USEABILITY_SUPPORT_FACTOR * self.states[self.peakState].support
                + self.forms[self.peakForm].linkCommonality
            )
        )

    def getConstants(self):
        self.exclusivity = clc.prompt(
            "What is the unit's exclusivity?",
            type=clc.Choice(EXCLUSIVITIES, case_sensitive=False),
            default="DF",
        )
        self.rarity = exclusivity2Rarity[self.exclusivity]
        self.name = clc.prompt("What is the unit's name?", default="Super Saiyan Goku")
        self._class = clc.prompt(
            "What is the unit's class?",
            type=clc.Choice(CLASSES, case_sensitive=False),
            default="S",
        )
        self._type = clc.prompt(
            "What is the unit's type?",
            type=clc.Choice(TYPES, case_sensitive=False),
            default="AGL",
        )
        self.eza = yesNo2Bool[
            clc.prompt(
                "Has the unit EZA'd?",
                type=clc.Choice(yesNo2Bool.keys(), case_sensitive=False),
                default="N",
            )
        ]
        self.jp_date = dt.datetime.strptime(
            clc.prompt(
                "When did the unit release on the Japanse version of Dokkan? (MM/YY)",
                default="01/24",
            ),
            "%m/%y",
        )
        self.gbl_date = dt.datetime.strptime(
            clc.prompt(
                "When did the unit release on the Global version of Dokkan? (MM/YY)",
                default="01/24",
            ),
            "%m/%y",
        )
        self.HP = clc.prompt("What is the unit's base HP stat?", default=0)
        self.ATK = clc.prompt("What is the unit's base ATT stat?", default=0)
        self.DEF = clc.prompt("What is the unit's base DEF stat?", default=0)
        self.leaderSkill = leaderSkillConversion[
            clc.prompt(
                "How would you rate the unit's leader skill on a scale of 1-10?\n200% limited - e.g. LR Hatchiyak Goku\n 200% small - e.g. LR Metal Cooler\n 200% medium - e.g. PHY God Goku\n 200% large - e.g. LR Vegeta & Trunks\n",
                type=clc.Choice(leaderSkillConversion.keys(), case_sensitive=False),
                default="<150%",
            )
        ]
        self.teams = clc.prompt(
            "How many categories is the unit on? If the unit's viability is limited to certain categories, take this into account.",
            default=1,
        )
        self.kiMod12 = float(
            clc.prompt(
                "What is the unit's 12 ki attck modifer?",
                type=clc.Choice(KI_MODIFIERS_12),
                default="1.5",
            )
        )
        self.keepStacking = yesNo2Bool[
            clc.prompt(
                "Does the unit have the ability to keep stacking before transforming?",
                type=clc.Choice(yesNo2Bool.keys(), case_sensitive=False),
                default="N",
            )
        ]
        self.giantRageDuration = clc.prompt(
            "How many turns does the unit's giant/rage mode last for?",
            type=clc.Choice(GIANT_RAGE_DURATION),
            default="0",
        )

    def getHiPo(self):
        HiPoStats = hiddenPotentalStatsConverter[self._type][self.nCopies - 1]
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

    def getSBR(self):
        self.sbr = 0.0
        if yesNo2Bool[
            clc.prompt(
                "Does the unit have any SBR abilities?",
                type=clc.Choice(yesNo2Bool.keys(), case_sensitive=False),
                default="N",
            )
        ]:
            attackAll = attackAllConversion[
                clc.prompt(
                    "Does the unit attack all enemies on super?",
                    type=clc.Choice(yesNo2Bool.keys(), case_sensitive=False),
                    default="N",
                )
            ]

            seal = sealTurnConversion[
                clc.prompt(
                    "How many turns does the unit seal for?",
                    type=clc.Choice(sealTurnConversion.keys()),
                    default="0",
                )
            ]
            if seal != 0:
                seal *= clc.prompt(
                    "What is the unit's chance to seal?", default=0.0
                )  # Scale by number of enemies for all enemy seal, same for stun

            stun = stunTurnConversion[
                clc.prompt(
                    "How many turns does the unit stun for?",
                    type=clc.Choice(stunTurnConversion.keys()),
                    default="0",
                )
            ]
            if stun != 0:
                stun *= clc.prompt("What is the unit's chance to stun?", default=0.0)

            attDebuffOnAtk = attDebuffTurnConversion[
                clc.prompt(
                    "How many turns does the unit lower the enemy attack by attacking?",
                    type=clc.Choice(attDebuffTurnConversion.keys()),
                    default="0",
                )
            ]
            if attDebuffOnAtk != 0:
                attDebuffOnAtk *= attDebuffOnAttackConversion[
                    clc.prompt(
                        "How much is attack lowered by on attack?",
                        type=clc.Choice(attDebuffOnAttackConversion.keys(), case_sensitive=False),
                        default="Lowers",
                    )
                ]

            attDebuffPassive = attDebuffTurnConversion[
                clc.prompt(
                    "How many turns does the unit lower the enemy attack passively?",
                    type=clc.Choice(attDebuffTurnConversion.keys()),
                    default="0",
                )
            ]
            if attDebuffPassive != 0:
                attDebuffPassive *= clc.prompt("How much is attack lowered passively?", default=0.3)

            multipleEnemyBuff = multipleEnemyBuffConversion[
                clc.prompt(
                    "How much of a buff does the unit get when facing multiple enemies?",
                    type=clc.Choice(multipleEnemyBuffConversion.keys(), case_sensitive=False),
                    default="None",
                )
            ]
            sbrActiveSkillBuff = 0.0
            if yesNo2Bool[
                clc.prompt(
                    "Does the unit have an active skill that has SBR effects?",
                    type=clc.Choice(yesNo2Bool.keys(), case_sensitive=False),
                    default="N",
                )
            ]:
                sbrActiveSkillTurn = clc.prompt("What turn can it be activated?", default=1)
                sbrActiveSkillEffect = self.getSBR()
                sbrActiveSkillBuff += SBR_DF ** (sbrActiveSkillTurn - 1) * sbrActiveSkillEffect

            self.sbr = (
                attackAllDebuffConversion[attackAll] * (seal + stun + attDebuffOnAtk)
                + attDebuffPassive
                + multipleEnemyBuff
                + attackAll
                + sbrActiveSkillBuff
            )
        return self.sbr

    def getForms(self):
        startTurn = 1
        self.forms = []
        numForms = clc.prompt("How many forms does the unit have?", default=1)
        for i in range(numForms):
            slot = int(clc.prompt(f"Which slot is form # {i + 1} best suited for?", default=2))
            if i == numForms - 1:
                endTurn = MAX_TURN
            else:
                (
                    transformationProbabilityPerTurn,
                    maxTransformationTurn,
                ) = restrictionQuestionaire()
                endTurn = (
                    startTurn
                    + int(
                        min(
                            RETURN_PERIOD_PER_SLOT[slot - 1] * round(1 / transformationProbabilityPerTurn),
                            maxTransformationTurn,
                        )
                    )
                    - 1
                )  # Mean of geometric distribution is 1/p
            self.forms.append(Form(startTurn, endTurn, slot))
            startTurn = endTurn + 1
        for form in self.forms:
            form.saMult12 = superAttackConversion[
                clc.prompt(
                    "What is the form's 12 ki super attack multiplier?",
                    type=clc.Choice(SUPER_ATTACK_MULTIPLIER_NAMES),
                    default="Immense",
                )
            ][superAttackLevelConversion[self.rarity][self.eza]]
            abilityQuestionaire(
                form,
                "How many effects does this unit's 12 ki super attack have?",
                SuperAttack,
                ["Please press enter to continue"],
                [None],
                [False],
            )
            if self.rarity == "LR":
                form.intentional12Ki = yesNo2Bool[
                    clc.prompt("Should a 12 Ki be targetted for this form?", default="N")
                ]
                if not (form.intentional12Ki):
                    abilityQuestionaire(
                        form,
                        "How many effects does this unit's 18 ki super attack have?",
                        SuperAttack,
                        ["Please press enter to continue"],
                        [None],
                        [True],
                    )
            form.normalCounterMult = counterAttackConversion[
                clc.prompt(
                    "What is the unit's normal counter multiplier?",
                    type=clc.Choice(counterAttackConversion.keys(), case_sensitive=False),
                    default="NA",
                )
            ]
            form.saCounterMult = counterAttackConversion[
                clc.prompt(
                    "What is the unit's super attack counter multiplier?",
                    type=clc.Choice(counterAttackConversion.keys(), case_sensitive=False),
                    default="NA",
                )
            ]
            form.getLinks()
            # assert len(np.unique(links))==MAX_NUM_LINKS, 'Duplicate links'
            form.abilities.extend(
                abilityQuestionaire(
                    form,
                    "How many unconditional buffs does the form have?",
                    StartOfTurn,
                )
            )
            form.abilities.extend(
                abilityQuestionaire(
                    form,
                    "How many turn dependent buffs does the form have?",
                    TurnDependent,
                    [
                        "What turn does the buff start from?",
                        "What turn does the buff end on?",
                    ],
                    [None, None],
                    [form.startTurn, form.endTurn],
                )
            )
            form.abilities.extend(
                abilityQuestionaire(
                    form,
                    "How many different buffs does the form get on attacks received?",
                    PerAttackReceived,
                    ["What is the maximum buff?"],
                    [None],
                    [1.0],
                )
            )
            form.abilities.extend(
                abilityQuestionaire(
                    form,
                    "How many different buffs does the form get after receiving an attack?",
                    AfterAttackReceived,
                )
            )
            form.abilities.extend(
                abilityQuestionaire(
                    form,
                    "How many slot specific buffs does the form have?",
                    SlotDependent,
                    ["Which slot is required?"],
                    [None],
                    [1],
                )
            )
            form.abilities.extend(
                abilityQuestionaire(
                    form,
                    "How many ki dependent buffs does the form have?",
                    KiDependent,
                    ["What is the required ki?"],
                    [None],
                    [24],
                )
            )
            form.abilities.extend(
                abilityQuestionaire(
                    form,
                    "How many different nullification abilities does the form have?",
                    Nullification,
                    ["Does this nullification have counter?"],
                    [YES_NO],
                    ["N"],
                )
            )
            form.abilities.extend(
                abilityQuestionaire(
                    form,
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
            form.specialAttacks.extend(
                abilityQuestionaire(
                    form,
                    "How many active skill attacks does the form have?",
                    ActiveSkillAttack,
                    [
                        "What is the attack multiplier?",
                        "What is the additional attack buff when performing thes attack?",
                    ],
                    [clc.Choice(specialAttackConversion.keys()), None],
                    ["Ultimate", 0.0],
                )
            )
            form.abilities.extend(
                abilityQuestionaire(
                    form,
                    "How many active skill buffs does the form have?",
                    ActiveSkillBuff,
                    [
                        "How many times can the active skill be activated?",
                    ],
                    [None],
                    [1],
                )
            )

    def getStates(self):
        self.states = []
        turn = 1
        formIdx = 0
        while turn <= MAX_TURN:
            form = self.forms[formIdx]
            slot = form.slot
            state = State(slot, turn)
            state.setState(self, form)
            self.states.append(state)
            nextTurn = turn + RETURN_PERIOD_PER_SLOT[slot - 1]
            if abs(PEAK_TURN - turn) < abs(nextTurn - PEAK_TURN):
                self.peakState = len(self.states) - 1
                self.peakForm = formIdx
            turn = nextTurn
            if turn > form.endTurn:
                formIdx += 1


class Form:
    def __init__(self, startTurn, endTurn, slot):
        self.startTurn = startTurn
        self.endTurn = endTurn
        self.slot = slot
        self.linkNames = [""] * MAX_NUM_LINKS
        self.linkCommonality = 0.0
        self.linkKi = 0.0
        self.linkAtkSoT = 0.0
        self.linkDef = 0.0
        self.linkCrit = 0.0
        self.linkAtkOnSuper = 0.0
        self.linkDodge = 0.0
        self.linkDmgRed = 0.0
        self.linkHealing = 0.0
        self.saMult12 = 0.0
        self.saMult18 = 0.0
        # Super Attack Multipliers
        self.sa12AtkBuff = 0.0
        self.sa18AtkBuff = 0.0
        # Super Attack ATK buffs
        self.sa12DefBuff = 0.0
        self.sa18DefBuff = 0.0
        # Super Attack DEF buffs
        self.sa12Disable = False
        self.sa18Disable = False  # Super Attack disable action effects
        self.sa12Crit = 0.0
        self.sa18Crit = 0.0  # Super Attack crit effects
        self.sa12AtkStacks = 0
        self.sa18AtkStacks = 0  # Super Attack ATK stacks
        self.sa12Deftacks = 0
        self.sa18DefStacks = 0  # Super Attack DEF stacks
        self.intentional12Ki = False
        self.normalCounterMult = 0.0
        self.saCounterMult = 0.0
        # This will be a list of Ability objects which will be iterated through each state to call applyToState.
        self.abilities = []
        # This will list active skill attacks and finish skills (as have to be applied after state.setState())
        self.specialAttacks = []

    def getLinks(self):
        for linkIndex in range(MAX_NUM_LINKS):
            self.linkNames[linkIndex] = clc.prompt(
                f"What is the form's link # {linkIndex+1}",
                type=clc.Choice(LINKS, case_sensitive=False),
                default="Fierce Battle",
            )
            linkCommonality = clc.prompt(
                "If has an ideal linking partner, what is the chance this link is active?",
                default=-1.0,
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


class State:
    def __init__(self, slot, turn):
        self.slot = slot  # Slot no.
        self.turn = turn
        self.constantKi = LEADER_SKILL_KI
        self.randomKi = KI_SUPPORT  # Constant and Random ki
        self.kiPerOtherTypeOrb = 1
        self.kiPerSameTypeOrb = KI_PER_SAME_TYPE_ORB
        self.kiPerRainbowKiSphere = 1  # Ki per orb
        self.numRainbowOrbs = NUM_RAINBOW_ORBS_NO_ORB_CHANGING
        self.numOtherTypeOrbs = NUM_OTHER_TYPE_ORBS_NO_ORB_CHANGING
        self.numSameTypeOrbs = NUM_SAME_TYPE_ORBS_NO_ORB_CHANGING  # num of orbs
        self.p1Atk = LEADER_SKILL_STATS + ATK_DEF_SUPPORT
        self.p1Def = LEADER_SKILL_STATS + ATK_DEF_SUPPORT  # Start of turn stats (Phase 1)
        self.p2Atk = 0.0  # Phase 2 ATK
        self.p3Atk = 0.0
        self.p2DefA = 0.0
        self.p2DefB = 0.0  # Phase 2 DEF (Before and after attacking)
        self.p3Def = 0.0
        self.AEAAT = 0.0  # Probability for attacks effective against all types
        self.guard = 0.0  # Probability of guarding
        self.crit = 0.0  # Probability of performing a critical hit
        self.pEvade = 0.0  # Probability of evading
        self.healing = 0.0  # Fraction of health healed every turn
        self.support = 0.0  # Support score
        self.pNullify = 0.0  # Probability of nullifying all enemy super attacks
        self.aaPSuper = []  # Probabilities of doing additional super attacks and guaranteed additionals
        self.aaPGuarantee = []
        self.dmgRedA = 0.0
        self.dmgRedB = 0.0  # Damage reduction before and after attacking
        self.dmgRedNormal = 0.0
        self.pCounterSA = 0.0  # Probability of countering an enemy super attack
        self.numAttacksReceived = 0  # Number of attacks received so far in this form. Assuming update the state.numAttacksReceievd after the abilities have been processed for that turn
        self.avgAtt = 0.0 # Average total ATK stat

    def setState(self, unit, form):
        for ability in form.abilities:
            ability.applyToState(self, unit)
        self.healing += form.linkHealing
        self.p1Atk = np.maximum(self.p1Atk, -1)
        self.p2Atk += form.linkAtkOnSuper
        self.p2Def = self.p2DefA + self.p2DefB
        self.crit = self.crit + (1 - self.crit) * (unit.pHiPoCrit + (1 - unit.pHiPoCrit) * form.linkCrit)
        self.pEvade = self.pEvade + (1 - self.pEvade) * (unit.pHiPoDodge + (1 - unit.pHiPoDodge) * form.linkDodge)
        self.pNullify = self.pNullify + (1 - self.pNullify) * self.pCounterSA
        self.randomKi += self.kiPerOtherTypeOrb * self.numOtherTypeOrbs + self.kiPerSameTypeOrb * self.numSameTypeOrbs + self.numRainbowOrbs * self.kiPerRainbowKiSphere + form.linkKi
        self.ki = np.min(int(np.around(self.constantKi + self.randomKi)), MAX_KI)
        self.Pr_N, self.Pr_SA, self.Pr_USA = getAttackDistribution(self.constantKi, self.randomKi, form.intentional12Ki, unit.rarity)
        self.avg_AA_SA = branchAA(-1, len(self.aaPSuper), unit.pHiPoAA, 1, self.aaPSuper, self.aaPGuarantee, unit.pHiPoAA)
        self.stackedAtk, self.stackedDef = self.getStackedStats()
        self.normal = getNormal(unit.kiMod_12, self.ki, unit.ATK, self.p1Atk, self.stackedAtk, form.linkAtt_SoT, self.p2Atk, self.p3Atk)
        self.sa = getSA(unit.kiMod_12, unit.ATK, self.p1Atk, self.stackedAtk, form.linkAtt_SoT, self.p2Atk, self.p3Atk, form.saMult12, unit.EZA, unit.exclusivity, unit.nCopies, form.sa12AtkStacks, form.sa12AtkBuff)
        if unit.rarity == "LR":
            self.usa = getUSA(unit.kiMod_12, self.ki, unit.ATK, self.p1Atk, self.stackedAtk, form.linkAtt_SoT, self.p2Atk, self.p3Atk, self.saMult18, unit.EZA, unit.exclusivity, unit.nCopies, form.sa18AtkStacks, form.sa18AtkBuff)
            self.avgAtt = getAvgAtk(self.aaPSuper, form.saMult12, unit.EZA, unit.exclusivity, unit.nCopies, form.sa12AtkStacks, form.sa12AtkBuff, form.sa18AtkBuff, self.stackedAtk, self.p1Atk, self.normal, self.sa, self.usa, unit.pHiPoAA, self.aaPGuarantee, self.pCounterSA, form.normalCounterMult, form.saCounterMult, self.Pr_N, self.Pr_SA, self.Pr_USA, unit.rarity)
        else:
            self.avgAtt = getAvgAtk(self.aaPSuper, form.saMult12, unit.EZA, unit.exclusivity, unit.nCopies, form.sa12AtkStacks, form.sa12AtkBuff, 0, self.stackedAtk, self.p1Atk, self.normal, self.sa, 0, unit.pHiPoAA, self.aaPGuarantee, form.pCounterNormal, self.pCounterSA, form.normalCounterMult, form.saCounterMult, self.Pr_N, self.Pr_SA, self.Pr_USA, unit.rarity)
        # Apply active skill and finish skill attacks
        for specialAttack in form.specialAttacks:
            specialAttack.applyToState(self, unit)
    """
        self.avgAttModifer = self.P_Crit * CritMultiplier + (1 - self.P_Crit) * (
            self.P_SEaaT * SEaaTMultiplier + (1 - self.P_SEaaT) * avgTypeAdvantage
        )
        self.apt = self.avgAtt * self.avgAttModifer
        if self.kit.GRLength != 0:
            self.apt[self.activeSkillTurn - 1] += self.apt_GR
            self.support[self.activeSkillTurn - 1] += self.support_GR
        self.avgDefMult = self.getAvgDefMult()
        self.avgDefPreSuper = (
            self.DEF
            * (1 + leaderSkillBuff)
            * (1 + self.p1Def)
            * (1 + self.linkDef)
            * (1 + self.kit.P2A_Def)
            * (1 + self.p3Def)
            * (1 + self.stackedDef)
        )
        self.avgDefPostSuper = (
            self.DEF
            * (1 + leaderSkillBuff)
            * (1 + self.p1Def)
            * (1 + self.linkDef)
            * (1 + self.p2Def)
            * (1 + self.p3Def)
            * (1 + self.avgDefMult)
        )
        self.normalDefencePreSuper = np.minimum(
            -(1 - (1 - dodgeCancelFrac) * self.P_Dodge)
            * (
                self.P_guard
                * GuardModifer(
                    maxNormalDamage * avgGuardFactor * (1 - self.dmgRedNormal)
                    - self.avgDefPreSuper,
                    guardMod,
                )
                + (1 - self.P_guard)
                * (
                    maxNormalDamage * avgTypeFactor * (1 - self.dmgRedNormal)
                    - self.avgDefPreSuper
                )
            )
            / (maxNormalDamage * avgTypeFactor),
            0.0,
        )
        self.normalDefencePostSuper = np.minimum(
            -(1 - (1 - dodgeCancelFrac) * self.P_Dodge)
            * (
                self.P_guard
                * GuardModifer(
                    maxNormalDamage * avgGuardFactor * (1 - self.dmgRedNormal)
                    - self.avgDefPostSuper,
                    guardMod,
                )
                + (1 - self.P_guard)
                * (
                    maxNormalDamage * avgTypeFactor * (1 - self.dmgRedNormal)
                    - self.avgDefPostSuper
                )
            )
            / (maxNormalDamage * avgTypeFactor),
            0.0,
        )
        self.saDefencePreSuper = np.minimum(
            -(
                1
                - (
                    self.P_nullify
                    + (1 - self.P_nullify) * (1 - dodgeCancelFrac) * self.P_Dodge
                )
            )
            * (
                self.P_guard
                * GuardModifer(
                    maxSADamage * avgGuardFactor * (1 - self.dmgRed)
                    - self.avgDefPreSuper,
                    guardMod,
                )
                + (1 - self.P_guard)
                * (
                    maxSADamage * avgTypeFactor * (1 - self.dmgRed)
                    - self.avgDefPreSuper
                )
            )
            / (maxSADamage * avgTypeFactor),
            0.0,
        )
        self.saDefencePostSuper = np.minimum(
            -(
                1
                - (
                    self.P_nullify
                    + (1 - self.P_nullify) * (1 - dodgeCancelFrac) * self.P_Dodge
                )
            )
            * (
                self.P_guard
                * GuardModifer(
                    maxSADamage * avgGuardFactor * (1 - self.dmgRed)
                    - self.avgDefPostSuper,
                    guardMod,
                )
                + (1 - self.P_guard)
                * (
                    maxSADamage * avgTypeFactor * (1 - self.dmgRed)
                    - self.avgDefPostSuper
                )
            )
            / (maxSADamage * avgTypeFactor),
            0.0,
        )
        self.slot1Ability = np.maximum(
            self.normalDefencePreSuper + self.saDefencePreSuper, -0.5
        )
        self.healing += (
            (0.03 + 0.0015 * HiPo_Recovery[self.nCopies - 1])
            * self.avgDefPreSuper
            * self.kit.collectKi
            * STOrbPerKi
            / avgHealth
        )
        self.attributes = [
            self.leaderSkill,
            self.SBR,
            self.useability,
            self.healing,
            self.support,
            self.apt,
            self.normalDefencePostSuper,
            self.saDefencePostSuper,
            self.slot1Ability,
        ]

        def getStackedStats(self):
        # Can make more efficient later by saving stacked attack for each turn and just add on next turn, rather than calculating the whole thing on each call
        stackedAtt, stackedDef = [0] * MAX_TURN, [0] * MAX_TURN
        for turn in range(
            MAX_TURN - 1
        ):  # For each turn < self.turn (i.e. turns which can affect how much defense have on self.turn)
            if self.kit.keepStacking:
                i = 0  # If want the stacking of initial turn and transform later
            else:
                i = turn
            if (
                self.kit.SA_18_Att_Stacks[i] > 1
            ):  # If stack for long enough to last to turn self.turn
                stackedAtt[turn + 1 : turn + self.kit.SA_18_Att_Stacks[i]] += (
                    self.Pr_USA[i] * self.kit.SA_18_Att[i]
                )  # add stacked atk
            if (
                self.kit.SA_18_Def_Stacks[i] > 1
            ):  # If stack for long enough to last to turn self.turn
                stackedDef[turn + 1 : turn + self.kit.SA_18_Def_Stacks[i]] += (
                    self.Pr_USA[i] * self.kit.SA_18_Def[i]
                )  # add stacked atk
            if (
                self.kit.SA_12_Att_Stacks[i] > 1
            ):  # If stack for long enough to last to turn self.turn
                stackedAtt[turn + 1 : turn + self.kit.SA_12_Att_Stacks[i]] += (
                    self.Pr_SA[i] + self.avg_AA_SA[i]
                ) * self.kit.SA_12_Att[
                    i
                ]  # add stacked atk
            if (
                self.kit.SA_12_Def_Stacks[i] > 1
            ):  # If stack for long enough to last to turn self.turn
                stackedDef[turn + 1 : turn + self.kit.SA_12_Def_Stacks[i]] += (
                    self.Pr_SA[i] + self.avg_AA_SA[i]
                ) * self.kit.SA_12_Def[
                    i
                ]  # add stacked atk
        return [np.array(stackedAtt), np.array(stackedDef)]

    def getAvgDefMult(self):
        if self.kit.rarity == "LR":  # If unit is a LR
            avgDefMult = (
                self.Pr_SA * self.kit.SA_12_Def + self.Pr_USA * self.kit.SA_18_Def
            )
        else:
            avgDefMult = self.Pr_SA * self.kit.SA_12_Def
        avgDefMult += self.stackedDef + self.avg_AA_SA * self.kit.SA_12_Def
        return avgDefMult
        """


class Ability:
    def __init__(self, form):
        self.form = form


class SpecialAbility(Ability):
    def __init__(self, form):
        super().__init__(form)
        self.activationProbability, self.maxTurnRestriction = restrictionQuestionaire()


class SingleTurnAbility(SpecialAbility):
    def __init__(self, form):
        super().__init__(form)
        self.activationTurn = int(
            max(
                min(round(1 / self.activationProbability), self.maxTurnRestriction),
                PEAK_TURN - 1,
            )
        )  # Mean of geometric distribution is 1/p


class GiantRageMode(SingleTurnAbility):
    def __init__(self, form, args):
        super().__init__(form)
        self.ATK = args[0]
        self.support = GIANT_RAGE_SUPPORT
        slot = 1  # Arbitarary choice, could also be 2 or 3
        self.giantRageForm = Form(
            self.activationTurn, self.activationTurn, slot
        )  # Create a form so can get access to abilityQuestionaire to ask user questions
        self.giantRageForm.abilities.extend(
            abilityQuestionaire(
                self.giantRageForm,
                "How many buffs does this giant/rage mode have?",
                StartOfTurn,
            )
        )
        self.giantRageModeState = State(
            slot, self.activationTurn
        )  # Create a State so can get access to setState for damage calc
        self.giantRageModeState.ATK = args[0]
        for ability in self.giantRageForm.abilities:  # Apply the giant/form abilities
            ability.applyToState(self.giantRageModeState)

    def applyToState(self, state, unit=None):
        if state.turn == self.activationTurn:
            giantRageUnit = copy(unit)
            giantRageUnit.ATK = self.ATK
            self.giantRageModeState.setState(self.giantRageForm, giantRageUnit)  # Calculate the APT of the state
            state.APT += self.giantRageModeState.APT * NUM_SLOTS * giantRageUnit.giantRageDuration
            state.support += self.support


class ActiveSkillBuff(SingleTurnAbility):
    def __init__(self, form, args):
        super().__init__(form)
        self.numActivations = args[0]
        for activation in range(self.numActivations):
            self.form.abilities.extend(
                abilityQuestionaire(
                    self.form,
                    "How many different buffs does this active skill attack have?",
                    TurnDependent,
                    [
                        "This is the activation turn. Please press enter to continue",
                        "This is the form's next turn. Please press enter to continue",
                    ],
                    [None, None],
                    [
                        self.activationTurn + activation * RETURN_PERIOD_PER_SLOT[self.form.slot],
                        self.activationTurn + activation * RETURN_PERIOD_PER_SLOT[self.form.slot] + 1,
                    ],
                )
            )


class ActiveSkillAttack(SingleTurnAbility):
    def __init__(self, form, args):
        super().__init__(form)
        self.attackMultiplier, self.attackBuff = args
        self.activeMult = specialAttackConversion[self.attackMultiplier] + self.attackBuff

    def applyToState(self, state, unit=None):
        if state.turn == self.activationTurn:
            state.attacksPerformed += 1  # Parameter should be used to determine buffs from per attack performed buffs
            state.avgAtk += getActiveAttack(
                unit.kiMod12,
                rarity2MaxKi[unit.rarity],
                unit.ATK,
                state.p1Atk,
                state.stackedAtk,
                self.form.linkAtkSoT,
                state.p2Atk,
                state.p3Atk,
                state.activeMult,
                unit.nCopies,
                    )


class Revive(SingleTurnAbility):
    def __init__(self, form, args):
        super().__init__(form)
        self.hpRegen, self.isThisCharacterOnly = args
        self.form.abilities.extend(
            abilityQuestionaire(
                self.form,
                "How many additional constant buffs does this revive have?",
                TurnDependent,
                [
                    "This is the activation turn. Please press enter to continue",
                    "This is the form's end turn. Please press enter to continue",
                ],
                [None, None],
                [self.activationTurn, self.form.endTurn],
            )
        )

    def applyToState(self, state, unit=None):
        if state.turn == self.activationTurn:
            state.healing = np.min(state.healing + self.hpRegen, 1.0)
        if self.isThisCharacterOnly:
            state.support += REVIVE_UNIT_SUPPORT_BUFF
        else:
            state.support += REVIVE_ROTATION_SUPPORT_BUFF


class PassiveAbility(Ability):
    def __init__(self, form, activationProbability, effect, buff, effectDuration):
        super().__init__(form)
        self.activationProbability = activationProbability
        self.effect = effect
        self.effectDuration = effectDuration
        self.effectiveBuff = buff * activationProbability


class SuperAttack(PassiveAbility):
    def __init__(self, form, activationProbability, effect, buff, effectDuration, args):
        super().__init__(form, activationProbability, effect, buff, effectDuration)
        self.is18Ki = args[0]
        if self.is18Ki:
            superAttackVars = [
                [form.sa18AtkBuff, form.sa18AtkStacks],
                [form.sa18DefBuff, form.sa18DefStacks],
                form.sa18Crit,
                form.sa18Disable,
            ]
        else:
            superAttackVars = [
                [form.sa12AtkBuff, form.sa12AtkStacks],
                [form.sa12DefBuff, form.sa12DefStacks],
                form.sa12Crit,
                form.sa12Disable,
            ]

        self.effectToVar = dict(zip(SUPER_ATTACK_EFFECTS, superAttackVars))
        if self.effect in ["Raise ATK", "Raise DEF"]:
            self.effectToVar[self.effect][
                0
            ] += self.effectiveBuff  # += here for unit super attack probability weightings
            self.effectToVar[self.effect][1] = self.effectDuration  # Assuming this doesn't vary in a unit super attack
        elif self.effect == "Disable Action":
            self.effectToVar[self.effect] = bool(self.effectiveBuff)
        else:
            self.effectToVar[self.effect] += self.effectiveBuff  # += here for unit super attack probability weightings
        numUnitSuperAttacks = clc.prompt("How many unit super attacks does this form have?", default=0)
        for unitSuperAttack in range(numUnitSuperAttacks):
            unitSuperAttackEffects = abilityQuestionaire(
                form,
                "How many effects does this unit super attack have?",
                SuperAttack,
                ["Please press enter to continue"],
                [None],
                [self.is18Ki],
            )


class StartOfTurn(PassiveAbility):
    def __init__(
        self, form, activationProbability, effect, buff, effectDuration, start=0, end=MAX_TURN, ki=0, slots=SLOTS
    ):
        super().__init__(form, activationProbability, effect, buff, effectDuration)
        self.start = start
        self.end = end
        self.ki = ki
        self.slots = slots
        self.effectiveBuff = buff * activationProbability * effectDuration

    def applyToState(self, state, unit=None):
        pHaveKi = 1.0 - ZTP_CDF(self.ki - 1 - state.constantKi, state.randomKi)
        self.effectiveBuff = self.effectiveBuff * pHaveKi
        self.activationProbability *= pHaveKi
        # Check if state is elligible for ability
        if state.turn >= self.start and state.turn <= self.end and state.slot in self.slots:
            # If not a support ability
            if self.effect not in SUPPORT_EFFECTS:
                # First try edge cases
                match self.effect:
                    case "Disable Action":
                        state.pNullify = (
                            P_NULLIFY_FROM_DISABLE_ACTIVE * (1.0 - state.pNullify)
                            + (1.0 - P_NULLIFY_FROM_DISABLE_ACTIVE) * state.pNullify
                        )
                    case "AdditonalSuper":
                        state.aaPSuper.append(self.activationProbability)
                        state.aaPGuarantee.append(0.0)
                    case "AAWithChanceToSuper":
                        chanceToSuper = clc.prompt(
                            "What is the chance to super given the additional triggered?",
                            default=0,
                        )
                        state.aaPSuper.append(chanceToSuper)
                        state.aaPGuarantee.append(self.activationProbability)
                    # Otherwise try regular cases
                    case _:
                        effectToVar = {
                            "Raise Ki": state.constantKi,
                            "Raise ATK": state.p1Atk,
                            "Raise DEF": state.p1Def,
                            "Guard": state.guard,
                            "DamageReduction Against Normal Attacks": state.dmgRedNormal,
                            "Critical Hit": state.crit,
                            "Evasion": state.pEvade,
                            "Attack Effective to All": state.AEAAT,
                            "Raise Ki (Type Ki Sphere)": state.kiPerTypeOrb,
                        }
                        effectToVar[self.effect] += self.effectiveBuff
            else:  # If a support ability
                state.support += SUPPORT_FACTOR_DICT[self.effect] * self.effectiveBuff


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

    def applyToState(self, state, unit=None):
        match self.effect:
            case "Ki":
                state.constantKi += np.minimum(
                    self.effectiveBuff
                    * (NUM_ATTACKS_RECEIVED_BEFORE_ATTACKING[state.slot] + state.numAttacksReceived),
                    self.max,
                )
            case "ATK":
                state.p2Atk += np.minimum(
                    self.effectiveBuff
                    * (NUM_ATTACKS_RECEIVED_BEFORE_ATTACKING[state.slot] + state.numAttacksReceived),
                    self.max,
                )
            case "DEF":
                state.p2DefA += np.minimum(
                    (2 * state.numAttacksReceived + NUM_ATTACKS_RECEIVED[state.slot] - 1) * self.effectiveBuff / 2,
                    self.max,
                )
            case "Critical Hit":
                state.crit += np.minimum(
                    self.effectiveBuff
                    * (NUM_ATTACKS_RECEIVED_BEFORE_ATTACKING[state.slot] + state.numAttacksReceived),
                    self.max,
                )


class AfterAttackReceived(PassiveAbility):
    def __init__(self, form, activationProbability, effect, buff, effectDuration, turnsSinceActivated=0):
        super().__init__(form, activationProbability, effect, buff, effectDuration)
        self.turnsSinceActivated = turnsSinceActivated

    def applyToState(self, state, unit=None):
        # state.attacksReceiving is how many attacks the state is expected to recieve not including evades/nullified attacks
        # If buff is a defensive one
        hitFactor = 1.0
        if self.turnsSinceActivated == 0:
            if self.effect in ["Raise DEF", "Damage Reduction"]:
                hitFactor = (
                    state.attacksReceiving - 1
                ) / state.attacksReceiving  # Factor to account for not having the buff on the fist hit
            else:
                hitFactor = np.min(state.attacksReceivingBeforeAttacking, 1.0)
        match self.effect:
            case "DEF":
                state.p2DefA += (
                    self.buff * hitFactor * geom.cdf(self.turnsSinceActivated + 1, self.activationProbability)
                )  # This should return self.activationProbabiltiy if self.turnsActivated = 0
            case "Attack Effective to All":
                state.AEAAT = (
                    self.buff * hitFactor * geom.cdf(self.turnsSinceActivated + 1, self.activationProbability)
                )
        self.turnsSinceActivated += 1
        # If buff lasts till unit's next turn
        if self.effectDuration > self.turnsSinceActivated * RETURN_PERIOD_PER_SLOT[state.slot]:
            self.form.abilities.extend(
                AfterAttackReceived(
                    self.form,
                    self.activationProbability,
                    self.effect,
                    self.buff,
                    self.effectDuration,
                    self.turnsSinceActivated,
                )
            )


class PerRainbowOrb(PassiveAbility):
    def __init__(self, form, activationProbability, effect, buff, effectDuration, args):
        super().__init__(form, activationProbability, effect, buff, effectDuration)

    def applyToState(self, state, unit=None):
        buffFromRainbowOrbs = self.effectiveBuff * state.numRainbowOrbs
        match self.effect:
            case "Critical Hit":
                state.crit += buffFromRainbowOrbs
            case "Damage Reduction":
                state.dmgRedA += buffFromRainbowOrbs
                state.dmgRedB += buffFromRainbowOrbs
                state.dmgRedNormal += buffFromRainbowOrbs
            case "Evasion":
                state.pEvade += buffFromRainbowOrbs


class Nullification(PassiveAbility):
    def __init__(self, form, activationProbability, effect, buff, effectDuration, args):
        super().__init__(form, activationProbability, effect, buff, effectDuration)
        self.hasCounter = args[0]

    def applyToState(self, state, unit=None):
        pNullify = self.activationProbability * (1.0 - (1.0 - saFracConversion[self.effect]) ** 2)
        state.pNullify = (1.0 - state.pNullify) * pNullify + (1.0 - pNullify) * state.pNullify
        if self.hasCounter:
            state.pCounterSA = (1.0 - state.pCounterSA) * pNullify + (1.0 - pNullify) * state.pCounterSA


if __name__ == "__main__":
    kit = Unit(1, 1, "DEF", "ADD", "DGE")
