import numpy as np
from datetime import datetime
from scipy.stats import poisson
# Make a modelling parameters file and put the below parameters in it
# Make drop down lists for input files for cells that have discrete options, e.g. Links, SA multipliers
# If want to increase efficiency can save Objects with Pickle module - probably also want to change class methods to save outputs as attributes
# On ki collect assume on average get 3.5 type orbs (50% same type, 50% other type) and 1 rainbow orb ->6.25 ki on average
# TODO
# New Quest Stages
# Path to Ultimate Power Event Treasures

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
    SAMultipliers = [0]*turnMax
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
    for i in range(turnMax):
        stackingPenalty=0
        if (nStacks[i]==turnMax): # If infinite stacker
            stackingPenalty = SA_Att[i]
        SAMultipliers[i] = baseMultiplier+0.05*HP_SA_Mult[nCopies-1]-stackingPenalty
    return SAMultipliers
def KiMultiplier(base,ki):
    kiMultipliers = [0]*turnMax
    for i in range(turnMax):
        if ki[i]<=12:
            kiMultipliers[i] = 1
        else:
            kiMultipliers[i] = (np.linspace(base,2,12))[ki[i]-13]
    return kiMultipliers
def branchAtt(i,nAA,M_12,M_N,P_AA,nProcs,P_SA,P_g,N_0,A_12_0,SA_mult,P_HP):
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
            tempAtt0 = branchAtt(i, nAA, M_12, M_N, P_AA, nProcs, P_SA, P_g, N_0, A_12_0, SA_mult, P_HP) # Add damage if don't get any additional attacks
            tempAtt1 = branchAtt(i, nAA, M_12, M_N, P_AA + P_HP * (1 - P_HP) ^ nProcs, nProcs + 1, P_SA, P_g, N_0, A_12_0, SA_mult, P_HP)
            tempAtt2 = branchAtt(i, nAA,M_12 + SA_mult, M_N + SA_mult, P_AA + P_HP * (1 - P_HP) ^ nProcs, nProcs + 1, P_SA, P_g, N_0, A_12_0, SA_mult, P_HP)
            branchAtt = P_SA[i] * (tempAtt2 + A_12) + (1 - P_SA[i])* (P_g[i] * (tempAtt1 + N) + (1 - P_g[i]) * (tempAtt0))
        return branchAtt
def branchAA(i,nAA,P_AA,nProcs,P_SA,P_g,P_HP):
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
            tempAA0 = branchAA(i, nAA, P_AA, nProcs, P_SA, P_g, P_HP) # Add damage if don't get any additional attacks
            tempAA1 = branchAA(i, nAA, P_AA + P_HP * (1 - P_HP) ^ nProcs, nProcs + 1, P_SA, P_g, P_HP)
            branchAA = P_SA[i] * tempAA1 + (1 - P_SA[i])* (P_g[i] * tempAA1 + (1 - P_g[i]) * tempAA0)
        return branchAA
class Unit:
    def __init__(self,ID,nCopies,HPS,skillOrbs):
        self.ID = str(ID)
        self.nCopies = nCopies
        self.HPS = HPS
        self.skillOrbs = skillOrbs
        self.HP_Stats = self.getHP_Stats()
        self.skillOrbs_Stats = self.getSkillOrb_Stats()
        self.att = self.kit.attack+self.HP_Stats[0]+self.skillOrbs_Stats[0]
        self.defence =self.kit.defence+self.HP_Stats[1]+self.skillOrbs_Stats[1]
        self.HP_P_AA = self.getHP_P_AA()
        self.HP_P_Crit = self.getHP_P_Crit()
        self.HP_P_Dodge = self.getHP_P_Dodge()
        self.leaderSkill = self.kit.leaderSkill
        self.SBR = self.kit.SBR
        [self.links_Commonality, self.links_Ki, self.linkAtt_SoT, self.linkDef, self.linkCrit, self.linkAtt_OnSuper, self.linkDodge, self.linkDmgRed, self.linkHealing] = self.getLinks()
        self.healing = self.kit.healing+self.linkHealing
        self.dmgRed = self.kit.dmgRed + self.linkDmgRed
        self.special = self.kit.special
        self.support = self.kit.support
        self.useability = self.kit.nTeams/nTeamsMax*(self.support[0]+self.links_Commonality[0])
        self.constantKi = leaderSkillKi+self.kit.passiveKi
        self.randomKi = self.links_Ki+self.kit.collectKi+avgKiSupport
        self.ki = (np.around(self.constantKi + self.randomKi)).astype('int32')
        [self.Pr_N, self.Pr_SA, self.Pr_USA] = self.getAttackDistribution()
        [self.stackedAtt, self.stackedDef] = self.getStackedStats()
        self.p1Att = self.kit.P1_Att+avgSupport
        self.p2Att = self.kit.P2_Att+self.linkAtt_OnSuper
        self.p3Att = self.kit.P3_Att
        self.p1Def = self.kit.P1_Def+avgSupport
        self.p2Def = self.kit.P2A_Def+self.kit.P2B_Def
        self.p3Def = self.kit.P3_Def
        self.normal = self.getNormal()
        self.sa = self.getSA()
        if self.kit.rarity == 'LR':
            self.usa = self.getUSA()
        [self.avg_AA_SA, self.avgAtt] = self.getAvg()
        self.P_Crit = self.kit.passiveCrit+(1-self.kit.passiveCrit)*(self.HP_P_Crit+(1-self.HP_P_Crit)*self.linkCrit)
        self.avgAttModifer = self.P_Crit*CritMultiplier+(1-self.P_Crit)*(self.kit.P_SEaaT*SEaaTMultiplier+(1-self.kit.P_SEaaT)*avgTypeAdvantage)
        self.apt = self.avgAtt*self.avgAttModifer
        self.P_Dodge = self.kit.P_dodge + (1-self.kit.P_dodge) * (self.HP_P_Dodge+(1-self.HP_P_Dodge)*self.linkDodge)
        self.avgDefMult = self.getAvgDefMult()
        self.avgDefPreSuper = self.defence*(1+leaderSkillBuff)*(1+self.p1Def)*(1+self.linkDef)*(1+self.kit.P2A_Def)*(1+self.p3Def)*(1+self.stackedDef)
        self.avgDefPostSuper = self.defence*(1+leaderSkillBuff)*(1+self.p1Def)*(1+self.linkDef)*(1+self.p2Def)*(1+self.p3Def)*(1+self.avgDefMult)
        self.normalDefence = np.minimum(-(1-(1-dodgeCancelFrac)*self.P_Dodge)*(self.kit.P_guard*(maxNormalDamage*(1-avgGuardFactor)*(1-self.dmgRed)-self.avgDefPostSuper)*guardMod+(1-self.kit.P_guard)*(maxNormalDamage*(1-self.dmgRed)-self.avgDefPostSuper)*avgTypeMod)/(maxNormalDamage*avgTypeMod),[0]*turnMax)
        self.saDefencePreSuper = -(1-(self.kit.P_nullify+(1-self.kit.P_nullify)*(1-dodgeCancelFrac)*self.P_Dodge))*((self.kit.P_guard*(maxSADamage*(1-avgGuardFactor)*(1-self.dmgRed)-self.avgDefPreSuper)*guardMod+(1-self.kit.P_guard)*(maxSADamage*(1-self.dmgRed)-self.avgDefPreSuper)*avgTypeMod))/(maxSADamage*avgTypeMod)
        self.saDefencePostSuper = -(1-(self.kit.P_nullify+(1-self.kit.P_nullify)*(1-dodgeCancelFrac)*self.P_Dodge))*((self.kit.P_guard*(maxSADamage*(1-avgGuardFactor)*(1-self.dmgRed)-self.avgDefPostSuper)*guardMod+(1-self.kit.P_guard)*(maxSADamage*(1-self.dmgRed)-self.avgDefPostSuper)*avgTypeMod))/(maxSADamage*avgTypeMod)
        self.slot1Ability = np.maximum(2*(0.5-self.saDefencePostSuper+self.saDefencePreSuper),[0]*turnMax)*(1+self.saDefencePostSuper)
        self.attributes = [self.leaderSkill, self.SBR, self.healing,self.special, self.support, self.useability,self.apt,self.normalDefence,self.saDefencePostSuper,self.slot1Ability]
    def getHP_Stats(self):
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
                    return HP_F2P[:,4]
                else:
                    return HP_INT[:,self.nCopies-1]
    def getSkillOrb_Stats(self):
        if(self.skillOrbs == 'A'):
            return [500,0]
        elif(self.skillOrbs == 'D'):
            return [0,500]
        else:
            raise Exception("Invalid Skill Orb entered")
    def getHP_P_AA(self):
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
    def getHP_P_Crit(self):
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
    def getHP_P_Dodge(self):
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
    def getLinks(self):
        linkCommonality, linkKi, linkAtt_SoT, linkDef, linkCrit, linkAtt_OnSuper, linkDodge, linkDmgRed, linkHealing = np.zeros(turnMax), np.zeros(turnMax), np.zeros(turnMax),np.zeros(turnMax), np.zeros(turnMax), np.zeros(turnMax),np.zeros(turnMax), np.zeros(turnMax), np.zeros(turnMax)
        for turn in range(turnMax):
            for link in self.kit.links[:,turn]:
                linkCommonality[turn] += link.commonality
                linkKi[turn] += link.commonality*link.ki
                linkAtt_SoT[turn] += link.commonality*link.att_SoT
                linkDef[turn] += link.commonality*link.defence
                linkCrit[turn] += link.commonality*link.crit
                linkAtt_OnSuper[turn] += link.commonality*link.att_OnSuper
                linkDodge[turn] += link.commonality*link.dodge
                linkDmgRed[turn] += link.commonality*link.dmgRed
                linkHealing[turn] += link.commonality*link.healing
        return [linkCommonality/7, linkKi, linkAtt_SoT, linkDef, linkCrit, linkAtt_OnSuper, linkDodge, linkDmgRed, linkHealing]
    def getAttackDistribution(self):
        Pr_N, Pr_SA, Pr_USA = [0]*turnMax, [0]*turnMax, [0]*turnMax
        for i in range(turnMax):
            Pr_N[i] = PoissonCDF(max(12-self.constantKi[i],0),self.randomKi[i])
            if(self.kit.intentional12Ki[i] or self.kit.rarity !='LR'):
                Pr_SA[i] = 1-Pr_N[i]
                Pr_USA[i] = 0
            else:
                Pr_USA[i] = 1-PoissonCDF(max(17-self.constantKi[i],0),self.randomKi[i])
                Pr_SA[i] = 1-Pr_N[i]-Pr_USA[i]
        return [Pr_N, Pr_SA, Pr_USA]
    def getAvg(self):
        nAA = [len(List) for List in self.kit.AA_P_super] # Number of additional attacks from passive in each turn
        i = -1 # iteration counter
        nProcs = 1 # Initialise number of HP procs
        SAmultiplier = SAMultiplier(self.kit.SA_Mult_12,self.kit.EZA,self.kit.exclusivity,self.nCopies,self.kit.SA_12_Att_Stacks,self.kit.SA_12_Att)
        if(self.kit.rarity=='LR'): # If self. is a LR
            USAmultiplier = SAMultiplier(self.kit.SA_Mult_18,self.kit.EZA,self.kit.exclusivity,self.nCopies,self.kit.SA_18_Att_Stacks,self.kit.SA_18_Att) # USA multiplier
        M_12 = SAmultiplier+self.kit.SA_12_Att+self.stackedAtt # 12 ki multiplier after SA effect
        A_12_0 = self.sa/M_12 # Get 12 ki SA attack stat without multiplier
        N_0 = self.normal/(self.p1Att+self.stackedAtt) # Get normal attack stat without SoT attack
        P_AA = self.HP_P_AA # Probability of doing an additional attack next
        P_SA = self.kit.AA_P_super # Probability of doing a super on inbuilt additional
        P_g = self.kit.AA_P_guarantee # Probability of inbuilt additional
        counterAtt = (4*self.kit.P_counterNormal+0.5*self.kit.P_counterSA)*self.kit.counterMod*self.normal
        avg_AA_SA, avgAtt = [0]*turnMax, [0]*turnMax
        for j in range(turnMax):
            avg_AA_SA[j] = branchAA(i,nAA[j],P_AA,nProcs,P_SA[j],P_g[j],self.HP_P_AA)
            avgAtt[j] = self.Pr_N[j]*(self.normal[j]+branchAtt(i,nAA[j],M_12[j],self.p1Att[j],P_AA,nProcs,P_SA[j],P_g[j],N_0[j],A_12_0[j],self.kit.SA_12_Att[j],self.HP_P_AA)) \
                   + self.Pr_SA[j]*(self.sa[j]+branchAtt(i,nAA[j],M_12[j]+SAmultiplier[j],self.p1Att[j]+SAmultiplier[j],P_AA,nProcs,P_SA[j],P_g[j],N_0[j],A_12_0[j],self.kit.SA_12_Att[j],self.HP_P_AA))
            if(self.kit.rarity=='LR'): # If self. is a LR
                avgAtt[j] += self.Pr_USA[j]*(self.usa[j]+branchAtt(i,nAA[j],M_12[j]+USAmultiplier[j],self.p1Att[j]+USAmultiplier[j],P_AA,nProcs,P_SA[j],P_g[j],N_0[j],A_12_0[j],self.kit.SA_12_Att[j],self.HP_P_AA))
        avgAtt += counterAtt
        return [avg_AA_SA, avgAtt]
    def getStackedStats(self):
        # Can make more efficient later by saving stacked attack for each turn and just add on next turn, rather than calculating the whole thing on each call
        stackedAtt, stackedDef = [0]*turnMax, [0]*turnMax
        for turn in range(turnMax-1): # For each turn < self.turn (i.e. turns which can affect how much defense have on self.turn) 
            if(self.kit.SA_18_Att_Stacks[turn]>1): # If stack for long enough to last to turn self.turn
                stackedAtt[turn+1:turn+self.kit.SA_18_Att_Stacks[turn]-1] += self.Pr_USA[turn]*self.kit.SA_18_Att[turn] # add stacked att
            if(self.kit.SA_18_Def_Stacks[turn]>1): # If stack for long enough to last to turn self.turn
                stackedDef[turn+1:turn+self.kit.SA_18_Def_Stacks[turn]-1] += self.Pr_USA[turn]*self.kit.SA_18_Def[turn] # add stacked att
            if(self.kit.SA_12_Att_Stacks[turn]>1): # If stack for long enough to last to turn self.turn
                stackedAtt[turn+1:turn+self.kit.SA_12_Att_Stacks[turn]-1] += (self.Pr_SA[turn]+self.avg_AA_SA[turn])*self.kit.SA_12_Att[turn] # add stacked att
            if(self.kit.SA_12_Def_Stacks[turn]>1): # If stack for long enough to last to turn self.turn
                stackedAtt[turn+1:turn+self.kit.SA_12_Def_Stacks[turn]-1] += (self.Pr_SA[turn]+self.avg_AA_SA[turn])*self.kit.SA_12_Def[turn] # add stacked att
        return [np.array(stackedAtt), np.array(stackedDef)]
    def getNormal(self):
        kiMultiplier = KiMultiplier(self.kit.kiMod_12,np.minimum(self.ki,[24]*turnMax))
        return self.att*(1+leaderSkillBuff)*(1+self.p1Att)*(1+self.linkAtt_SoT)*(1+self.p2Att)*(1+self.p3Att)*kiMultiplier
    def getSA(self):
        kiMultiplier = [self.kit.kiMod_12]*turnMax
        SAmultiplier = SAMultiplier(self.kit.SA_Mult_12,self.kit.EZA,self.kit.exclusivity,self.nCopies,self.kit.SA_12_Att_Stacks,self.kit.SA_12_Att)
        return self.att*(1+leaderSkillBuff)*(1+self.p1Att)*(1+self.linkAtt_SoT)*(1+self.p2Att)*(1+self.p3Att)*kiMultiplier*(SAmultiplier+self.kit.SA_12_Att)
    def getUSA(self):
        kiMultiplier = KiMultiplier(self.kit.kiMod_12,np.minimum(np.maximum(self.ki,[18]*turnMax),[24]*turnMax))
        SAmultiplier = SAMultiplier(self.kit.SA_Mult_18,self.kit.EZA,self.kit.exclusivity,self.nCopies,self.kit.SA_18_Att_Stacks,self.kit.SA_18_Att)
        return self.att*(1+leaderSkillBuff)*(1+self.p1Att)*(1+self.linkAtt_SoT)*(1+self.p2Att)*(1+self.p3Att)*kiMultiplier*(SAmultiplier+self.kit.SA_18_Att)
    def getAvgDefMult(self):
        if(self.kit.rarity=='LR'): # If unit is a LR
            avgDefMult = self.Pr_SA*self.kit.SA_12_Def+self.Pr_USA*self.kit.SA_18_Def
        else:
            avgDefMult = self.Pr_SA*self.kit.SA_12_Def
        avgDefMult += self.stackedDef + self.avg_AA_SA*self.kit.SA_12_Def
        return avgDefMult
class TUR(Unit):
    def __init__(self,ID,nCopies,HPS,skillOrbs):
        self.kit = Kit(str(ID),"TUR").getKit()
        super().__init__(ID,nCopies,HPS,skillOrbs)
class LR(Unit):
    def __init__(self,ID,nCopies,HPS,skillOrbs):
        self.kit = Kit(str(ID),"LR").getKit()
        super().__init__(ID,nCopies,HPS,skillOrbs)     
class Kit:
    def __init__(self,ID,rarity):
        self.ID = ID
        self.rarity = rarity
        self.links = np.array([[None]*turnMax for i in range(7)])
    def getKit(self):
        filepath = 'C:/Users/Tyler/OneDrive/Documents/DokkanAnalysis/DokkanKits/'+self.ID+'.csv'
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
        filepath = 'C:/Users/Tyler/OneDrive/Documents/DokkanAnalysis/LinkTable.csv'
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
#class Evaluator:

Goku = LR(1,5,['C','A'],'D')
for attribute in Goku.attributes:
    print(attribute)