import click as clc
import datetime as dt

# TODO:
# - Make separate file where all constants and imports are stored
# - Ideally would just pull data from database, but not up in time for new units. Would be amazing for old units though.
# - Leader skill weight should decrease from 5 as new structure adds more variability between leader skills

# CONSTANTS
YES_NO = ['Y', 'N']
EXCLUSIVITIES = ['DF', 'DFLR', 'LR', 'CLR', 'BU', 'F2P', 'F2PLR', 'Super Strike']
CLASSES = ['S', 'E']
TYPES = ['AGL', 'INT', 'PHY', 'STR', 'TEQ']
ATT_DEBUFF_PASSIVE_CONVERSION_GRADIENT = 10 # 10% attack down for 2 turns = SBR score of +1
LEADER_SKILL_TIERS = ['<150%', '1 x 150%', '2 x 150%', '2 x 150-170% / 1 x 170%', '2 x 170% / 1 x 180%', '200% limted', '200% small', '200% medium', '200% large']
LEADER_SKILL_SCORES = [0, 1, 2, 4, 5, 7, 8, 9, 10] # [-]
DEBUFF_DURATIONS = ['0', '1', '2'] # [turns]
SEAL_SCORE_PER_TURN = [0, 0.25, 0.75] # [SBR metric/chance to seal]
STUN_SCORE_PER_TURN = [0, 0.5, 1.5] # [SBR metric/chance to stun]
ATT_DEBUFF_SCORE_PER_TURN = [0, 1/3, 1] # [SBR metirc/attack debuff score]
ATT_DEBUFF_ON_ATT_TYPES = ['Lowers', 'Greatly Lowers']
ATT_DEBUFF_ON_ATT_SCORE = [0.25, 0.5] # [attack debuff scrore for lower and greatly lower]
MULTIPLE_ENEMY_BUFF_TIERS = ['Minor', 'Moderate', 'Major', 'Huge']
MULTIPLE_ENEMY_BUFF_SCORES = [0.25, 0.5, 1, 2] # [SBR metric]
ATTACK_ALL_SCORE = [0, 1] # [SBR metric]
ATTACK_ALL_DEBUFF_FACTOR = [1, 3] # [-]
KI_MODIFIERS_12 = [1.4, 1.45, 1.5, 1.6] # [-]
SUPER_ATTACK_MULTIPLIER_NAMES = ['Destructive', 'Supreme', 'Immense', 'Colossal', 'Mega-Colossal']
COUNTER_ATTACK_MULTIPLIER_NAMES = ['Tremendous', 'Furocious']
COUNTER_ATTACK_MULTIPLIERS = [3.0, 4.0]


# Helper dicts
yesNo2Bool = dict(zip(YES_NO, [True, False]))
leaderSkillConversion = dict(zip(LEADER_SKILL_TIERS,LEADER_SKILL_SCORES))
sealTurnConversion = dict(zip(DEBUFF_DURATIONS,SEAL_SCORE_PER_TURN))
stunTurnConversion = dict(zip(DEBUFF_DURATIONS,STUN_SCORE_PER_TURN))
attDebuffTurnConversion = dict(zip(DEBUFF_DURATIONS,ATT_DEBUFF_SCORE_PER_TURN))
attDebuffOnAttackConversion = dict(zip(ATT_DEBUFF_ON_ATT_TYPES,ATT_DEBUFF_ON_ATT_SCORE))
multipleEnemyBuffConversion = dict(zip(MULTIPLE_ENEMY_BUFF_TIERS,MULTIPLE_ENEMY_BUFF_SCORES))
attackAllConversion = dict(zip(YES_NO, ATTACK_ALL_SCORE))
attackAllDebuffConversion = dict(zip(ATTACK_ALL_SCORE, ATTACK_ALL_DEBUFF_FACTOR))
counterAttackConversion = dict(zip(COUNTER_ATTACK_MULTIPLIER_NAMES,COUNTER_ATTACK_MULTIPLIERS))

@clc.group(chain=True)
def main():
    clc.echo('Hello, this program will guide you through inputting the data required to enter a Dokkan unit into the database')


@main.command('InitialQuestionaire')
def InitialQuestionaire():
    exclusivity = clc.prompt("What is the unit's exclusivity?", type=clc.Choice(EXCLUSIVITIES, case_sensitive=False), default='DF')
    name = clc.prompt("What is the unit's name?", default='Super Saiyan Goku')
    _class = clc.prompt("What is the unit's class?", type=clc.Choice(CLASSES, case_sensitive=False), default='AGL')
    _type = clc.prompt("What is the unit's type?", type=clc.Choice(TYPES, case_sensitive=False), default='Super')
    eza = yesNo2Bool[clc.prompt("Has the unit EZA'd?", type=clc.Choice(YES_NO, case_sensitive=False), default='N')]
    jp_date = dt.datetime.strptime(clc.prompt("When did the unit release on the Japanse version of Dokkan? (MM/YY)", default='01/24'),'%m/%y')
    gbl_date = dt.datetime.strptime(clc.prompt("When did the unit release on the Global version of Dokkan? (MM/YY)", default='01/24'),'%m/%y')
    hp = clc.prompt("What is the unit's base HP stat?", default=0)
    att = clc.prompt("What is the unit's base ATT stat?", default=0)
    _def = clc.prompt("What is the unit's base DEF stat?", default=0)
    leader_skill = leaderSkillConversion[clc.prompt("How would you rate the unit's leader skill on a scale of 1-10?\n200% limited - e.g. LR Hatchiyak Goku\n 200% small - e.g. LR Metal Cooler\n 200% medium - e.g. PHY God Goku\n 200% large - e.g. LR Vegeta & Trunks\n", type=clc.Choice(leaderSkillConversion.keys(), case_sensitive=False), default='<150%')]
    teams = clc.prompt("How many categories is the unit on? If the unit's viability is limited to certain categories, take this into account.", default=1)
    ki_mod_12 = clc.prompt("What is the unit's 12 ki attck modifer?", type=clc.Choice(KI_MODIFIERS_12), default=1.5)
    sa_mult_12 = clc.prompt("What is the unit's 12 ki super attack multiplier?", type=clc.Choice(SUPER_ATTACK_MULTIPLIER_NAMES), default='Immense')
    counter_mult = counterAttackConversion[clc.prompt("What is the unit's counter-attack multiplier?", type=clc.Choice(COUNTER_ATTACK_MULTIPLIER_NAMES), default='Tremendous')]
    if 'LR' in exclusivity:
        sa_mult_18 = clc.prompt("What is the unit's 18 ki super attack multiplier?", type=clc.Choice(SUPER_ATTACK_MULTIPLIER_NAMES), default='Mega-Colossal')




@main.command('SBRQuestionaire')
@clc.option('--sbr_abilities', type=clc.Choice(yesNo2Bool.keys(), case_sensitive=False), prompt="Does the unit have any SBR abilities?")
def SBRQuestionaire(sbr_abilities):
    sbr = 0.0
    if sbr_abilities:
        attack_all = attackAllConversion[clc.prompt("Does the unit attack all enemies on super?",type=clc.Choice(yesNo2Bool.keys(),case_sensitive=False))]

        seal = sealTurnConversion[int(clc.prompt("How many turns does the unit seal for?", type=clc.Choice(sealTurnConversion.keys())))]
        if seal != 0:
            seal *= float(clc.prompt("What is the unit's chance to seal?",type=float)) # Scale by number of enemies for all enemy seal, same for stun

        stun = stunTurnConversion[int(clc.prompt("How many turns does the unit stun for?", type=clc.Choice(stunTurnConversion.keys())))]
        if stun != 0:
            stun *= float(clc.prompt("What is the unit's chance to stun?", type=float))
        
        att_debuff_on_att = attDebuffTurnConversion[int(clc.prompt("How many turns does the unit lower the enemy attack by attacking?", type=clc.Choice(attDebuffTurnConversion.keys())))]
        if att_debuff_on_att != 0:
            att_debuff_on_att *= attDebuffOnAttackConversion[int(clc.prompt("How much is attack lowered by on attack?", type=clc.Choice(attDebuffOnAttackConversion.keys())))]

        att_debuff_passive = attDebuffTurnConversion[int(clc.prompt("How many turns does the unit lower the enemy attack passively?", type=clc.Choice(attDebuffTurnConversion.keys())))]
        if att_debuff_passive != 0:
            att_debuff_passive *= float(clc.prompt("How much is attack lowered passively?", type=float))
        
        multiple_enemy_buff = multipleEnemyBuffConversion[clc.prompt("How much of a buff does the unit get when facing multiple enemies?",type=clc.Choice(multipleEnemyBuffConversion.keys()))]
        
        sbr += attackAllConversion[attack_all] * (seal + stun + att_debuff_on_att) + att_debuff_passive + multiple_enemy_buff + attack_all

    return sbr
#TODO make another command that goes through each turn 1-10 for those parameters
#TODO make the outputted variables get saved to a file that can be modified later. Also record the inputs if transformed to unrecognizable form.
#TODO Once calculate how many supers do on turn 1, use this in the SBR calculation for debuffs on super. i.e. SBR should be one of the last things to be calculated

if __name__ == '__main__':
    main()
