import datetime as dt
from dokkanUnitHelperFunctions import *

# TODO:
#  - The stacking penality applies to all super attcks that stack more than one turn: Source Dokkan Wiki
# - Make sure to include TYPE DEF BOOST correctly (HP & lowering Guard modifier) 
# - Instead of asking user how many of something, should ask until they enteran exit key aka while loop instead of for loop
# - How are we dealing with unit-super attacks? I think this works if user specifies the correct activation probabilities
# - Should read up on python optimisation techniques once is running and se how long it takes. But try be efficient you go.
# - I think the 20x3 state matrix needs to be used to compute the best path
# - Whilst the state matrix is the ideal way, for now just assume a user inputed slot for each form
# - Should put at may not be relevant tag onto end of the prompts that may not always be relevant.
# - Should print out relavant parameters back to user, like activationTurn for special ability
# - Group constants so easier to manage
# - Still need to get stats out of links, but can mostly copy whats in dokkanUnit.py
# - Should determine which slot is best for the unit
# - Make separate file where all constants and imports are stored
# - Ideally would just pull data from database, but not up in time for new units. Would be amazing for old units though.
# - Leader skill weight should decrease from 5 as new structure adds more variability between leader skills
# - Make the outputted variables get saved to a file that can be modified later. Also record the inputs if transformed to unrecognizable form. Or can set defaults of quiz as previously input values.
# - Once calculate how many supers do on turn 1, use this in the SBR calculation for debuffs on super. i.e. SBR should be one of the last things to be calculated

##################################################### Helper Functions ############################################################################

def restrictionQuestionaire():
    numRestrictions = clc.prompt(
        "How many different restrictions does this ability have?", default=0
    )
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
            restrictionProbability = 1.0 - maxHealthCDF(
                clc.prompt("What is the maximum HP restriction?", default=0.7)
            )
        elif restrictionType == "Min HP":
            restrictionProbability = maxHealthCDF(
                clc.prompt("What is the minimum HP restriction?", default=0.7)
            )
        elif restrictionType == "Enemy Max HP":
            restrictionProbability = 1.0 - clc.prompt(
                "What is the maximum enemy HP restriction?", default=0.5
            )
        elif restrictionType == "Enemy Min HP":
            restrictionProbability = clc.prompt(
                "What is the minimum enemy HP restriction?", default=0.5
            )
        # Assume independence
        totalRestrictionProbability = (
            1.0 - totalRestrictionProbability
        ) * restrictionProbability + (
            1.0 - restrictionProbability
        ) * totalRestrictionProbability
    return 1.0 - totalRestrictionProbability, turnRestriction


def abilityQuestionaire(
    form, abilityPrompt, abilityClass, parameterPrompts=[], types=[], defaults=[]
):
    parameters = []
    numAbilities = clc.prompt(abilityPrompt, default=0)
    abilities = []
    for i in range(numAbilities):
        for j, parameterPrompt in enumerate(parameterPrompts):
            if len(types) == 0:  # If don't care about prompt choices
                parameters.append(clc.prompt(parameterPrompt))
            else:
                parameters.append(
                    clc.prompt(parameterPrompt, type=types[j], default=defaults[j])
                )
        if issubclass(abilityClass, PassiveAbility):
            effect = clc.prompt(
                "What type of buff does the unit get?",
                type=clc.Choice(EFFECTS, case_sensitive=False),
                default="Raise ATK",
            )
            activationProbability = clc.prompt(
                "What is the probability this ability activates?", default=1.0
            )
            buff = clc.prompt("What is the value of the buff?", default=0.0)
            ability = abilityClass(
                form, activationProbability, effect, buff, parameters
            )
        elif issubclass(abilityClass, SingleTurnAbility):
            ability = abilityClass(form, parameters)
        abilities.append(ability)
    return abilities

######################################################### Classes #################################################################

class Kit:
    def __init__(self, id):
        self.id = id  # unique ID for unit
        self.getConstants()
        self.getSBR()
        self.getForms()
        self.getStates()

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
        self.leader_skill = leaderSkillConversion[
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
                        type=clc.Choice(
                            attDebuffOnAttackConversion.keys(), case_sensitive=False
                        ),
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
                attDebuffPassive *= clc.prompt(
                    "How much is attack lowered passively?", default=0.3
                )

            multipleEnemyBuff = multipleEnemyBuffConversion[
                clc.prompt(
                    "How much of a buff does the unit get when facing multiple enemies?",
                    type=clc.Choice(
                        multipleEnemyBuffConversion.keys(), case_sensitive=False
                    ),
                    default="None",
                )
            ]

            self.sbr = (
                attackAllDebuffConversion[attackAll] * (seal + stun + attDebuffOnAtk)
                + attDebuffPassive
                + multipleEnemyBuff
                + attackAll
            )
        return self.sbr

    def getForms(self):
        startTurn = 1
        self.forms = []
        numForms = clc.prompt("How many forms does the unit have?", default=1)
        for i in range(numForms):
            slot = int(
                clc.prompt(f"Which slot is form # {i + 1} best suited for?", default=2)
            )
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
                            RETURN_PERIOD_PER_SLOT[slot - 1]
                            * round(1 / transformationProbabilityPerTurn),
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
            superAttackEffects = abilityQuestionaire(
                form,
                "How many effects does this unit's 12 ki super attack have?",
                SuperAttack,
                ["How many turns does the effect last for?"],
                [None],
                [1],
            )
            for superAttackEffect in superAttackEffects:
                superAttackEffect.setSuperAttack()
            if self.rarity == "LR":
                form.intentional12Ki = yesNo2Bool[
                    clc.prompt(
                        "Should a 12 Ki be targetted for this form?", default="N"
                    )
                ]
                if not (form.intentional12Ki):
                    ultraSuperAttackEffects = abilityQuestionaire(
                        form,
                        "How many effects does this unit's 18 ki super attack have?",
                        SuperAttack,
                        ["How many turns does the effect last for?"],
                        [None],
                        [1],
                    )
                    for ultraSuperAttackEffect in ultraSuperAttackEffects:
                        ultraSuperAttackEffect.setUltraSuperAttack()
            form.normalCounterMult = counterAttackConversion[
                clc.prompt(
                    "What is the unit's normal counter multiplier?",
                    type=clc.Choice(
                        counterAttackConversion.keys(), case_sensitive=False
                    ),
                    default="NA",
                )
            ]
            form.saCounterMult = counterAttackConversion[
                clc.prompt(
                    "What is the unit's super attack counter multiplier?",
                    type=clc.Choice(
                        counterAttackConversion.keys(), case_sensitive=False
                    ),
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
                    "How many different buffs does the form get within the same turn after receiving an attack?",
                    WithinSameTurnAfterReceivingAttack,
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
            # form.updateRandomKi(start, end) # Compute the average ki each turn which has a random component because need to be able to compute how much ki the unit gets on average for ki dependent effects
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
            form.abilities.extend(
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

    def getStates(self):
        self.states = []
        turn = 1
        formIdx = 0
        while turn <= MAX_TURN:
            form = self.forms[formIdx]
            slot = form.slot
            state = State(slot, turn)
            for ability in form.abilities:
                ability.applyToState(state)
            self.states.append(state)
            turn += RETURN_PERIOD_PER_SLOT[slot - 1]
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
        self.abilities = (
            []
        )  # This will be a list of Ability objects which will be iterated through each state to call applyToState.

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
            self.linkAtkSoT += link.attSoT
            self.linkDef += link.defence
            self.linkCrit += link.crit
            self.linkAtkOnSuper += link.att_OnSuper
            self.linkDodge += link.dodge
            self.linkDmgRed += link.dmgRed
            self.linkHealing += link.healing
        self.linkCommonality /= MAX_NUM_LINKS


class Link:
    def __init__(self, name, commonality):
        self.name = name
        i = LINK_NAMES.index(self.name)
        self.ki = float(LINK_DATA[i, 10])
        self.attSoT = float(LINK_DATA[i, 11])
        self.defence = float(LINK_DATA[i, 12])
        self.att_OnSuper = float(LINK_DATA[i, 13])
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
        self.p1Atk = LEADER_SKILL_STATS
        self.p1Def = LEADER_SKILL_STATS  # Start of turn stats (Phase 1)
        self.p2Atk = 0.0  # Phase 2 ATK
        self.p2DefA = 0.0
        self.p2DefB = 0.0  # Phase 2 DEF (Before and after attacking)
        self.AEAAT = 0.0  # Probability for attacks effective against all types
        self.guard = 0.0  # Probability of guarding
        self.crit = 0.0  # Probability of performing a critical hit
        self.pEvade = 0.0  # Probability of evading
        self.healing = 0.0  # Fraction of health healed every turn
        self.support = 0.0  # Support score
        self.pNullify = 0.0  # Probability of nullifying all enemy super attacks
        self.aaPSuper = []
        self.aaPGuarantee = (
            []
        )  # Probabilities of doing additional super attacks and guaranteed additionals
        self.dmgRedA = 0.0
        self.dmgRedB = 0.0  # Damage reduction before and after attacking
        self.pCounterSA = 0.0  # Probability of countering an enemy super attack
        self.numAttacksReceived = 0  # Number of attacks received so far in this form. Assuming update the state.numAttacksReceievd after the abilities have been processed for that turn

    def updateRandomKi(self, form):
        kiCollect = (
            self.kiPerOtherTypeOrb * self.numOtherTypeOrbs
            + self.kiPerSameTypeOrb * self.numSameTypeOrbs
            + self.numRainbowOrbs * self.kiPerRainbowKiSphere
        )
        self.randomKi += kiCollect + form.linkKi


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


class ActiveSkillAttack(SingleTurnAbility):
    def __init__(self, form, args):
        super().__init__(form)
        self.attackMultiplier = args[0]
        self.attackBuff = args[1]
        self.activeAttackTurn = self.activationTurn
        self.activeMult = (
            specialAttackConversion[self.attackMultiplier] + self.attackBuff
        )
        self.form.abilities.extend(
            abilityQuestionaire(
                self.form,
                "How many additional single-turn buffs does this active skill attack have?",
                TurnDependent,
                [
                    "This is the activation turn. Please press enter to continue",
                    "This is the form's next turn. Please press enter to continue",
                ],
                [None, None],
                [
                    self.activationTurn,
                    self.activationTurn + RETURN_PERIOD_PER_SLOT[self.form.slot],
                ],
            )
        )

    def applyToState(self, state):
        # TODO
        # Should apply the apt for an active skill attack on the activation turn
        pass


class Revive(SingleTurnAbility):
    def __init__(self, form, args):
        super().__init__(form)
        self.hpRegen = args[0]
        self.isThisCharacterOnly = args[1]
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

    def applyToState(self, state):
        if state.turn == self.activationTurn:
            state.healing = np.min(state.healing + self.hpRegen, 1.0)
        if self.isThisCharacterOnly:
            state.support += REVIVE_UNIT_SUPPORT_BUFF
        else:
            state.support += REVIVE_ROTATION_SUPPORT_BUFF


class PassiveAbility(Ability):
    def __init__(self, form, activationProbability, effect, buff):
        super().__init__(form)
        self.activationProbability = activationProbability
        self.effect = effect
        self.buff = buff * activationProbability


class SuperAttack(PassiveAbility):
    def __init__(self, form, activationProbability, effect, buff, args):
        super().__init__(form, activationProbability, effect, buff)
        self.effectDuration = args[0]

    def setSuperAttack(self):
        match self.effect:
            case "Raise ATK":
                self.form.sa12AtkBuff += (
                    self.buff
                )  # += here for unit super attack probability weightings
                self.form.sa12AtkStacks = (
                    self.effectDuration
                )  # Assuming this doesn't vary in a unit super attack
            case "Raise DEF":
                self.form.sa12DefBuff += (
                    self.buff
                )  # += here for unit super attack probability weightings
                self.form.sa12DefStacks = (
                    self.effectDuration
                )  # Assuming this doesn't vary in a unit super attack
            case "Critical Hit":
                self.form.sa12Crit += (
                    self.buff
                )  # += here for unit super attack probability weightings
        numUnitSuperAttacks = clc.prompt(
            "How many 12 ki unit super attacks does this form have?", default=0
        )
        for unitSuperAttack in range(numUnitSuperAttacks):
            unitSuperAttackEffects = abilityQuestionaire(
                self.form,
                "How many effects does this unit super attack have?",
                SuperAttack,
                ["How many turns does the effect last for?"],
                [None],
                [1],
            )
            for unitSuperAttackEffect in unitSuperAttackEffects:
                unitSuperAttackEffect.setSuperAttack()

    def setUltraSuperAttack(self):
        match self.effect:
            case "Raise ATK":
                self.form.sa18AtkBuff += (
                    self.buff
                )  # += here for unit super attack probability weightings
                self.form.sa18AtkStacks = (
                    self.effectDuration
                )  # Assuming this doesn't vary in a unit super attack
            case "Raise DEF":
                self.form.sa18DefBuff += (
                    self.buff
                )  # += here for unit super attack probability weightings
                self.form.sa18DefStacks = (
                    self.effectDuration
                )  # Assuming this doesn't vary in a unit super attack
            case "Disable Action":
                self.form.sa18Disable = bool(self.buff)
            case "Critical Hit":
                self.form.sa18Crit += (
                    self.buff
                )  # += here for unit super attack probability weightings


class StartOfTurn(PassiveAbility):
    def __init__(
        self,
        form,
        activationProbability,
        effect,
        buff,
        start=0,
        end=MAX_TURN,
        ki=0,
        slots=SLOTS,
    ):
        super().__init__(form, activationProbability, effect, buff)
        self.start = start
        self.end = end
        self.ki = ki
        self.slots = slots

    def applyToState(self, state):
        pHaveKi = 1.0 - ZTP_CDF(self.ki - 1 - state.constantKi, state.randomKi)
        self.buff = self.buff * pHaveKi
        self.activationProbability *= pHaveKi
        if (
            state.turn >= self.start
            and state.turn <= self.end
            and state.slot in self.slots
        ):
            match self.effect:
                case "Ki":
                    state.constantKi += self.buff
                case "ATK":
                    state.p1Atk += self.buff
                case "DEF":
                    state.p1Def += self.buff
                case "Guard":
                    state.guard += self.buff
                case "Critical Hit":
                    state.crit += self.buff
                case "Evasion":
                    state.pEvade += self.buff
                case "Disable Action":
                    state.pNullify = (
                        P_NULLIFY_FROM_DISABLE_ACTIVE * (1.0 - state.pNullify)
                        + (1.0 - P_NULLIFY_FROM_DISABLE_ACTIVE) * state.pNullify
                    )
                case "Raise Ki (Type Ki Sphere)":
                    state.kiPerTypeOrb += self.buff
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
                case "Attack Effective to All":
                    state.AEAAT += self.activationProbability


class TurnDependent(StartOfTurn):
    def __init__(self, form, activationProbability, effect, buff, args):
        start = args[0]
        end = args[1]
        super().__init__(
            form, activationProbability, effect, buff, start=start, end=end
        )


class KiDependent(StartOfTurn):
    def __init__(self, form, activationProbability, effect, buff, args):
        ki = args[0]
        super().__init__(form, activationProbability, effect, buff, ki=ki)


class SlotDependent(StartOfTurn):
    def __init__(self, form, activationProbability, effect, buff, args):
        slots = args[0]
        super().__init__(form, activationProbability, effect, buff, slots=slots)


class PerAttackReceived(PassiveAbility):
    def __init__(self, form, activationProbability, effect, buff, args):
        super().__init__(form, activationProbability, effect, buff)
        self.max = args[0]

    def applyToState(self, state):
        match self.effect:
            case "Ki":
                state.constantKi += np.minimum(
                    self.buff
                    * (
                        NUM_ATTACKS_RECEIVED_BEFORE_ATTACKING[state.slot]
                        + state.numAttacksReceived
                    ),
                    self.max,
                )
            case "ATK":
                state.p2Atk += np.minimum(
                    self.buff
                    * (
                        NUM_ATTACKS_RECEIVED_BEFORE_ATTACKING[state.slot]
                        + state.numAttacksReceived
                    ),
                    self.max,
                )
            case "DEF":
                state.p2DefA += np.minimum(
                    (
                        2 * state.numAttacksReceived
                        + NUM_ATTACKS_RECEIVED[state.slot]
                        - 1
                    )
                    * self.buff
                    / 2,
                    self.max,
                )
            case "Critical Hit":
                state.crit += np.minimum(
                    self.buff
                    * (
                        NUM_ATTACKS_RECEIVED_BEFORE_ATTACKING[state.slot]
                        + state.numAttacksReceived
                    ),
                    self.max,
                )


class WithinSameTurnAfterReceivingAttack(PassiveAbility):
    def __init__(self, form, activationProbability, effect, buff, args):
        super().__init__(form, activationProbability, effect, buff)

    def applyToState(self, state):
        match self.effect:
            case "DEF":
                state.p2DefA += (
                    self.buff
                    * (NUM_ATTACKS_RECEIVED[state.slot] - 1)
                    / NUM_ATTACKS_RECEIVED[state.slot]
                )
            case "Attack Effective to All":
                state.AEAAT = self.buff * np.minimum(
                    NUM_ATTACKS_RECEIVED_BEFORE_ATTACKING[state.slot], 1.0
                )


class PerRainbowOrb(PassiveAbility):
    def __init__(self, form, activationProbability, effect, buff, args):
        super().__init__(form, activationProbability, effect, buff)

    def applyToState(self, state):
        buffFromRainbowOrbs = self.buff * state.numRainbowOrbs
        match self.effect:
            case "Critical Hit":
                state.crit += buffFromRainbowOrbs
            case "Damage Reduction":
                state.dmgRedA += buffFromRainbowOrbs
                state.dmgRedB += buffFromRainbowOrbs
            case "Evasion":
                state.pEvade += buffFromRainbowOrbs


class Nullification(PassiveAbility):
    def __init__(self, form, activationProbability, effect, buff, args):
        super().__init__(form, activationProbability, effect, buff)
        self.hasCounter = args[0]

    def applyToState(self, state):
        pNullify = self.activationProbability * (
            1.0 - (1.0 - saFracConversion[self.effect]) ** 2
        )
        state.pNullify = (1.0 - state.pNullify) * pNullify + (
            1.0 - pNullify
        ) * state.pNullify
        if self.hasCounter:
            state.pCounterSA = (1.0 - state.pCounterSA) * pNullify + (
                1.0 - pNullify
            ) * state.pCounterSA


if __name__ == "__main__":
    kit = Kit(1)
