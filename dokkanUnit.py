import numpy as np
import pandas as pd
from scipy.stats import poisson
# Make drop down lists for input files for cells that have discrete options, e.g. Links, SA multipliers
# On ki collect assume on average get 3.75 type orbs (50% same type, 50% other type, unless get bonus key per type ki sphere then 20% same type) and 1.25 rainbow orb ->6.5 ki on average
# Calculate average healing from Orbs- should really have input of # of same type and # of rainbow and other type
# Change input method so inputs don't depend on HP
# Add Hit points as variable
# Somehow take account of units requiring to get hit better
# Should include average enemy defence to account for crit ignnoring it. Will require reformat of getAvgAtt and branchAtt as should return a list of all attcks, not their sum
# Could store average from previous complete run so didn't have to completely rerun each time add new characters (Although inly doing a new complete run would give the true result)
nonTurnBasedKitEntries = 21 # Not including SA Mult 12 and 18 because too hard to change input format
activeIndex = 12
reviveIndex = 13
standbyIndex = 14
turnMax = 10
leaderSkillBuff = 4
leaderSkillKi = 6
avgSupport = 0.2
avgKiSupport = 1
nTeamsMax = 21
peakTurn = 3 # From Redzone spreadsheet, rounded
avgTypeAdvantage = 1.131725
avgTypeFactor = 1.09
avgGuardFactor = 0.78
guardMod = 0.5
dodgeCancelFrac = 0.1
kiSuperFrac = 0.55
MeleeSuperFrac = 0.13
CritMultiplier = 2.03
SEaaTMultiplier = 1.624
STOrbPerKi = 0.25
avgHealth = 650000
maxNormalDamage = np.append(np.linspace(330000,530000,peakTurn),[530000]*(turnMax-peakTurn),axis=0)
maxSADamage = np.append(np.linspace(924000,1855000,peakTurn),[1855000]*(turnMax-peakTurn),axis=0)
maxDefence = np.append(np.linspace(100000,110000,peakTurn),[110000]*(turnMax-peakTurn),axis=0)
SBR_df = 0.25 #discount factor of SBR ability per turn
HP_PHY = np.array([[2000,3700,4000,4700,5000],[2000,3300,3600,3910,4600]])
HP_STR = np.array([[2000,4100,4400,5100,5400],[2000,3300,3600,3910,4600]])
HP_AGL = np.array([[2000,3700,4000,4700,5000],[2000,4100,4400,4710,5400]])
HP_TEQ = np.array([[2000,4100,4400,5100,5400],[2000,3700,4000,4310,5000]])
HP_INT = np.array([[2000,3700,4000,4700,5000],[2000,3700,4000,4310,5000]])
HP_F2P = np.array([[3000,3240,3000,3240,3000],[2760,2760,3240,3000,3000]])
BRZ_STAT = 500
BRZ_HP = 0.02
SLV_HP = 0.04
GLD_HP1 = 0.05
GLD_HP2 = 0.01
# ATT,DEF,ADD,CRT,DGE
HP_D0 = {'AGL':[0,0,0.1,0,0],
         'INT':[0,0,0,0,0.05],
         'PHY':[0,0,0.1,0,0],
         'STR':[0,0,0,0.1,0],
         'TEQ':[0,0,0,0.1,0]}
HP_D1 = {('ADD','CRT'):[0,0,0.18,0.06,0],
         ('ADD','DGE'):[0,0,0.18,0,0.03],
         ('CRT','DGE'):[0,0,0,0.18,0.03],
         ('CRT','ADD'):[0,0,0.06,0.18,0],
         ('DGE','ADD'):[0,0,0.06,0,0.09],
         ('DGE','CRT'):[0,0,0,0.06,0.09]}
HP_D2 = {('ADD','CRT'):[0,0,0.12,0.06,0],
         ('ADD','DGE'):[0,0,0.12,0,0.03],
         ('CRT','DGE'):[0,0,0,0.12,0.03],
         ('CRT','ADD'):[0,0,0.06,0.12,0],
         ('DGE','ADD'):[0,0,0.06,0,0.06],
         ('DGE','CRT'):[0,0,0,0.06,0.06]}
HP_BRZ = {'ATT':[BRZ_STAT,0,0,0,0],
          'DEF':[0,BRZ_STAT,0,0,0],
          'ADD':[0,0,2*BRZ_HP,0,0],
          'CRT':[0,0,0,2*BRZ_HP,0],
          'DGE':[0,0,0,0,BRZ_HP]}
HP_SLV = {'ADD':[0,0,2*SLV_HP,0,0],
          'CRT':[0,0,0,2*SLV_HP,0],
          'DGE':[0,0,0,0,SLV_HP]}
HP_GLD = {('ADD','CRT'):[0,0,2*GLD_HP1,2*GLD_HP2,0],
         ('ADD','DGE'):[0,0,2*GLD_HP1,0,GLD_HP2],
         ('CRT','DGE'):[0,0,0,2*GLD_HP1,GLD_HP2],
         ('CRT','ADD'):[0,0,2*GLD_HP2,2*GLD_HP1,0],
         ('DGE','ADD'):[0,0,2*GLD_HP2,0,GLD_HP1],
         ('DGE','CRT'):[0,0,0,2*GLD_HP2,GLD_HP1]}
HP_SA_Mult = [6,7,8,14,15]
HP_Recovery = [7,7,8,9,15]
LRExclusivities = ['Carnival LR', 'LR', 'DF LR']

def GuardModifer(ExcessDamage,guardMod):
    modifiedExcessDamage = [0]*turnMax
    for i in range(turnMax):
        if ExcessDamage[i] >0:
            modifiedExcessDamage[i] = ExcessDamage[i]*guardMod
        else:
            modifiedExcessDamage[i] = ExcessDamage[i]/guardMod
    return modifiedExcessDamage
def ZTP_CDF(x,Lambda):
    return (poisson.cdf(x,Lambda)-poisson.cdf(0,Lambda))/(1-poisson.cdf(0,Lambda))
def SAMultiplier(multiplier,EZA,exclusivity,nCopies,nStacks,SA_Att):
    if(exclusivity=='Super Strike'):
        baseMultiplier = 6.3
    else:
        if(EZA):
            match multiplier:
                case 'Destructive':
                    baseMultiplier = 4.45
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
                case 'Destructive':
                    baseMultiplier = 4.2
                case 'Supreme':
                    baseMultiplier = 4.3
                case 'Immense':
                    baseMultiplier = 5.05
                case 'Colossal':
                    baseMultiplier = 4.25
                case 'Mega-Colossal':
                    baseMultiplier = 5.7
    stackingPenalty=0
    if (nStacks==turnMax): # If infinite stacker
        stackingPenalty = SA_Att
    return baseMultiplier+0.05*HP_SA_Mult[nCopies-1]-stackingPenalty
def KiMultiplier(base,ki):
    if ki<=12:
        return 1
    else:
        return (np.linspace(base,2,12))[ki-13]
def branchAtt(i,nAA,M_12,M_N,P_AA,nProcs,P_SA,P_g,N_0,A_12_0,SA_mult,P_HP):
    N = M_N * N_0
    A_12 = M_12 * A_12_0
    if(i == nAA - 1): #If no more additional attacks
        return 0.5 * P_AA * (A_12 + N) #Add average HP damage
    else:
        i+= 1 # Increment attack counter
        # Calculate extra attack if get additional super and subsequent addditional attacks
        tempAtt0 = branchAtt(i, nAA, M_12, M_N, P_AA, nProcs, P_SA, P_g, N_0, A_12_0, SA_mult, P_HP) # Add damage if don't get any additional attacks
        tempAtt1 = branchAtt(i, nAA, M_12, M_N, P_AA + P_HP * (1 - P_HP)**nProcs, nProcs + 1, P_SA, P_g, N_0, A_12_0, SA_mult, P_HP)
        tempAtt2 = branchAtt(i, nAA,M_12 + SA_mult, M_N + SA_mult, P_AA + P_HP * (1 - P_HP)**nProcs, nProcs + 1, P_SA, P_g, N_0, A_12_0, SA_mult, P_HP)
        return P_SA[i] * (tempAtt2 + A_12) + (1 - P_SA[i])* (P_g[i] * (tempAtt1 + N) + (1 - P_g[i]) * (tempAtt0))
            
def branchAA(i,nAA,P_AA,nProcs,P_SA,P_g,P_HP):
    if(i == nAA - 1): #If no more additional attacks
        return 0.5 * P_AA # Add average HP super chance
    else:
        i+= 1 # Increment attack counter
        # Calculate extra attack if get additional super and subsequent addditional attacks
        tempAA0 = branchAA(i, nAA, P_AA, nProcs, P_SA, P_g, P_HP) # Add damage if don't get any additional attacks
        tempAA1 = branchAA(i, nAA, P_AA + P_HP * (1 - P_HP) ** nProcs, nProcs + 1, P_SA, P_g, P_HP)
        return P_SA[i] * (1+tempAA1) + (1 - P_SA[i])* (P_g[i] * tempAA1 + (1 - P_g[i]) * tempAA0)
def getAttackDistribution(constantKi,randomKi,intentional12Ki,rarity):
    Pr_N= ZTP_CDF(max(11-constantKi,0),randomKi)
    if(intentional12Ki or rarity !='LR'):
        Pr_SA = 1-Pr_N
        Pr_USA = 0
    else:
        Pr_USA = 1-ZTP_CDF(max(17-constantKi,0),randomKi)
        Pr_SA = 1-Pr_N-Pr_USA
    return [Pr_N, Pr_SA, Pr_USA]
def getNormal(kiMod_12,ki,att,p1Att,stackedAtt,linkAtt_SoT,p2Att,p3Att):
    kiMultiplier = KiMultiplier(kiMod_12,ki)
    return att*(1+leaderSkillBuff)*(1+p1Att+stackedAtt)*(1+linkAtt_SoT)*(1+p2Att)*(1+p3Att)*kiMultiplier
def getSA(kiMod_12,att,p1Att,stackedAtt,linkAtt_SoT,p2Att,p3Att,SA_Mult_12,EZA,exclusivity,nCopies,SA_12_Att_Stacks,SA_12_Att):
    kiMultiplier = kiMod_12
    SAmultiplier = SAMultiplier(SA_Mult_12,EZA,exclusivity,nCopies,SA_12_Att_Stacks,SA_12_Att)
    return att*(1+leaderSkillBuff)*(1+p1Att)*(1+linkAtt_SoT)*(1+p2Att)*(1+p3Att)*kiMultiplier*(SAmultiplier+SA_12_Att+stackedAtt)
def getUSA(kiMod_12,ki,att,p1Att,stackedAtt,linkAtt_SoT,p2Att,p3Att,SA_Mult_18,EZA,exclusivity,nCopies,SA_18_Att_Stacks,SA_18_Att):
    kiMultiplier = KiMultiplier(kiMod_12,max(ki,18))
    SAmultiplier = SAMultiplier(SA_Mult_18,EZA,exclusivity,nCopies,SA_18_Att_Stacks,SA_18_Att)
    return att*(1+leaderSkillBuff)*(1+p1Att)*(1+linkAtt_SoT)*(1+p2Att)*(1+p3Att)*kiMultiplier*(SAmultiplier+SA_18_Att+stackedAtt)
def getActiveAttack(kiMod_12,ki,att,p1Att,stackedAtt,linkAtt_SoT,p2Att,p3Att,SA_Mult_Active,nCopies):
    kiMultiplier = KiMultiplier(kiMod_12,ki)
    SAmultiplier = SA_Mult_Active+0.05*HP_SA_Mult[nCopies-1]
    return att*(1+leaderSkillBuff)*(1+p1Att)*(1+linkAtt_SoT)*(1+p2Att)*(1+p3Att)*kiMultiplier*(1+stackedAtt)*SAmultiplier
def getAvgAtt(AA_P_super,SA_Mult_12,EZA,exclusivity,nCopies,SA_12_Att_Stacks,SA_12_Att,SA_18_Att,stackedAtt,p1Att,normal,sa,usa,HP_P_AA,AA_P_guarantee,P_counterNormal,P_counterSA,counterMod,Pr_N,Pr_SA,Pr_USA,rarity):
    nAA = len(AA_P_super) # Number of additional attacks from passive in each turn
    i = -1 # iteration counter
    nProcs = 1 # Initialise number of HP procs
    SAmultiplier = SAMultiplier(SA_Mult_12,EZA,exclusivity,nCopies,SA_12_Att_Stacks,SA_12_Att)
    M_12 = SAmultiplier+SA_12_Att+stackedAtt # 12 ki multiplier after SA effect
    A_12_0 = sa/M_12 # Get 12 ki SA attack stat without multiplier
    if(1+p1Att+stackedAtt==0):
        N_0 = 0
    else:
        N_0 = normal/(1+p1Att+stackedAtt) # Get normal attack stat without SoT attack        
    P_AA = HP_P_AA # Probability of doing an additional attack next
    P_SA = AA_P_super # Probability of doing a super on inbuilt additional
    P_g = AA_P_guarantee # Probability of inbuilt additional
    counterAtt = (4*P_counterNormal+0.5*P_counterSA)*counterMod*normal
    avgAtt = Pr_N*(normal+branchAtt(i,nAA,M_12,p1Att+stackedAtt,P_AA,nProcs,P_SA,P_g,N_0,A_12_0,SA_12_Att,HP_P_AA)) \
            + Pr_SA*(sa+branchAtt(i,nAA,M_12+SA_12_Att,p1Att+stackedAtt+SA_18_Att,P_AA,nProcs,P_SA,P_g,N_0,A_12_0,SA_12_Att,HP_P_AA))
    if(rarity=='LR'): # If  is a LR
        avgAtt += Pr_USA*(usa+branchAtt(i,nAA,M_12+SA_18_Att,p1Att+stackedAtt+SA_18_Att,P_AA,nProcs,P_SA,P_g,N_0,A_12_0,SA_12_Att,HP_P_AA))
    avgAtt += counterAtt
    return avgAtt
class Unit:
    def __init__(self,ID,nCopies,BRZ,HP1,HP2):
        self.ID = str(ID)
        self.nCopies = nCopies
        self.BRZ = BRZ
        self.HP1 = HP1
        self.HP2 = HP2
        self.kit = Kit(str(ID)).getKit()
        self.HP_Stats = self.getHP_Stats()
        self.HP = self.getHP()
        self.att = self.kit.attack+self.HP_Stats[0]+self.HP[0]
        self.defence =self.kit.defence+self.HP_Stats[1]+self.HP[1]
        self.HP_P_AA = self.HP[2]
        self.HP_P_Crit = self.HP[3]
        self.HP_P_Dodge = self.HP[4]
        self.leaderSkill = self.kit.leaderSkill
        [self.links_Commonality, self.links_Ki, self.linkAtt_SoT, self.linkDef, self.linkCrit, self.linkAtt_OnSuper, self.linkDodge, self.linkDmgRed, self.linkHealing] = self.getLinks()
        self.dmgRed = np.minimum(self.kit.dmgRed + self.linkDmgRed,[1]*turnMax)
        self.dmgRedNormal = np.minimum(self.kit.dmgRedNormal+self.dmgRed,[1]*turnMax)
        self.SBR = self.kit.SBR
        self.constantKi = leaderSkillKi+self.kit.passiveKi
        self.randomKi = self.links_Ki+self.kit.collectKi+avgKiSupport
        self.healing = self.kit.healing+self.linkHealing
        self.support = self.kit.support
        self.useability = self.kit.nTeams/nTeamsMax*(1+self.support[0]/5+self.links_Commonality[0])
        self.p1Att = np.maximum(self.kit.P1_Att+avgSupport,-1)
        self.p2Att = self.kit.P2_Att+self.linkAtt_OnSuper
        self.p1Def = self.kit.P1_Def+avgSupport
        self.p2Def = self.kit.P2A_Def+self.kit.P2B_Def
        self.p3Att = self.kit.P3_Att
        self.p3Def = self.kit.P3_Def
        self.P_Crit = self.kit.passiveCrit+(1-self.kit.passiveCrit)*(self.HP_P_Crit+(1-self.HP_P_Crit)*self.linkCrit)
        self.P_SEaaT = self.kit.P_SEaaT
        self.P_Dodge = self.kit.P_dodge + (1-self.kit.P_dodge) * (self.HP_P_Dodge+(1-self.HP_P_Dodge)*self.linkDodge)
        self.P_guard = self.kit.P_guard
        self.P_nullify = self.kit.P_nullify+ (1-self.kit.P_nullify) * self.kit.P_counterSA
        if self.kit.GRLength!=0:
            self.GRTurn = max(self.kit.activeTurn,peakTurn)
            self.att_GR = self.kit.attack_GR+self.HP_Stats[0]+self.HP[0]
            self.constantKi_GR = leaderSkillKi+self.kit.passiveKi_Active
            self.randomKi_GR = self.kit.collectKi_Active
            self.ki_GR = np.minimum((np.around(self.constantKi_GR + self.randomKi_GR)).astype('int32'),24)
            [self.Pr_N_GR, self.Pr_SA_GR, self.Pr_USA_GR] = getAttackDistribution(self.constantKi_GR,self.randomKi_GR,False,self.kit.rarity)
            self.normal_GR = getNormal(self.kit.kiMod_12,self.ki_GR,self.att_GR,0,0,0,0,0)
            self.sa_GR = getSA(self.kit.kiMod_12,self.att_GR,0,0,0,0,0,self.kit.SA_Mult_12_GR,self.kit.EZA,self.kit.exclusivity,self.nCopies,0,self.kit.SA_12_Att_GR)
            if self.kit.rarity == 'LR':
                self.usa_GR = getUSA(self.kit.kiMod_12,self.ki_GR,self.att_GR,0,0,0,0,0,self.kit.SA_Mult_18_GR,self.kit.EZA,self.kit.exclusivity,self.nCopies,0,self.kit.SA_18_Att_GR)
                self.avgAtt_GR = getAvgAtt(self.kit.AA_P_super_Active,self.kit.SA_Mult_12_GR,self.kit.EZA,self.kit.exclusivity,self.nCopies,0,self.kit.SA_12_Att_GR,self.kit.SA_18_Att_GR,0,0,self.normal_GR,self.sa_GR,self.usa_GR,self.HP_P_AA,self.kit.AA_P_guarantee_Active,0,0,0,self.Pr_N_GR,self.Pr_SA_GR,self.Pr_USA_GR,self.kit.rarity)
            else:
                self.avgAtt_GR = getAvgAtt(self.kit.AA_P_super_Active,self.kit.SA_Mult_12_GR,self.kit.EZA,self.kit.exclusivity,self.nCopies,0,self.kit.SA_12_Att_GR,0,0,0,self.normal_GR,self.sa_GR,0,self.HP_P_AA,self.kit.AA_P_guarantee_Active,0,0,0,self.Pr_N_GR,self.Pr_SA_GR,0,self.kit.rarity)
            self.P_Crit_GR = self.kit.passiveCrit_Active+(1-self.kit.passiveCrit_Active)*(self.HP_P_Crit)
            self.avgAttModifer_GR = self.P_Crit_GR*CritMultiplier+(1-self.P_Crit_GR)*(self.kit.P_SEaaT_Active*SEaaTMultiplier+(1-self.kit.P_SEaaT_Active)*avgTypeAdvantage)
            self.apt_GR = self.kit.GRLength*3*self.avgAtt_GR*self.avgAttModifer_GR
            #self.dpt_GR
        if self.kit.activeTurn!=0:
            self.SBR += SBR_df**(self.kit.activeTurn-1)*self.kit.SBR_Active
            self.activeSkillTurn = int(max(self.kit.activeTurn,peakTurn))
            self.dmgRed[self.activeSkillTurn-1] += self.kit.dmgRed_Active
            self.healing[self.activeSkillTurn-1] += self.kit.healing_Active
            self.support[self.activeSkillTurn-1] += self.kit.support_Active
            self.constantKi[self.activeSkillTurn-1] += self.kit.passiveKi_Active
            self.randomKi[self.activeSkillTurn-1] = self.links_Ki[self.activeSkillTurn-1]+self.kit.collectKi_Active+avgKiSupport
            self.P_Dodge[self.activeSkillTurn-1] = self.kit.P_dodge_Active+(1-self.kit.P_dodge_Active)*(self.kit.P_dodge[self.activeSkillTurn-1] + (1-self.kit.P_dodge[self.activeSkillTurn-1]) * (self.HP_P_Dodge+(1-self.HP_P_Dodge)*self.linkDodge[self.activeSkillTurn-1]))
            self.P_guard[self.activeSkillTurn-1] = self.kit.P_guard_Active+(1-self.kit.P_guard_Active)*self.kit.P_guard[self.activeSkillTurn-1]
            self.P_nullify[self.activeSkillTurn-1] = self.kit.P_nullify_Active+(1-self.kit.P_nullify_Active)*self.kit.P_nullify[self.activeSkillTurn-1]
            self.P_Crit[self.activeSkillTurn-1] = self.kit.passiveCrit_Active+(1-self.kit.passiveCrit_Active)*(self.kit.passiveCrit[self.activeSkillTurn-1] + (1-self.kit.passiveCrit[self.activeSkillTurn-1])*(self.HP_P_Crit+(1-self.HP_P_Crit)*self.linkCrit[self.activeSkillTurn-1]))
            self.P_SEaaT[self.activeSkillTurn-1] = self.kit.P_SEaaT_Active + (1-self.kit.P_SEaaT_Active)*self.kit.P_SEaaT[self.activeSkillTurn-1]
            self.kit.AA_P_super[self.activeSkillTurn-1] = self.kit.AA_P_super_Active
            self.kit.AA_P_guarantee[self.activeSkillTurn-1] = self.kit.AA_P_guarantee_Active
            if(self.kit.activeMult!=0): # If active skill attack
                self.p2Att[self.activeSkillTurn-1] = self.kit.P2_Att_Active
                self.p2Def[self.activeSkillTurn-1] = self.kit.P2A_Def[self.activeSkillTurn-1]+self.kit.P2B_Def_Active
                self.p3Att[self.activeSkillTurn-1] += self.kit.P3_Att_Active
                self.p3Def[self.activeSkillTurn-1] += self.kit.P3_Def_Active
        if self.kit.reviveTurn!=0:
            self.reviveSkillTurn = int(max(self.kit.reviveTurn,peakTurn))
            self.healing[self.reviveSkillTurn-1] += self.kit.healing_Revive
            self.support[self.reviveSkillTurn-1] += self.kit.support_Revive
        self.ki = np.minimum((np.around(self.constantKi + self.randomKi)).astype('int32'),[24]*turnMax)
        self.Pr_N, self.Pr_SA, self.Pr_USA, self.avg_AA_SA, self.normal,self.sa, self.usa, self.avgAtt = [0]*turnMax, [0]*turnMax, [0]*turnMax, [0]*turnMax, [0]*turnMax, [0]*turnMax, [0]*turnMax, [0]*turnMax
        for i in range(turnMax):
            [self.Pr_N[i], self.Pr_SA[i], self.Pr_USA[i]] = getAttackDistribution(self.constantKi[i],self.randomKi[i],self.kit.intentional12Ki[i],self.kit.rarity)
            self.avg_AA_SA[i] = branchAA(-1,len(self.kit.AA_P_super[i]),self.HP_P_AA,1,self.kit.AA_P_super[i],self.kit.AA_P_guarantee[i],self.HP_P_AA)
        [self.stackedAtt, self.stackedDef] = self.getStackedStats()
        for i in range(turnMax):
            self.normal[i] = getNormal(self.kit.kiMod_12,self.ki[i],self.att,self.p1Att[i],self.stackedAtt[i],self.linkAtt_SoT[i],self.p2Att[i],self.p3Att[i])
            self.sa[i] = getSA(self.kit.kiMod_12,self.att,self.p1Att[i],self.stackedAtt[i],self.linkAtt_SoT[i],self.p2Att[i],self.p3Att[i],self.kit.SA_Mult_12[i],self.kit.EZA,self.kit.exclusivity,self.nCopies,self.kit.SA_12_Att_Stacks[i],self.kit.SA_12_Att[i])
            if self.kit.rarity == 'LR':
                self.usa[i] = getUSA(self.kit.kiMod_12,self.ki[i],self.att,self.p1Att[i],self.stackedAtt[i],self.linkAtt_SoT[i],self.p2Att[i],self.p3Att[i],self.kit.SA_Mult_18[i],self.kit.EZA,self.kit.exclusivity,self.nCopies,self.kit.SA_18_Att_Stacks[i],self.kit.SA_18_Att[i])
                self.avgAtt[i] = getAvgAtt(self.kit.AA_P_super[i],self.kit.SA_Mult_12[i],self.kit.EZA,self.kit.exclusivity,self.nCopies,self.kit.SA_12_Att_Stacks[i],self.kit.SA_12_Att[i],self.kit.SA_18_Att[i],self.stackedAtt[i],self.p1Att[i],self.normal[i],self.sa[i],self.usa[i],self.HP_P_AA,self.kit.AA_P_guarantee[i],self.kit.P_counterNormal[i],self.kit.P_counterSA[i],self.kit.counterMod,self.Pr_N[i],self.Pr_SA[i],self.Pr_USA[i],self.kit.rarity)
                if self.kit.activeTurn !=0 and i==self.activeSkillTurn-1:
                    self.avgAtt[i] += getActiveAttack(self.kit.kiMod_12,24,self.att,self.p1Att[self.activeSkillTurn-1],self.stackedAtt[self.activeSkillTurn-1],self.linkAtt_SoT[self.activeSkillTurn-1],self.p2Att[self.activeSkillTurn-1],self.p3Att[self.activeSkillTurn-1],self.kit.activeMult,self.nCopies)
            else:
                self.avgAtt[i] = getAvgAtt(self.kit.AA_P_super[i],self.kit.SA_Mult_12[i],self.kit.EZA,self.kit.exclusivity,self.nCopies,self.kit.SA_12_Att_Stacks[i],self.kit.SA_12_Att[i],0,self.stackedAtt[i],self.p1Att[i],self.normal[i],self.sa[i],0,self.HP_P_AA,self.kit.AA_P_guarantee[i],self.kit.P_counterNormal[i],self.kit.P_counterSA[i],self.kit.counterMod,self.Pr_N[i],self.Pr_SA[i],self.Pr_USA[i],self.kit.rarity)
                if self.kit.activeTurn != 0 and i==self.activeSkillTurn-1:
                    self.avgAtt[i] += getActiveAttack(self.kit.kiMod_12,12,self.att,self.p1Att[self.activeSkillTurn-1],self.stackedAtt[self.activeSkillTurn-1],self.linkAtt_SoT[self.activeSkillTurn-1],self.p2Att[self.activeSkillTurn-1],self.p3Att[self.activeSkillTurn-1],self.kit.activeMult,self.nCopies)
        self.avgAttModifer = self.P_Crit*CritMultiplier+(1-self.P_Crit)*(self.P_SEaaT*SEaaTMultiplier+(1-self.P_SEaaT)*avgTypeAdvantage)
        self.apt = self.avgAtt*self.avgAttModifer
        if self.kit.GRLength!=0:
            self.apt[self.activeSkillTurn-1] += self.apt_GR
        self.avgDefMult = self.getAvgDefMult()
        self.avgDefPreSuper = self.defence*(1+leaderSkillBuff)*(1+self.p1Def)*(1+self.linkDef)*(1+self.kit.P2A_Def)*(1+self.p3Def)*(1+self.stackedDef)
        self.avgDefPostSuper = self.defence*(1+leaderSkillBuff)*(1+self.p1Def)*(1+self.linkDef)*(1+self.p2Def)*(1+self.p3Def)*(1+self.avgDefMult)
        self.normalDefencePreSuper = np.minimum(-(1-(1-dodgeCancelFrac)*self.P_Dodge)*(self.P_guard*GuardModifer(maxNormalDamage*avgGuardFactor*(1-self.dmgRedNormal)-self.avgDefPreSuper,guardMod)+(1-self.P_guard)*(maxNormalDamage*avgTypeFactor*(1-self.dmgRedNormal)-self.avgDefPreSuper))/(maxNormalDamage*avgTypeFactor),0.2)
        self.normalDefencePostSuper = np.minimum(-(1-(1-dodgeCancelFrac)*self.P_Dodge)*(self.P_guard*GuardModifer(maxNormalDamage*avgGuardFactor*(1-self.dmgRedNormal)-self.avgDefPostSuper,guardMod)+(1-self.P_guard)*(maxNormalDamage*avgTypeFactor*(1-self.dmgRedNormal)-self.avgDefPostSuper))/(maxNormalDamage*avgTypeFactor),0.2)
        self.saDefencePreSuper = np.minimum(-(1-(self.P_nullify+(1-self.P_nullify)*(1-dodgeCancelFrac)*self.P_Dodge))*(self.P_guard*GuardModifer(maxSADamage*avgGuardFactor*(1-self.dmgRed)-self.avgDefPreSuper,guardMod)+(1-self.P_guard)*(maxSADamage*avgTypeFactor*(1-self.dmgRed)-self.avgDefPreSuper))/(maxSADamage*avgTypeFactor),0.2)
        self.saDefencePostSuper = np.minimum(-(1-(self.P_nullify+(1-self.P_nullify)*(1-dodgeCancelFrac)*self.P_Dodge))*(self.P_guard*GuardModifer(maxSADamage*avgGuardFactor*(1-self.dmgRed)-self.avgDefPostSuper,guardMod)+(1-self.P_guard)*(maxSADamage*avgTypeFactor*(1-self.dmgRed)-self.avgDefPostSuper))/(maxSADamage*avgTypeFactor),0.2)
        self.slot1Ability = np.maximum(self.normalDefencePreSuper+self.saDefencePreSuper,-0.5)
        self.healing += (0.03+0.0015*HP_Recovery[self.nCopies-1])*self.avgDefPreSuper*self.kit.collectKi*STOrbPerKi/avgHealth
        self.attributes = [self.leaderSkill, self.SBR,self.useability, self.healing, self.support,self.apt,self.normalDefencePostSuper,self.saDefencePostSuper,self.slot1Ability]
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
    def getHP(self):
        HP = np.array(HP_D0[self.kit.type]) + HP_BRZ[self.BRZ] + HP_SLV[self.HP1]
        if self.nCopies > 1:
            HP += HP_D1[(self.HP1,self.HP2)]
        if self.nCopies > 2:
            HP += np.array(HP_D2[(self.HP1,self.HP2)]) + HP_GLD[(self.HP1,self.HP2)]
        return HP
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

    def getStackedStats(self):
        # Can make more efficient later by saving stacked attack for each turn and just add on next turn, rather than calculating the whole thing on each call
        stackedAtt, stackedDef = [0]*turnMax, [0]*turnMax
        for turn in range(turnMax-1): # For each turn < self.turn (i.e. turns which can affect how much defense have on self.turn)
            if(self.kit.keepStacking):
                i = 0 # If want the stacking of initial turn and transform later 
            else:
                i = turn
            if(self.kit.SA_18_Att_Stacks[i]>1): # If stack for long enough to last to turn self.turn
                stackedAtt[turn+1:turn+self.kit.SA_18_Att_Stacks[i]] += self.Pr_USA[i]*self.kit.SA_18_Att[i] # add stacked att
            if(self.kit.SA_18_Def_Stacks[i]>1): # If stack for long enough to last to turn self.turn
                stackedDef[turn+1:turn+self.kit.SA_18_Def_Stacks[i]] += self.Pr_USA[i]*self.kit.SA_18_Def[i] # add stacked att
            if(self.kit.SA_12_Att_Stacks[i]>1): # If stack for long enough to last to turn self.turn
                stackedAtt[turn+1:turn+self.kit.SA_12_Att_Stacks[i]] += (self.Pr_SA[i]+self.avg_AA_SA[i])*self.kit.SA_12_Att[i] # add stacked att
            if(self.kit.SA_12_Def_Stacks[i]>1): # If stack for long enough to last to turn self.turn
                stackedDef[turn+1:turn+self.kit.SA_12_Def_Stacks[i]] += (self.Pr_SA[i]+self.avg_AA_SA[i])*self.kit.SA_12_Def[i] # add stacked att
        return [np.array(stackedAtt), np.array(stackedDef)]
    def getAvgDefMult(self):
        if(self.kit.rarity=='LR'): # If unit is a LR
            avgDefMult = self.Pr_SA*self.kit.SA_12_Def+self.Pr_USA*self.kit.SA_18_Def
        else:
            avgDefMult = self.Pr_SA*self.kit.SA_12_Def
        avgDefMult += self.stackedDef + self.avg_AA_SA*self.kit.SA_12_Def
        return avgDefMult  
class Kit:
    def __init__(self,ID):
        self.ID = ID
        self.linkCommonality = None
        self.links = np.array([[None]*turnMax for i in range(7)])
    def getKit(self):
        filepath = 'C:/Users/Tyler/Documents/DokkanAnalysis/DokkanKits/'+self.ID+'.xlsx'
        with open(filepath,'rb') as file:
            kitData = (pd.read_excel(file)).to_numpy()
            for i in range(nonTurnBasedKitEntries):
                match kitData[i,0]:
                    case 'Exclusivity':
                        self.exclusivity = kitData[i,1]
                        if(self.exclusivity in LRExclusivities):
                            self.rarity = 'LR'
                        else:
                            self.rarity = 'TUR'
                    case 'Name':
                        self.name = kitData[i,1]
                    case 'Class':
                        self.Class = kitData[i,1]
                    case 'Type':
                        self.type = kitData[i,1]
                    case 'EZA':
                        self.EZA = bool(int(kitData[i,1]))
                    case 'JP Release':
                        self.JP_releaseDate = kitData[i,1]
                    case 'GLB Release':
                        self.GLB_releaseDate = kitData[i,1]
                    case 'Att':
                        self.attack = int(kitData[i,1])
                        self.attack_GR = int(kitData[i,activeIndex])
                    case 'Def':
                        self.defence = int(kitData[i,1])
                    case 'Leader Skill':
                        self.leaderSkill = float(kitData[i,1])
                    case 'Teams': # Only teams which would acutally run on. For units with big restrictions, restrict to those teams
                        self.nTeams = int(kitData[i,1])
                    case 'SBR':
                        self.SBR = float(kitData[i,1])
                        self.SBR_Active = kitData[i,activeIndex]
                    case 'Ki Mod 12':
                        self.kiMod_12 = float(kitData[i,1])
                    case 'SA Mult 12':
                        buildUpTime = int(kitData[i,1])
                        self.SA_Mult_12 = np.append(kitData[i,2:buildUpTime+1],[kitData[i,buildUpTime+1]]*(turnMax-buildUpTime+1),axis=0)
                        self.SA_Mult_12_GR = kitData[i,activeIndex]
                    case 'SA Mult 18':
                        if(self.rarity == 'LR'):
                            buildUpTime = int(kitData[i,1])
                            self.SA_Mult_18 = np.append(kitData[i,2:buildUpTime+1],[kitData[i,buildUpTime+1]]*(turnMax-buildUpTime+1),axis=0)
                            self.SA_Mult_18_GR = kitData[i,activeIndex]
                    case 'Counter Mod':
                        self.counterMod = float(kitData[i,1])
                    case 'KeepStacking':
                        self.keepStacking = bool(kitData[i,1])
                    case 'Active Skill Turn':
                        self.activeTurn = float(kitData[i,1])
                    case 'Active Skill Attack Multiplier':
                        self.activeMult = float(kitData[i,1])
                    case 'Revival Skill Turn':
                        self.reviveTurn = float(kitData[i,1])
                    case 'Giant/Rage Length':
                        self.GRLength = float(kitData[i,1])
            for i in range(nonTurnBasedKitEntries,len(kitData)):
                buildUpTime = int(kitData[i,1])
                extended = np.append(kitData[i,2:buildUpTime+1],[kitData[i,buildUpTime+1]]*(turnMax-buildUpTime+1),axis=0)
                match kitData[i,0]:
                    case 'P1 Att':
                        self.P1_Att = extended.astype('float64')
                    case 'P1 Def':
                        self.P1_Def = extended.astype('float64')
                    case 'P2 Att':
                        self.P2_Att = extended.astype('float64')
                        self.P2_Att_Active = kitData[i,activeIndex]
                    case 'P2A Def':
                        self.P2A_Def = extended.astype('float64')
                    case 'P2B Def':
                        self.P2B_Def = extended.astype('float64')
                        self.P2B_Def_Active = kitData[i,activeIndex]
                    case 'P3 Att':
                        self.P3_Att = extended.astype('float64')
                        self.P3_Att_Active = kitData[i,activeIndex]
                    case 'P3 Def':
                        self.P3_Def = extended.astype('float64')
                        self.P3_Def_Active = kitData[i,activeIndex]
                    case 'SA 12 Att':
                        self.SA_12_Att = extended.astype('float64')
                        self.SA_12_Att_GR = kitData[i,activeIndex]
                    case 'SA 12 Att Stacks':
                        self.SA_12_Att_Stacks = extended.astype('int32')
                    case 'SA 12 Def':
                        self.SA_12_Def = extended.astype('float64')
                    case 'SA 12 Def Stacks':
                        self.SA_12_Def_Stacks = extended.astype('int32')
                    case 'SA 18 Att':
                        self.SA_18_Att = extended.astype('float64')
                        self.SA_18_Att_GR = kitData[i,activeIndex]
                    case 'SA 18 Att Stacks':
                        self.SA_18_Att_Stacks = extended.astype('int32')
                    case 'SA 18 Def':
                        self.SA_18_Def= extended.astype('float64')
                    case 'SA 18 Def Stacks':
                        self.SA_18_Def_Stacks= extended.astype('int32')
                    case 'Link 1 Commonality':
                        self.linkCommonality = extended.astype('float64')
                    case 'Link 1':
                        self.links[0][:] = [Link(name).getLink(self.linkCommonality[0]) for name in extended]
                    case 'Link 2 Commonality':
                        self.linkCommonality = extended.astype('float64')
                    case 'Link 2':
                        self.links[1][:] = [Link(name).getLink(self.linkCommonality[0]) for name in extended]
                    case 'Link 3 Commonality':
                        self.linkCommonality = extended.astype('float64')
                    case 'Link 3':
                        self.links[2][:] = [Link(name).getLink(self.linkCommonality[0]) for name in extended]
                    case 'Link 4 Commonality':
                        self.linkCommonality = extended.astype('float64')
                    case 'Link 4':
                        self.links[3][:] = [Link(name).getLink(self.linkCommonality[0]) for name in extended]
                    case 'Link 5 Commonality':
                        self.linkCommonality = extended.astype('float64')
                    case 'Link 5':
                        self.links[4][:] = [Link(name).getLink(self.linkCommonality[0]) for name in extended]
                    case 'Link 6 Commonality':
                        self.linkCommonality = extended.astype('float64')
                    case 'Link 6':
                        self.links[5][:] = [Link(name).getLink(self.linkCommonality[0]) for name in extended]
                    case 'Link 7 Commonality':
                        self.linkCommonality = extended.astype('float64')
                    case 'Link 7':
                        self.links[6][:] = [Link(name).getLink(self.linkCommonality[0]) for name in extended]
                    case 'Passive Ki':
                        self.passiveKi = extended.astype('float64')
                        self.passiveKi_Active = kitData[i,activeIndex]
                    case 'Collect Ki':
                        self.collectKi = extended.astype('float64')
                        self.collectKi_Active = kitData[i,activeIndex]
                    case 'Intentional 12 Ki':
                        self.intentional12Ki = extended.astype('float64') 
                    case 'Healing':
                        self.healing = extended.astype('float64')
                        self.healing_Active = kitData[i,activeIndex]
                        self.healing_Revive = kitData[i,reviveIndex]
                    case 'Support':
                        self.support = extended.astype('float64')
                        self.support_Active = kitData[i,activeIndex]
                        self.support_Revive = kitData[i,reviveIndex]
                    case 'P Guard':
                        self.P_guard = extended.astype('float64')
                        self.P_guard_Active = kitData[i,activeIndex]
                    case 'Dmg Red Normal':
                        self.dmgRedNormal = extended.astype('float64')
                    case 'Dmg Red':
                        self.dmgRed = extended.astype('float64')
                        if not(np.isnan(kitData[i,activeIndex])):
                            self.dmgRed_Active = kitData[i,activeIndex]
                        else:
                            self.dmgRed_Active = 0
                    case 'P Dodge':
                        self.P_dodge = extended.astype('float64')
                        self.P_dodge_Active = kitData[i,activeIndex]
                    case 'P Counter Normal':
                        self.P_counterNormal = extended.astype('float64')
                    case 'P Counter SA':
                        self.P_counterSA = extended.astype('float64')
                    case 'P Nullify':
                        self.P_nullify = extended.astype('float64')
                        self.P_nullify_Active = kitData[i,activeIndex]
                    case 'AA P Super':
                        listOfLists = [[] for i in range(turnMax)]
                        for j in range(turnMax):
                            elements = (extended[j]).strip('][').split(',')
                            if (elements[0] != ''):
                                listOfLists[j] = np.array(elements).astype('float64')
                        self.AA_P_super = listOfLists
                        elements = (kitData[i,activeIndex]).strip('][').split(',')
                        self.AA_P_super_Active = []
                        if (elements[0] != ''):
                            self.AA_P_super_Active = np.array(elements).astype('float64')
                    case 'AA P Guarantee':
                        listOfLists = [[] for i in range(turnMax)]
                        for j in range(turnMax):
                            elements = (extended[j]).strip('][').split(',')
                            if (elements[0] != ''):
                                listOfLists[j] = np.array(elements).astype('float64')
                        self.AA_P_guarantee = listOfLists
                        elements = (kitData[i,activeIndex]).strip('][').split(',')
                        self.AA_P_guarantee_Active = []
                        if (elements[0] != ''):
                            self.AA_P_guarantee_Active = np.array(elements).astype('float64')
                    case 'Passive Crit':
                        self.passiveCrit = extended.astype('float64')
                        self.passiveCrit_Active = kitData[i,activeIndex]
                    case 'P SEaaT':
                        self.P_SEaaT = extended.astype('float64')
                        self.P_SEaaT_Active = kitData[i,activeIndex]
        file.close()
        return self
class Link:
    def __init__(self,name):
        self.name = name
    def getLink(self,commonality):
        filepath = 'C:/Users/Tyler/Documents/DokkanAnalysis/LinkTable.csv'
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
        if np.isnan(commonality):
            self.commonality = float(linkData[i,9])
        else:
            self.commonality = float(commonality)
        file.close()
        return self