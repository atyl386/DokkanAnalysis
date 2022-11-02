import numpy as np
from datetime import datetime
from scipy.stats import poisson
# Make a modelling parameters file and put the below parameters in it
# Make drop down lists for input files for cells that have discrete options, e.g. Links, SA multipliers
# If want to increase efficiency can save Objects with Pickle module - probably also want to change class methods to save outputs as attributes
# On ki collect assume on average get 3.5 type orbs (50% same type, 50% other type) and 1 rainbow orb ->6.25 ki on average
# TODO
# Pikkon Super Strike
# Path to Ultimate Power Event
# Gamma 1 & 2 Dokkan Events
turnMax = 10
leaderSkillBuff = 4
leaderSkillKi = 6
avgSupport = 0.2
avgKiSupport = 1
nTeamsMax = 20
avgTypeAdvantage = 1.131725
avgTypeMod = 1/avgTypeAdvantage
avgGuardFactor = 0.16926
guardMod = 0.45
dodgeCancelFrac = 0.1
kiSuperFrac = 0.55
MeleeSuperFrac = 0.13
CritMultiplier = 2.03
SEaaTMultiplier = 1.5
maxNormalDamage = np.append(np.linspace(300000,530000,4),[530000]*(turnMax-4),axis=0)
maxSADamage = np.append(np.linspace(812000,1855000,4),[1855000]*(turnMax-4),axis=0)
HP_PHY = np.array([[2000,3700,4000,4700,5000],[2000,3300,3600,3910,4600]])
HP_STR = np.array([[2000,4100,4400,5100,5400],[2000,3300,3600,3910,4600]])
HP_AGL = np.array([[2000,3700,4000,4700,5000],[2000,4100,4400,4710,5400]])
HP_TEQ = np.array([[2000,4100,4400,5100,5400],[2000,3700,4000,4310,5000]])
HP_INT = np.array([[2000,3700,4000,4700,5000],[2000,3700,4000,4310,5000]])
HP_F2P = np.array([[3000,3240,3000,3240,3000],[2760,2760,3240,3000,3000]])
HP_SA_Mult = [6,7,8,14,15]
def PoissonCDF(x,mu):
    return (poisson.pmf(x,mu)-poisson.pmf(0,mu))/(1-poisson.pmf(0,mu))
def SAMultiplier(multiplier,EZA,exclusivity,nCopies,nStacks,SA_Att):
    stackingPenalty=0
    if(exclusivity=='Super Strike'):
        baseMultiplier = 6.3
    else:
        if(EZA):
            match multiplier:
                case 'Supreme':
                    baseMultiplier = 5.3
                case 'Immense':
                    baseMultiplier = 6.3
                case 'Colossal':
                    baseMultiplier = 4.5
                case 'Mega-Colossal':
                    baseMultiplier = 6.2
        else:
            match multiplier:
                case 'Supreme':
                    baseMultiplier = 4.3
                case 'Immense':
                    baseMultiplier = 5.05
                case 'Colossal':
                    baseMultiplier = 4.25
                case 'Mega-Colossal':
                    baseMultiplier = 5.7
    if (nStacks==turnMax): # If infinite stacker
        stackingPenalty = SA_Att
    return baseMultiplier+0.05*HP_SA_Mult[nCopies-1]-stackingPenalty
def KiMultiplier(base,ki):
    if ki<=12:
        return 1
    else:
        return (np.linspace(base,2,12))[ki-13]
def AttackDistribution(constantKi,randomKi,intentional12Ki,rarity):
    Pr_N = PoissonCDF(max(12-constantKi,0),randomKi)
    if(intentional12Ki or rarity!='LR'):
        Pr_12Ki = 1-Pr_N
        Pr_18Ki = 0
    else:
        Pr_18Ki = 1-PoissonCDF(max(17-constantKi,0),randomKi)
        Pr_12Ki = 1-Pr_N-Pr_18Ki
    return [Pr_N, Pr_12Ki, Pr_18Ki]
class Unit:
    def __init__(self,ID,nCopies,HPS,skillOrbs):
        self.ID = str(ID)
        self.nCopies = nCopies
        self.HPS = HPS
        self.skillOrbs = skillOrbs
    def HP_Stats(self):
        match self.kit.type:
            case 'PHY':
                if (self.kit.exclusivity=='F2P'):
                    return HP_F2P[:,0]
                else:
                    return HP_PHY[:,self.nCopies-1]
            case 'STR':
                if (self.kit.exclusivity=='F2P'):
                    return HP_F2P[:,1]
                else:
                    return HP_STR[:,self.nCopies-1]
            case 'AGL':
                if (self.kit.exclusivity=='F2P'):
                    return HP_F2P[:,2]
                else:
                    return HP_AGL[:,self.nCopies-1]
            case 'TEQ':
                if (self.kit.exclusivity=='F2P'):
                    return HP_F2P[:,3]
                else:
                    return HP_TEQ[:,self.nCopies-1]
            case 'INT':
                if (self.kit.exclusivity=='F2P'):
                    return HP_F2P[:][4]
                else:
                    return HP_INT[:,self.nCopies-1]
    def SkillOrb_Stats(self):
        if(self.skillOrbs == 'A'):
            return [500,0]
        elif(self.skillOrbs == 'D'):
            return [0,500]
        else:
            raise Exception("Invalid Skill Orb entered")
    def HP_P_AA(self):
        INT_penalty = 0
        if(self.kit.type=='INT'):
            INT_penalty = 0.1
        if(self.HPS[0]=='A'):
            if(self.nCopies>2):
                return 0.5
            elif(self.nCopies==2):
                return 0.28
            else:
                return 0.1
        elif(self.HPS[1]=='A'):
            if(self.nCopies>2):
                return 0.22-INT_penalty
            elif(self.nCopies==2):
                return 0.16-INT_penalty
            else:
                return 0.1-INT_penalty
        elif(self.type=='PHY' or self.type=='AGL'):
            return 0.1
        else:
            return 0
    def HP_P_Crit(self):
        INT_penalty = 0
        if(self.kit.type=='INT'):
            INT_penalty = 0.1
        if(self.HPS[0]=='C'):
            if(self.nCopies>2):
                return 0.5
            elif(self.nCopies==2):
                return 0.28
            else:
                return 0.1
        elif(self.HPS[1]=='C'):
            if(self.nCopies>2):
                return 0.22-INT_penalty
            elif(self.nCopies==2):
                return 0.16-INT_penalty
            else:
                return 0.1-INT_penalty
        elif(self.type=='STR' or self.type=='TEQ'):
            return 0.1
        else:
            return 0
    def HP_P_Dodge(self):
        if(self.HPS[0]=='D'):
            if(self.nCopies>2):
                return 0.25
            elif(self.nCopies==2):
                return 0.14
            else:
                return 0.05
        elif(self.HPS[1]=='D'):
            if(self.nCopies>2):
                return 0.11
            elif(self.nCopies==2):
                return 0.08
            else:
                return 0.05
        elif(self.kit.type=='INT'):
            return 0.05
        else:
            return 0
class TUR(Unit):
    def __init__(self,ID,nCopies,HPS,skillOrbs):
        super().__init__(ID,nCopies,HPS,skillOrbs)
        self.kit = Kit(self.ID,"TUR").getKit()
class LR(Unit):
    def __init__(self,ID,nCopies,HPS,skillOrbs):
        super().__init__(ID,nCopies,HPS,skillOrbs)
        self.kit = Kit(self.ID,"LR").getKit()
class Kit:
    def __init__(self,ID,rarity):
        self.ID = ID
        self.rarity = rarity
        self.links = np.array([[None]*turnMax for i in range(7)])
    def getKit(self):
        filepath = 'C:/Users/Tyler/OneDrive/Documents/Gaming/DokkanKits/'+self.ID+'.csv'
        file = open(filepath)
        kitData = np.genfromtxt(file,dtype='str',delimiter=',',skip_header=True)
        for i in range(17):
            match kitData[i,0]:
                case 'Exclusivity':
                    self.exclusivity = kitData[i,1]
                case 'Name':
                    self.name = kitData[i,1]
                case 'Class':
                    self.Class = kitData[i,1]
                case 'Type':
                    self.type = kitData[i,1]
                case 'EZA':
                    self.EZA = bool(int(kitData[i,1]))
                case 'JP Release':
                    self.JP_releaseDate = datetime.strptime(kitData[i,1],'%d/%m/%Y')
                case 'GLB Release':
                    self.GLB_releaseDate = datetime.strptime(kitData[i,1],'%d/%m/%Y')
                case 'Att':
                    self.attack = int(kitData[i,1])
                case 'Def':
                    self.defence = int(kitData[i,1])
                case 'Leader Skill':
                    self.leaderSkill = float(kitData[i,1])
                case 'Teams':
                    self.nTeams = int(kitData[i,1])
                case 'SBR':
                    self.SBR = float(kitData[i,1])
                case 'Ki Mod 12':
                    self.kiMod_12 = float(kitData[i,1])
                case 'SA Mult 12':
                    self.SA_Mult_12 = kitData[i,1]
                case 'SA Mult 18':
                    if(self.rarity == 'LR'):
                        self.SA_Mult_18 = kitData[i,1]
                case 'Counter Mod':
                    self.counterMod = float(kitData[i,1])
                case 'Avg Super Per Turn':
                    self.avgSupersPerTurn = float(kitData[i,1])
        for i in range(17,len(kitData)):
            buildUpTime = int(kitData[i,1])
            extended = np.append(kitData[i,2:buildUpTime+1],[kitData[i,buildUpTime+1]]*(turnMax-buildUpTime+1),axis=0)
            match kitData[i,0]:
                case 'P1 Att':
                    self.P1_Att = extended.astype('float64')
                case 'P1 Def':
                    self.P1_Def = extended.astype('float64')
                case 'P2 Att':
                    self.P2_Att = extended.astype('float64')
                case 'P2A Def':
                    self.P2A_Def = extended.astype('float64')
                case 'P2B Def':
                    self.P2B_Def = extended.astype('float64')
                case 'P3 Att':
                    self.P3_Att = extended.astype('float64')
                case 'P3 Def':
                    self.P3_Def = extended.astype('float64')
                case 'SA 12 Att':
                    self.SA_12_Att = extended.astype('float64')
                case 'SA 12 Att Stacks':
                    self.SA_12_Att_Stacks = extended.astype('int32')
                case 'SA 12 Def':
                    self.SA_12_Def = extended.astype('float64')
                case 'SA 12 Def Stacks':
                    self.SA_12_Def_Stacks = extended.astype('int32')
                case 'SA 18 Att':
                    if(self.rarity == 'LR'):
                        self.SA_18_Att = extended.astype('float64')
                case 'SA 18 Att Stacks':
                    self.SA_18_Att_Stacks = extended.astype('int32')
                case 'SA 18 Def':
                    if(self.rarity == 'LR'):
                        self.SA_18_Def= extended.astype('float64')
                case 'SA 18 Def Stacks':
                    if(self.rarity == 'LR'):
                        self.SA_18_Def_Stacks= extended.astype('int32')
                case 'Link 1':
                    self.links[0][:] = [Link(name).getLink() for name in extended]
                case 'Link 2':
                    self.links[1][:] = [Link(name).getLink() for name in extended]
                case 'Link 3':
                    self.links[2][:] = [Link(name).getLink() for name in extended]
                case 'Link 4':
                    self.links[3][:] = [Link(name).getLink() for name in extended]
                case 'Link 5':
                    self.links[4][:] = [Link(name).getLink() for name in extended]
                case 'Link 6':
                    self.links[5][:] = [Link(name).getLink() for name in extended]
                case 'Link 7':
                    self.links[6][:] = [Link(name).getLink() for name in extended]
                case 'Ki Hungry':
                    self.kiHungry = extended.astype('float64')
                case 'Passive Ki':
                    self.passiveKi = extended.astype('float64')
                case 'Collect Ki':
                    self.collectKi = extended.astype('float64')
                case 'Intentional 12 Ki':
                    self.intentional12Ki = extended.astype('float64') 
                case 'Healing':
                    self.healing = extended.astype('float64')
                case 'Support':
                    self.support = extended.astype('float64')
                case 'Special':
                    self.special = extended.astype('float64')
                case 'P Guard':
                    self.P_guard = extended.astype('float64')
                case 'Dmg Red':
                    self.dmgRed = extended.astype('float64')
                case 'P Dodge':
                    self.P_dodge = extended.astype('float64')
                case 'P Counter Normal':
                    self.P_counterNormal = extended.astype('float64')
                case 'P Counter SA':
                    self.P_counterSA = extended.astype('float64')
                case 'P Nullify':
                    self.P_nullify = extended.astype('float64')
                case 'AA P Super':
                    listOfLists = [[] for i in range(turnMax)]
                    for i in range(turnMax):
                        elements = extended[i].split()
                        if (len(elements)>1):
                            listOfLists[i] = (elements[1:-1]).astype('float64')
                    self.AA_P_super = listOfLists
                case 'AA P Guarantee':
                    listOfLists = [[] for i in range(turnMax)]
                    for i in range(turnMax):
                        elements = extended[i].split()
                        if (len(elements)>1):
                            listOfLists[i] = (elements[1:-1]).astype('float64')
                    self.AA_P_guarantee = listOfLists
                case 'Passive Crit':
                    self.passiveCrit = extended.astype('float64')
                case 'P SEaaT':
                    self.P_SEaaT = extended.astype('float64')
        file.close()
        return self
class Link:
    def __init__(self,name):
        self.name = name
    def getLink(self):
        filepath = 'C:/Users/Tyler/OneDrive/Documents/Gaming/LinkTable.csv'
        file = open(filepath)
        linkData = np.genfromtxt(file,dtype='str',delimiter=',',skip_header=True)
        names = list(linkData[:,0])
        i = names.index(self.name)
        self.ki = float(linkData[i,1])
        self.att_SoT = float(linkData[i,2])
        self.defence = float(linkData[i,3])
        self.att_OnSuper = float(linkData[i,4])
        self.crit = float(linkData[i,5])
        self.dmgRed = float(linkData[i,6])
        self.dodge = float(linkData[i,7])
        self.healing = float(linkData[i,8])
        self.commonality = float(linkData[i,9])
        file.close()
        return self
class Evaluator:
    # First create attributes some singular, others for each turn
    # Then have different weightings for each based on SBR, FL, Red Zone etc.
    def __init__(self,attributes):
        self.attributes = attributes

class Factor():
     def __init__(self,SBR,FL,RZ,overall):
        self.SBR = SBR
        self.FL = FL
        self.RZ = RZ
        self.overall = overall
class TurnBasedFactor(Factor):
    def __init__(self,turn,SBR,FL,RZ,overall):
        super().__init__(SBR,FL,RZ,overall)
        self.turn = turn
class TurnBasedHelper():
    def __init__(self,turn):
        self.turn = turn
class LeaderSkill(Factor):
    def __init__(self,SBR=0,FL=0,RZ=0,overall=0):
        super().__init__(SBR,FL,RZ,overall)
    def calculate(self,unit):
        return unit.kit.leaderSkill
class Useability(Factor):
    def __init__(self,SBR=0,FL=0,RZ=0,overall=0):
        super().__init__(SBR,FL,RZ,overall)
    def calculate(self,unit):
        return unit.kit.nTeams/nTeamsMax*(unit.kit.support[0]+Links_Commonality(1).calculate(unit))
class SBR(Factor):
    def __init__(self,SBR=0,FL=0,RZ=0,overall=0):
        super().__init__(SBR,FL,RZ,overall)
    def calculate(self,unit):
        return unit.kit.SBR
class Offense(TurnBasedFactor):
    def __init__(self,turn,SBR=0,FL=0,RZ=0,overall=0):
        super().__init__(turn,SBR,FL,RZ,overall)
    def calculate(self,unit):
        apt = APT(self.turn).calculate(unit)
        return apt
        # Need to divide this by the max APT, do this once have stored each unit, so will need to save APT undivided too
class NormalDefence(TurnBasedFactor):
    def __init__(self,turn,SBR=0,FL=0,RZ=0,overall=0):
        super().__init__(turn,SBR,FL,RZ,overall)
    def calculate(self,unit):
        P_dodge = unit.kit.P_dodge[self.turn-1] + (1-unit.kit.P_dodge[self.turn-1]) * (unit.HP_P_Dodge()+(1-unit.HP_P_Dodge())*Links_Dodge(self.turn).calculate(unit))
        dmgRed = DmgRed(self.turn).calculate(unit)
        avgDefPostSuper = AvgDefPostSuper(self.turn).calculate(unit)
        return min(-(1-(1-dodgeCancelFrac)*P_dodge)*(unit.kit.P_guard[self.turn-1]*(maxNormalDamage[self.turn-1]*(1-avgGuardFactor)*(1-dmgRed)-avgDefPostSuper)*guardMod+(1-unit.kit.P_guard[self.turn-1])*(maxNormalDamage[self.turn-1]*(1-dmgRed)-avgDefPostSuper)*avgTypeMod)/(maxNormalDamage[self.turn-1]*avgTypeMod),0)
class SADefence(TurnBasedFactor):
    def __init__(self,turn,SBR=0,FL=0,RZ=0,overall=0):
        super().__init__(turn,SBR,FL,RZ,overall)
    def calculate(self,unit,slot1=False):
        P_dodge = unit.kit.P_dodge[self.turn-1] + (1-unit.kit.P_dodge[self.turn-1]) * (unit.HP_P_Dodge()+(1-unit.HP_P_Dodge())*Links_Dodge(self.turn).calculate(unit))
        dmgRed = DmgRed(self.turn).calculate(unit)
        if slot1:
            avgDef = AvgDefPreSuper(self.turn).calculate(unit)
        else:
            avgDef = AvgDefPostSuper(self.turn).calculate(unit)
        return -(1-(unit.kit.P_nullify[self.turn-1]+(1-unit.kit.P_nullify[self.turn-1])*(1-dodgeCancelFrac)*P_dodge))*((unit.kit.P_guard[self.turn-1]*(maxSADamage[self.turn-1]*(1-avgGuardFactor)*(1-dmgRed)-avgDef)*guardMod+(1-unit.kit.P_guard[self.turn-1])*(maxSADamage[self.turn-1]*(1-dmgRed)-avgDef)*avgTypeMod))/(maxSADamage[self.turn-1]*avgTypeMod)
class Slot1Ability(TurnBasedFactor):
    def __init__(self,turn,SBR=0,FL=0,RZ=0,overall=0):
            super().__init__(turn,SBR,FL,RZ,overall)
    def calculate(self,unit):
        saDefencePreSuper = SADefence(self.turn).calculate(unit,slot1=True)
        saDefencePostSuper = SADefence(self.turn).calculate(unit)
        slot1DefFrac = 1-saDefencePostSuper+saDefencePreSuper
        return max(2*(slot1DefFrac-0.5),0)*(1+SADefence(self.turn).calculate(unit))
class Healing(TurnBasedFactor):
    def __init__(self,turn,SBR=0,FL=0,RZ=0,overall=0):
            super().__init__(turn,SBR,FL,RZ,overall)
    def calculate(self,unit):
        return unit.kit.healing[self.turn-1]
class Support(TurnBasedFactor):
    def __init__(self,turn,SBR=0,FL=0,RZ=0,overall=0):
            super().__init__(turn,SBR,FL,RZ,overall)
    def calculate(self,unit):
        return unit.kit.support[self.turn-1]
class Special(TurnBasedFactor):
    def __init__(self,turn,SBR=0,FL=0,RZ=0,overall=0):
            super().__init__(turn,SBR,FL,RZ,overall)
    def calculate(self,unit):
        return unit.kit.special[self.turn-1]
class APT(TurnBasedHelper):
    def __init__(self,turn):
        super().__init__(turn)
    def calculate(self,unit):
        avg_att = AvgAtt(self.turn).calculate(unit)
        avg_att_modifier = AvgAttModifier(self.turn).calculate(unit)
        return avg_att * avg_att_modifier
class AvgAtt(TurnBasedHelper):
    def __init__(self,turn):
        super().__init__(turn)
    def branchAtt(self,i,nAA,M_12,M_N,P_AA,nProcs,P_SA,P_g,N_0,A_12_0,SA_mult,P_HP):
        #i_loc = i
        #M_12_loc = M_12
        #M_N_loc = M_N
        #p_A_loc = p_A
        #procs_loc = procs
        N = M_N * N_0
        A_12 = M_12 * A_12_0
        if(i == nAA - 1): #If no more additional attacks
            branchAtt = 0.5 * P_AA * (A_12 + N) #Add average HP damage
        else:
            i+= 1 # Increment attack counter
            # Calculate extra attack if get additional super and subsequent addditional attacks
            tempAtt0 = self.branchAtt(i, nAA, M_12, M_N, P_AA, nProcs, P_SA, P_g, N_0, A_12_0, SA_mult, P_HP) # Add damage if don't get any additional attacks
            tempAtt1 = self.branchAtt(i, nAA, M_12, M_N, P_AA + P_HP * (1 - P_HP) ^ nProcs, nProcs + 1, P_SA, P_g, N_0, A_12_0, SA_mult, P_HP)
            tempAtt2 = self.branchAtt(i, nAA,M_12 + SA_mult, M_N + SA_mult, P_AA + P_HP * (1 - P_HP) ^ nProcs, nProcs + 1, P_SA, P_g, N_0, A_12_0, SA_mult, P_HP)
            branchAtt = P_SA[i] * (tempAtt2 + A_12) + (1 - P_SA[i])* (P_g[i] * (tempAtt1 + N) + (1 - P_g[i]) * (tempAtt0))
        return branchAtt
    def calculate(self,unit):
        nAA = len(unit.kit.AA_P_super[self.turn-1]) # Number of additional attacks from passive
        normal = Normal(self.turn).calculate(unit) # Damage from normal
        sa = SA(self.turn).calculate(unit) # Damage from 12 Ki SA
        SAmultiplier = SAMultiplier(unit.kit.SA_Mult_12,unit.kit.EZA,unit.kit.exclusivity,unit.nCopies,unit.kit.SA_12_Att_Stacks[self.turn-1],unit.kit.SA_12_Att[self.turn-1]) # 12 Ki SA multipler
        [constantKi,randomKi] = Ki(self.turn).calculate(unit)
        attackDistribution = AttackDistribution(constantKi,randomKi,unit.kit.intentional12Ki[self.turn-1],unit.kit.rarity)
        i = -1 # iteration counter
        M_12 = (SAmultiplier+unit.kit.SA_12_Att[self.turn-1]) # 12 ki multiplier after SA effect
        A_12_0 = sa/M_12 # Get 12 ki SA attack stat without multiplier
        P1_Att = unit.kit.P1_Att[self.turn-1]+avgSupport # get SoT attack stat for SA multiplier scaling
        N_0 = normal/P1_Att # Get normal attack stat without SoT attack
        nProcs = 1 # Initialise number of HP procs
        P_AA = unit.HP_P_AA() # Probability of doing an additional attack next
        P_SA = unit.kit.AA_P_super[self.turn-1] # Probability of doing a super on inbuilt additional
        P_g = unit.kit.AA_P_guarantee[self.turn-1] # Probability of inbuilt additional
        counterAtt = (4*unit.kit.P_counterNormal[self.turn-1]+0.5*unit.kit.P_counterSA[self.turn-1])*unit.kit.counterMod*normal
        avgAtt = attackDistribution[0]*(normal+self.branchAtt(i,nAA,M_12,P1_Att,P_AA,nProcs,P_SA,P_g,N_0,A_12_0,unit.kit.SA_12_Att[self.turn-1],unit.HP_P_AA)) \
                   + attackDistribution[1]*(sa+self.branchAtt(i,nAA,M_12+SAmultiplier,P1_Att+SAmultiplier,P_AA,nProcs,P_SA,P_g,N_0,A_12_0,unit.kit.SA_12_Att[self.turn-1],unit.HP_P_AA))
        if(unit.kit.rarity=='LR'): # If unit is a LR
            USAmultiplier = SAMultiplier(unit.kit.SA_Mult_18,unit.kit.EZA,unit.kit.exclusivity,unit.nCopies,unit.kit.SA_18_Att_Stacks[self.turn-1],unit.kit.SA_18_Att[self.turn-1]) # USA multiplier
            usa = USA(self.turn).calculate(unit) # USA attack stat
            avgAtt += attackDistribution[2]*(usa+self.branchAtt(i,nAA,M_12+USAmultiplier,P1_Att+USAmultiplier,P_AA,nProcs,P_SA,P_g,N_0,A_12_0,unit.kit.SA_12_Att[self.turn-1],unit.HP_P_AA()))
        avgAtt += counterAtt
        return avgAtt   
class Normal(TurnBasedHelper):
    def __init__(self,turn):
        super().__init__(turn)
    def calculate(self,unit):
        att = unit.kit.attack+(unit.HP_Stats())[0]+(unit.SkillOrb_Stats())[0]
        p1_Att = unit.kit.P1_Att[self.turn-1]+avgSupport+StackedAtt(self.turn).calculate(unit)
        links_Att = Links_Att(self.turn).calculate(unit)
        p2_Att = unit.kit.P2_Att[self.turn-1]+Links_Att_OnSuper(self.turn).calculate(unit)
        p3_Att = unit.kit.P3_Att[self.turn-1]
        kiMultiplier = KiMultiplier(unit.kit.kiMod_12,min(round(sum(Ki(self.turn).calculate(unit))),24))
        return att*(1+leaderSkillBuff)*(1+p1_Att)*(1+links_Att)*(1+p2_Att)*(1+p3_Att)*kiMultiplier
class SA(TurnBasedHelper):
    def __init__(self,turn):
        super().__init__(turn)
    def calculate(self,unit):
        att = unit.kit.attack+(unit.HP_Stats())[0]+(unit.SkillOrb_Stats())[0]
        p1_Att = unit.kit.P1_Att[self.turn-1]+avgSupport+StackedAtt(self.turn).calculate(unit)
        links_Att = Links_Att(self.turn).calculate(unit)
        p2_Att = unit.kit.P2_Att[self.turn-1]+Links_Att_OnSuper(self.turn).calculate(unit)
        p3_Att = unit.kit.P3_Att[self.turn-1]
        kiMultiplier = unit.kit.kiMod_12
        SAmultiplier = SAMultiplier(unit.kit.SA_Mult_12,unit.kit.EZA,unit.kit.exclusivity,unit.nCopies,unit.kit.SA_12_Att_Stacks[self.turn-1],unit.kit.SA_12_Att[self.turn-1])
        return att*(1+leaderSkillBuff)*(1+p1_Att)*(1+links_Att)*(1+p2_Att)*(1+p3_Att)*kiMultiplier*(SAmultiplier+unit.kit.SA_12_Att[self.turn-1])
class USA(TurnBasedHelper):
    def __init__(self,turn):
        super().__init__(turn)
    def calculate(self,unit):
        att = unit.kit.attack+(unit.HP_Stats())[0]+(unit.SkillOrb_Stats())[0]
        p1_Att = unit.kit.P1_Att[self.turn-1]+avgSupport+StackedAtt(self.turn).calculate(unit)
        links_Att = Links_Att(self.turn).calculate(unit)
        p2_Att = unit.kit.P2_Att[self.turn-1]+Links_Att_OnSuper(self.turn).calculate(unit)
        p3_Att = unit.kit.P3_Att[self.turn-1]
        kiMultiplier = KiMultiplier(unit.kit.kiMod_12,min(max(round(sum(Ki(self.turn).calculate(unit))),18),24))
        SAmultiplier = SAMultiplier(unit.kit.SA_Mult_18,unit.kit.EZA,unit.kit.exclusivity,unit.nCopies,unit.kit.SA_18_Att_Stacks[self.turn-1],unit.kit.SA_18_Att[self.turn-1])
        return att*(1+leaderSkillBuff)*(1+p1_Att)*(1+links_Att)*(1+p2_Att)*(1+p3_Att)*kiMultiplier*(SAmultiplier+unit.kit.SA_18_Att[self.turn-1])
class StackedAtt(TurnBasedHelper):
    def __init__(self,turn):
        super().__init__(turn)
    def calculate(self,unit):
        # Can make more efficient later by saving stacked attack for each turn and just add on next turn, rather than calculating the whole thing on each call
        stackedAtt = 0
        for turn in range(1,self.turn): # For each turn < self.turn (i.e. turns which can affect how much defense have on self.turn)
            [constantKi,randomKi] = Ki(turn).calculate(unit)
            attackDistribution = AttackDistribution(constantKi,randomKi,unit.kit.intentional12Ki[self.turn-1],unit.kit.rarity) # compute probabilities of normal,SA and USA
            if(unit.kit.SA_18_Att_Stacks[turn-1]>=self.turn-turn): # If stack for long enough to last to turn self.turn
                stackedAtt += attackDistribution[2]*unit.kit.SA_18_Att[turn-1] # add stacked att
            if(unit.kit.SA_12_Att_Stacks[turn-1]>=self.turn-turn): # If stack for long enough to last to turn self.turn
                stackedAtt += (attackDistribution[1]+Avg_AA_SA(turn).calculate(unit))*unit.kit.SA_12_Att[turn-1] # add stacked att
        return stackedAtt
class StackedDef(TurnBasedHelper):
    def __init__(self,turn):
        super().__init__(turn)
    def calculate(self,unit):
        # Can make more efficient later by saving stacked attack for each turn and just add on next turn, rather than calculating the whole thing on each call
        stackedDef = 0
        for turn in range(1,self.turn): # For each turn < self.turn (i.e. turns which can affect how much defense have on self.turn)
            [constantKi,randomKi] = Ki(turn).calculate(unit)
            attackDistribution = AttackDistribution(constantKi,randomKi,unit.kit.intentional12Ki[self.turn-1],unit.kit.rarity) # compute probabilities of normal,SA and USA
            if(unit.kit.SA_18_Def_Stacks[turn-1]>=self.turn-turn): # If stack for long enough to last to turn self.turn
                stackedDef += attackDistribution[2]*unit.kit.SA_18_Def[turn-1] # add stacked att
            if(unit.kit.SA_12_Def_Stacks[turn-1]>=self.turn-turn): # If stack for long enough to last to turn self.turn
                stackedDef += (attackDistribution[1]+Avg_AA_SA(turn).calculate(unit))*unit.kit.SA_12_Def[turn-1] # add stacked att
        return stackedDef
class Links_Att(TurnBasedHelper):
    def __init__(self,turn):
        super().__init__(turn)
    def calculate(self,unit):
        sum = 0
        for link in unit.kit.links[:,self.turn-1]:
            sum += link.att_SoT*link.commonality
        return sum
class Links_Att_OnSuper(TurnBasedHelper):
    def __init__(self,turn):
        super().__init__(turn)
    def calculate(self,unit):
        sum = 0
        for link in unit.kit.links[:,self.turn-1]:
            sum += link.att_OnSuper*link.commonality
        return sum
class Links_Ki(TurnBasedHelper):
    def __init__(self,turn):
        super().__init__(turn)
    def calculate(self,unit):
        sum = 0
        for link in unit.kit.links[:,self.turn-1]:
            sum += link.ki*link.commonality
        return sum
class Links_Defence(TurnBasedHelper):
    def __init__(self,turn):
        super().__init__(turn)
    def calculate(self,unit):
        sum = 0
        for link in unit.kit.links[:,self.turn-1]:
            sum += link.defence*link.commonality
        return sum
class Links_Crit(TurnBasedHelper):
    def __init__(self,turn):
        super().__init__(turn)
    def calculate(self,unit):
        sum = 0
        for link in unit.kit.links[:,self.turn-1]:
            sum += link.crit*link.commonality
        return sum
class Links_DmgRed(TurnBasedHelper):
    def __init__(self,turn):
        super().__init__(turn)
    def calculate(self,unit):
        sum = 0
        for link in unit.kit.links[:,self.turn-1]:
            sum += link.dmgRed*link.commonality
        return sum
class Links_Dodge(TurnBasedHelper):
    def __init__(self,turn):
        super().__init__(turn)
    def calculate(self,unit):
        sum = 0
        for link in unit.kit.links[:,self.turn-1]:
            sum += link.dodge*link.commonality
        return sum
class Links_Healing(TurnBasedHelper):
    def __init__(self,turn):
        super().__init__(turn)
    def calculate(self,unit):
        sum = 0
        for link in unit.kit.links[:,self.turn-1]:
            sum += link.healing*link.commonality
        return sum
class Links_Commonality(TurnBasedHelper):
    def __init__(self,turn):
        super().__init__(turn)
    def calculate(self,unit):
        sum = 0
        for link in unit.kit.links[:,self.turn-1]:
            sum += link.commonality
        return sum/7
class Ki(TurnBasedHelper):
    def __init__(self,turn):
        super().__init__(turn)
    def calculate(self,unit):
        links_ki = Links_Ki(self.turn)
        return [leaderSkillKi+unit.kit.passiveKi[self.turn-1],links_ki.calculate(unit)+unit.kit.collectKi[self.turn-1]+avgKiSupport]
class AvgAttModifier(TurnBasedHelper):
    def __init__(self,turn):
        super().__init__(turn)
    def calculate(self,unit):
        P_crit = P_Crit(self.turn).calculate(unit)
        return P_crit*CritMultiplier+(1-P_crit)*(unit.kit.P_SEaaT[self.turn-1]*SEaaTMultiplier+(1-unit.kit.P_SEaaT[self.turn-1])*avgTypeAdvantage)
class P_Crit(TurnBasedHelper):
    def __init__(self,turn):
        super().__init__(turn)
    def calculate(self,unit):
        return unit.kit.passiveCrit[self.turn-1]+(1-unit.kit.passiveCrit[self.turn-1])*(unit.HP_P_Crit()+(1-unit.HP_P_Crit())*Links_Crit(self.turn).calculate(unit))
class DmgRed(TurnBasedHelper):
    def __init__(self,turn):
        super().__init__(turn)
    def calculate(self,unit):
        return unit.kit.dmgRed[self.turn-1] + Links_DmgRed(self.turn).calculate(unit)
class AvgDefPreSuper(TurnBasedHelper):
    def __init__(self,turn):
        super().__init__(turn)
    def calculate(self,unit):
        defStat = unit.kit.defence+(unit.HP_Stats())[1]+(unit.SkillOrb_Stats())[1]
        defSoT = unit.kit.P1_Def[self.turn-1]+avgSupport
        links_Defence = Links_Defence(self.turn).calculate(unit)
        p2_Def = unit.kit.P2A_Def[self.turn-1]
        p3_Def = unit.kit.P3_Def[self.turn-1]
        avgDefMult = StackedDef(self.turn).calculate(unit)
        return defStat*(1+leaderSkillBuff)*(1+defSoT)*(1+links_Defence)*(1+p2_Def)*(1+p3_Def)*(1+avgDefMult)
class AvgDefPostSuper(TurnBasedHelper):
    def __init__(self,turn):
        super().__init__(turn)
    def calculate(self,unit):
        defStat = unit.kit.defence+(unit.HP_Stats())[1]+(unit.SkillOrb_Stats())[1]
        defSoT = unit.kit.P1_Def[self.turn-1]+avgSupport
        links_Defence = Links_Defence(self.turn).calculate(unit)
        p2_Def = unit.kit.P2A_Def[self.turn-1]+unit.kit.P2B_Def[self.turn-1]
        p3_Def = unit.kit.P3_Def[self.turn-1]
        avgDefMult = AvgDefMult(self.turn).calculate(unit)
        return defStat*(1+leaderSkillBuff)*(1+defSoT)*(1+links_Defence)*(1+p2_Def)*(1+p3_Def)*(1+avgDefMult)
class Avg_AA_SA(TurnBasedHelper):
    def __init__(self,turn):
        super().__init__(turn)
    def branchAA(self,i,nAA,P_AA,nProcs,P_SA,P_g,P_HP):
        #i_loc = i
        #M_12_loc = M_12
        #M_N_loc = M_N
        #p_A_loc = p_A
        #procs_loc = procs
        if(i == nAA - 1): #If no more additional attacks
            branchAA = 0.5 * P_AA # Add average HP super chance
        else:
            i+= 1 # Increment attack counter
            # Calculate extra attack if get additional super and subsequent addditional attacks
            tempAA0 = self.branchDef(i, nAA, P_AA, nProcs, P_SA, P_g, P_HP) # Add damage if don't get any additional attacks
            tempAA1 = self.branchDef(i, nAA, P_AA + P_HP * (1 - P_HP) ^ nProcs, nProcs + 1, P_SA, P_g, P_HP)
            branchAA = P_SA[i] * tempAA1 + (1 - P_SA[i])* (P_g[i] * tempAA1 + (1 - P_g[i]) * tempAA0)
        return branchAA
    def calculate(self,unit):
        nAA = len(unit.kit.AA_P_super[self.turn-1]) # Number of additional attacks from passive
        i = -1 # iteration counter
        nProcs = 1 # Initialise number of HP procs
        P_AA = unit.HP_P_AA() # Probability of doing an additional attack next
        P_SA = unit.kit.AA_P_super[self.turn-1] # Probability of doing a super on inbuilt additional
        P_g = unit.kit.AA_P_guarantee[self.turn-1] # Probability of inbuilt additional
        avg_AA_SA = self.branchAA(i,nAA,P_AA,nProcs,P_SA,P_g,unit.HP_P_AA)
        return avg_AA_SA
class AvgDefMult(TurnBasedHelper):
    def __init__(self,turn):
        super().__init__(turn)
    def calculate(self,unit):
        [constantKi,randomKi] = Ki(self.turn).calculate(unit)
        attackDistribution = AttackDistribution(constantKi,randomKi,unit.kit.intentional12Ki[self.turn-1],unit.kit.rarity)
        if(unit.kit.rarity=='LR'): # If unit is a LR
            avgDefMult = attackDistribution[1]*unit.kit.SA_12_Def[self.turn-1]+attackDistribution[2]*unit.kit.SA_18_Def[self.turn-1]
        else:
            avgDefMult = attackDistribution[1]*unit.kit.SA_12_Def[self.turn-1]
        avgDefMult += StackedDef(self.turn).calculate(unit) + Avg_AA_SA(self.turn).calculate(unit)*unit.kit.SA_12_Def[self.turn-1]
        return avgDefMult

Goku = LR(1,1,['C','A'],'D')
leaderSkill = LeaderSkill(10).calculate(Goku)
slot1 = SBR(10).calculate(Goku)
print(slot1)