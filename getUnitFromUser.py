import datetime as dt
from dokkanUnitHelperFunctions import *
from scipy.stats import geom
import copy
import os
import pickle

# TODO:
# - Should save all the user inputs to a .txt file and read them back in (up to one before end) to quickly catch the user back up to where they were before they inputted an error
# - It would be awesome if after I have read in a unit I could reconstruct the passive description to compare it against the game
# - Instead of asking user how many of something, should ask until they enteran exit key aka while loop instead of for loop
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
    totalRestrictionProbability = 1
    turnRestriction = MAX_TURN
    for restriction in range(numRestrictions):
        restrictionType = clc.prompt(
            "What type of restriction is it?",
            type=clc.Choice(RESTRICTIONS, case_sensitive=False),
            default="Turn",
        )
        if restrictionType == "Turn":
            turnRestriction = min(
                clc.prompt(
                    "What is the turn restriction (relative to the form's starting turn)?",
                    default=5,
                ),
                turnRestriction,
            )
        else:
            if restrictionType == "Max HP":
                restrictionProbability = 1 - maxHealthCDF(
                    clc.prompt("What is the maximum HP restriction?", default=0.7)
                )
            elif restrictionType == "Min HP":
                restrictionProbability = maxHealthCDF(clc.prompt("What is the minimum HP restriction?", default=0.7))
            elif restrictionType == "Enemy Max HP":
                restrictionProbability = 1 - clc.prompt("What is the maximum enemy HP restriction?", default=0.5)
            elif restrictionType == "Enemy Min HP":
                restrictionProbability = clc.prompt("What is the minimum enemy HP restriction?", default=0.5)
            # Assume independence
            totalRestrictionProbability = (1 - totalRestrictionProbability) * restrictionProbability + (
                1 - restrictionProbability
            ) * totalRestrictionProbability
    return max(1 - totalRestrictionProbability, 1 / MAX_TURN), turnRestriction


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
                default="ATK",
            )
            activationProbability = clc.prompt("What is the probability this ability activates?", default=1.0)
            buff = clc.prompt("What is the value of the buff?", default=1.0)
            effectDuration = clc.prompt(
                "How many turns does it last for? Only applicable to abilities with a time limit.", default=1
            )
            ability = abilityClass(form, activationProbability, effect, buff, effectDuration, args=parameters)
        elif issubclass(abilityClass, SingleTurnAbility):
            ability = abilityClass(form, parameters)
        abilities.append(ability)
    return abilities


######################################################### Classes #################################################################


class Unit:
    def __init__(self, id, nCopies, brz, HiPo1, HiPo2, loadPickle=False):
        self.picklePath = os.getcwd() + "\\DokkanUnits\\" + HIPO_DUPES[nCopies - 1] + "\\unit_" + str(id) + ".pkl"
        # For debugging
        if loadPickle:
            self = pickle.load(open(self.picklePath, "rb"))
            self.stacks = dict(zip(STACK_EFFECTS, [[], []]))  # Dict mapping STACK_EFFECTS to list of Stack objects
            self.getStates()
            self.saveUnit()
        else:
            self.id = str(id)
            self.nCopies = nCopies
            self.brz = brz
            self.HiPo1 = HiPo1
            self.HiPo2 = HiPo2
            self.getConstants()  # Requires user input, should make a version that loads from file
            self.getHiPo()
            self.getSBR()  # Requires user input, should make a version that loads from file
            self.getForms()  # Requires user input, should make a version that loads from file
            self.stacks = dict(zip(STACK_EFFECTS, [[], []]))  # Dict mapping STACK_EFFECTS to list of Stack objects
            self.getStates()
            self.saveUnit()

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
        self.EZA = yesNo2Bool[
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
        self.HP = clc.prompt("What is the unit's Max Level HP stat?", default=0)
        self.ATK = clc.prompt("What is the unit's Max Level ATK stat?", default=0)
        self.DEF = clc.prompt("What is the unit's Max Level DEF stat?", default=0)
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
            default=0,
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
        self.TAB = HIPO_TYPE_ATK_BOOST[self.nCopies - 1]
        self.TDB = HIPO_TYPE_DEF_BOOST[self.nCopies - 1]

    def getSBR(self):
        self.SBR = 0
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
            sbrActiveSkillBuff = 0
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

            self.SBR = (
                attackAllDebuffConversion[attackAll] * (seal + stun + attDebuffOnAtk)
                + attDebuffPassive
                + multipleEnemyBuff
                + attackAll
                + sbrActiveSkillBuff
            )
        return self.SBR

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
            form.intentional12Ki = yesNo2Bool[clc.prompt("Should a 12 Ki be targetted for this form?", default="N")]
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
            form.getSuperAttacks(self.rarity, self.EZA)
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
                        "What is the additional attack buff when performing the attack?",
                    ],
                    [clc.Choice(specialAttackConversion.keys(), case_sensitive=False), None],
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
            form.numAttacksReceived += NUM_ATTACKS_RECEIVED[slot - 1]
            self.states.append(state)
            nextTurn = turn + RETURN_PERIOD_PER_SLOT[slot - 1]
            if abs(PEAK_TURN - turn) < abs(nextTurn - PEAK_TURN):
                self.peakState = len(self.states) - 1
                self.peakForm = formIdx
            turn = nextTurn
            if turn > form.endTurn:
                formIdx += 1

    def saveUnit(self):
        with open(self.picklePath, "wb") as outp:  # Overwrites any existing file.
            pickle.dump(self, outp, pickle.HIGHEST_PROTOCOL)
        outp.close()


class Form:
    def __init__(self, startTurn, endTurn, slot):
        self.startTurn = startTurn
        self.endTurn = endTurn
        self.slot = slot
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
        self.intentional12Ki = False
        self.normalCounterMult = 0
        self.saCounterMult = 0
        self.numAttacksReceived = 0  # Number of attacks received so far in this form.
        self.superAttacks = {}  # Will be a list of SuperAttack objects
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
                clc.prompt(
                    f"What is the form's {superAttackType} super attack multiplier?",
                    type=clc.Choice(SUPER_ATTACK_MULTIPLIER_NAMES, case_sensitive=False),
                    default=DEFAULT_SUPER_ATTACK_MULTIPLIER_NAMES[superAttackType],
                )
            ][superAttackLevelConversion[rarity][eza]]
            avgSuperAttack = SuperAttack(superAttackType, multiplier)
            if superAttackType == "12 Ki" or (rarity == "LR" and not (self.intentional12Ki)):
                numSuperAttacks = clc.prompt(
                    f"How many different {superAttackType} super attacks does this form have?", default=1
                )
                superFracTotal = 0
                for i in range(numSuperAttacks):
                    if numSuperAttacks > 1:
                        superFrac = clc.prompt(
                            f"What is the probability of this {superAttackType} super attack variant from occuring?",
                            default=1.0,
                        )
                    else:
                        superFrac = 1
                    numEffects = clc.prompt(
                        f"How many effects does this form's {superAttackType} super attack have?", default=1
                    )
                    for j in range(numEffects):
                        effectType = clc.prompt(
                            "What type of effect does the unit get on super?",
                            type=clc.Choice(SUPER_ATTACK_EFFECTS, case_sensitive=False),
                            default="ATK",
                        )
                        activationProbability = clc.prompt(
                            "What is the probability this effect activates when supering?", default=1.0
                        )
                        buff = clc.prompt("What is the value of the buff?", default=0.0)
                        duration = clc.prompt("How many turns does it last for?", default=MAX_TURN)
                        avgSuperAttack.addEffect(effectType, activationProbability, buff, duration, superFrac)
                    superFracTotal += superFrac
                assert superFracTotal == 1, "Invald super attack variant proabilities entered"
            self.superAttacks[superAttackType] = avgSuperAttack


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
    def __init__(self, slot, turn):
        self.slot = slot  # Slot no.
        self.turn = turn
        self.randomKi = KI_SUPPORT  # Constant and Random ki
        # Dictionary for variables which have a 1-1 relationship with StartOfTurn EFFECTS
        self.buff = {
            "Ki": LEADER_SKILL_KI,
            "AEAAT": 0,
            "Guard": 0,
            "Crit": 0,
            "Disable Guard": 0,
            "Evade": 0,
            "Dmg Red against Normals": 0,
        }
        self.p1Buff = {"ATK": LEADER_SKILL_STATS + ATK_DEF_SUPPORT, "DEF": LEADER_SKILL_STATS + ATK_DEF_SUPPORT}
        self.p2Buff = {"ATK": 0, "DEF": 0}
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

    def setState(self, unit, form):
        for ability in form.abilities:
            ability.applyToState(self, unit)
        self.p1Buff["ATK"] = np.maximum(self.p1Buff["ATK"], -1)
        self.p2Buff["ATK"] += form.linkAtkOnSuper
        self.p2Buff["DEF"] = self.p2DefA + self.p2DefB
        self.buff["Crit"] = self.buff["Crit"] + (1 - self.buff["Crit"]) * (
            unit.pHiPoCrit + (1 - unit.pHiPoCrit) * form.linkCrit
        )
        self.buff["Evade"] = self.buff["Evade"] + (1 - self.buff["Evade"]) * (
            unit.pHiPoDodge + (1 - unit.pHiPoDodge) * form.linkDodge
        )
        self.pNullify = self.pNullify + (1 - self.pNullify) * self.pCounterSA
        self.randomKi += (
            self.kiPerOtherTypeOrb * self.numOtherTypeOrbs
            + self.kiPerSameTypeOrb * self.numSameTypeOrbs
            + self.numRainbowOrbs * self.kiPerRainbowKiSphere
            + form.linkKi
        )
        self.buff["Ki"] = min(round(self.buff["Ki"] + self.randomKi), rarity2MaxKi[unit.rarity])
        self.pN, self.pSA, self.pUSA = getAttackDistribution(
            self.buff["Ki"], self.randomKi, form.intentional12Ki, unit.rarity
        )
        self.aaSA = branchAA(-1, len(self.aaPSuper), unit.pHiPoAA, 1, self.aaPSuper, self.aaPGuarantee, unit.pHiPoAA)
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
            specialAttack.applyToState(self, unit)
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
            unit.DEF, self.p1Buff["ATK"], form.linkDef, self.p2DefA, self.p3Buff["DEF"], self.stackedStats["DEF"]
        )
        self.avgDefPostSuper = getDefStat(
            unit.DEF, self.p1Buff["ATK"], form.linkDef, self.p2Buff["DEF"], self.p3Buff["DEF"], self.avgDefMult
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
            NUM_NORMAL_ATTACKS_RECEIVED_BEFORE_ATTACKING[self.slot - 1] * self.normalDamageTakenPreSuper
            + NUM_NORMAL_ATTACKS_RECEIVED_AFTER_ATTACKING[self.slot - 1] * self.normalDamageTakenPostSuper
        ) / (NUM_NORMAL_ATTACKS_RECEIVED[self.slot - 1])
        self.saDamageTaken = (
            NUM_SUPER_ATTACKS_RECEIVED_BEFORE_ATTACKING[self.slot - 1] * self.saDamageTakenPreSuper
            + NUM_SUPER_ATTACKS_RECEIVED_AFTER_ATTACKING[self.slot - 1] * self.saDamageTakenPostSuper
        ) / (NUM_SUPER_ATTACKS_RECEIVED[self.slot - 1])
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
        self.stackedStats = dict(zip(STACK_EFFECTS, np.zeros(len(STACK_EFFECTS))))
        # If want the stacking of initial turn and transform later
        if unit.keepStacking:
            form = unit.forms[0]
            state = self.states[0]
        else:
            state = self
        for stat in STACK_EFFECTS:
            # Update previous stack durations
            for stack in unit.stacks[stat]:
                stack.duration -= RETURN_PERIOD_PER_SLOT[unit.states[-1].slot]
            # Remove them if expired
            unit.stacks[stat] = [stack for stack in unit.stacks[stat] if stack.duration > 0]
            # Add new stacks
            if unit.rarity == "LR":
                # If stack for long enough to last to next turn
                if form.superAttacks["18 Ki"].effects[stat].duration > RETURN_PERIOD_PER_SLOT[state.slot - 1]:
                    unit.stacks[stat].append(
                        Stack(
                            stat,
                            state.pUSA * form.superAttacks["18 Ki"].effects[stat].buff,
                            form.superAttacks["18 Ki"].effects[stat].duration,
                        )
                    )
            if form.superAttacks["12 Ki"].effects[stat].duration > RETURN_PERIOD_PER_SLOT[state.slot - 1]:
                unit.stacks[stat].append(
                    Stack(
                        stat,
                        (state.pSA + state.aaSA) * form.superAttacks["12 Ki"].effects[stat].buff,
                        form.superAttacks["12 Ki"].effects[stat].duration,
                    )
                )
            # Apply stacks
            for stack in unit.stacks[stat]:
                self.stackedStats[stat] += stack.buff

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
                PEAK_TURN,
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
                    "How many different buffs does this active skill have?",
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
                state.stackedStats["ATK"],
                self.form.linkAtkSoT,
                state.p2Buff["ATK"],
                state.p3Buff["ATK"],
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
            state.healing = np.min(state.healing + self.hpRegen, 1)
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

    def applyToState(self, state, unit=None):
        pHaveKi = 1 - ZTP_CDF(self.ki - 1 - state.buff["Ki"], state.randomKi)
        self.effectiveBuff = self.effectiveBuff * pHaveKi
        self.activationProbability *= pHaveKi
        # Check if state is elligible for ability
        if state.turn >= self.start and state.turn <= self.end and state.slot in self.slots:
            # If not a support ability
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
                    case "AdditonalSuper":
                        state.aaPSuper.append(self.activationProbability)
                        state.aaPGuarantee.append(0)
                    case "AAWithChanceToSuper":
                        chanceToSuper = clc.prompt(
                            "What is the chance to super given the additional triggered?",
                            default=0.0,
                        )
                        state.aaPSuper.append(chanceToSuper)
                        state.aaPGuarantee.append(self.activationProbability)
                    case "Ki (Type Ki Sphere)":
                        state.kiPerOtherTypeOrb += self.effectiveBuff
                        state.kiPerSameTypeOrb += self.effectiveBuff


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
        if self.effect in state.buff.keys():
            state.buff[self.effect] += min(
                self.effectiveBuff * (NUM_ATTACKS_RECEIVED_BEFORE_ATTACKING[state.slot - 1] + state.numAttacksReceived),
                self.max,
            )
        else:
            match self.effect:
                case "ATK":
                    state.p2Buff["ATK"] += min(
                        self.effectiveBuff
                        * (NUM_ATTACKS_RECEIVED_BEFORE_ATTACKING[state.slot - 1] + state.numAttacksReceived),
                        self.max,
                    )
                case "DEF":
                    state.p2DefA += np.minimum(
                        (2 * state.numAttacksReceived + NUM_ATTACKS_RECEIVED[state.slot - 1] - 1)
                        * self.effectiveBuff
                        / 2,
                        self.max,
                    )


class AfterAttackReceived(PassiveAbility):
    def __init__(self, form, activationProbability, effect, buff, effectDuration, turnsSinceActivated=0, args=[]):
        super().__init__(form, activationProbability, effect, buff, effectDuration)
        self.turnsSinceActivated = turnsSinceActivated

    def applyToState(self, state, unit=None):
        # state.attacksReceiving is how many attacks the state is expected to recieve not including evades/nullified attacks
        # If buff is a defensive one
        hitFactor = 1
        if self.turnsSinceActivated == 0:
            if self.effect in ["DEF", "Dmg Red"]:
                hitFactor = (
                    state.attacksReceiving - 1
                ) / state.attacksReceiving  # Factor to account for not having the buff on the fist hit
            else:
                hitFactor = np.min(state.attacksReceivingBeforeAttacking, 1)
        # This should return self.activationProbabiltiy if self.turnsActivated = 0
        effectiveBuff = self.buff * hitFactor * geom.cdf(self.turnsSinceActivated + 1, self.activationProbability)
        if self.effect in state.buff.keys():
            state.buff[self.effect] += effectiveBuff
        else:
            match self.effect:
                case "DEF":
                    state.p2DefA += effectiveBuff
        self.turnsSinceActivated += 1
        # If buff lasts till unit's next turn
        if self.effectDuration > self.turnsSinceActivated * RETURN_PERIOD_PER_SLOT[state.slot]:
            self.form.abilities.extend(
                AfterAttackReceived(
                    self.form,
                    self.activationProbability,
                    self.effect,
                    self.effectiveBuff,
                    self.effectDuration,
                    self.turnsSinceActivated,
                )
            )


class PerRainbowOrb(PassiveAbility):
    def __init__(self, form, activationProbability, effect, buff, effectDuration, args=[]):
        super().__init__(form, activationProbability, effect, buff, effectDuration)

    def applyToState(self, state, unit=None):
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

    def applyToState(self, state, unit=None):
        pNullify = self.activationProbability * (1 - (1 - saFracConversion[self.effect]) ** 2)
        state.pNullify = (1 - state.pNullify) * pNullify + (1 - pNullify) * state.pNullify
        if self.hasCounter:
            state.pCounterSA = (1 - state.pCounterSA) * pNullify + (1 - pNullify) * state.pCounterSA


if __name__ == "__main__":
    kit = Unit(1, 1, "DEF", "ADD", "DGE", loadPickle=True)
