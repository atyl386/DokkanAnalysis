import click as clc
from scipy.stats import poisson
import copy
from dokkanUnitConstants import *
from ast import literal_eval

#################################################### Helper functions #######################################################################


def simplest_type(s):
    try:
        return literal_eval(s)
    except:
        return s


def maxHealthCDF(maxHealth):
    """Returns the probability that health is less than the input"""
    return 4 / 3 * maxHealth**3 - maxHealth**2 + 2 / 3 * maxHealth


def ZTP_CDF(x, Lambda):
    """Returns the cdf(x) of a zero-truncated poisson distribution(lambda)"""
    return max((poisson.cdf(x, Lambda) - poisson.cdf(0, Lambda)) / (1 - poisson.cdf(0, Lambda)), 0)


def SAMultiplier(baseMultiplier, nCopies, nStacks, saAtk):
    """Returns the super-attack multiplier of a form"""
    stackingPenalty = 0
    if nStacks > 1:  # If stack attack
        stackingPenalty = saAtk
    return baseMultiplier + SA_BOOST_INC * HIPO_SA_BOOST[nCopies - 1] - stackingPenalty


def KiModifier(base, ki):
    """Returns the ki modifier for a unit (only used for normals and Ultras)"""
    if ki <= 12:
        return 1
    else:
        return np.linspace(base, 2, 13)[ki - 12]


def branchAPT(
    i,
    nAA,
    m12,
    mN,
    p2Atk,
    pAA,
    nProcs,
    pSA,
    pG,
    n_0,
    a12_0,
    saMult,
    pHiPo,
    crit,
    critMultiplier,
    atkModifier,
    p2AtkBuff,
    atkPerAttackPerformed,
    critPerAttackPerformed,
    atkPerSuperPerformed,
    critPerSuperPerformed,
    sa12Crit,
):
    """Returns the total remaining APT of a unit in a turn recursively"""
    p2AtkFactor = (1 + p2Atk + p2AtkBuff) / (1 + p2Atk)
    normal = mN * n_0 * p2AtkFactor * atkModifier
    additional12Ki = m12 * a12_0 * p2AtkFactor * atkModifier
    if i == nAA - 1:  # If no more additional attacks
        return 0.5 * pAA * (additional12Ki + normal)  # Add average hidden-potential attack damage
    else:
        i += 1  # Increment attack counter
        # Calculate extra attack if get additional super and subsequent addditional attacks
        # Add damage if don't get any additional attacks
        crit0 = copy.copy(crit)
        crit.updateChance("On Super", critPerAttackPerformed[0], "Crit")
        crit1 = copy.copy(crit)
        crit.updateChance("On Super", critPerSuperPerformed[0] - critPerAttackPerformed[0], "Crit")
        crit.updateChance("Super Attack Effect", sa12Crit, "Crit")
        crit2 = copy.copy(crit)
        if crit0.prob == 1:
            atkModifier1 = critMultiplier
            atkModifier2 = critMultiplier
        else:
            atkModifier1 = (atkModifier - critMultiplier * crit0.prob) / (1 - crit0.prob) * (
                1 - crit1.prob
            ) + crit1.prob * critMultiplier
            atkModifier2 = (atkModifier - critMultiplier * crit0.prob) / (1 - crit0.prob) * (
                1 - crit2.prob
            ) + crit2.prob * critMultiplier

        tempAPT0 = branchAPT(
            i,
            nAA,
            m12,
            mN,
            p2Atk,
            pAA,
            nProcs,
            pSA,
            pG,
            n_0,
            a12_0,
            saMult,
            pHiPo,
            crit0,
            critMultiplier,
            atkModifier,
            p2AtkBuff,
            atkPerAttackPerformed,
            critPerAttackPerformed,
            atkPerSuperPerformed,
            critPerSuperPerformed,
            sa12Crit,
        )
        tempAPT1 = branchAPT(
            i,
            nAA,
            m12,
            mN,
            p2Atk,
            pAA + pHiPo * (1 - pHiPo) ** nProcs,
            nProcs + 1,
            pSA,
            pG,
            n_0,
            a12_0,
            saMult,
            pHiPo,
            crit1,
            critMultiplier,
            atkModifier1,
            p2AtkBuff + atkPerAttackPerformed[0],
            atkPerAttackPerformed[1:],
            critPerAttackPerformed[1:],
            atkPerSuperPerformed,
            critPerSuperPerformed,
            sa12Crit,
        )
        tempAPT2 = branchAPT(
            i,
            nAA,
            m12 + saMult,
            mN + saMult,
            p2Atk,
            pAA + pHiPo * (1 - pHiPo) ** nProcs,
            nProcs + 1,
            pSA,
            pG,
            n_0,
            a12_0,
            saMult,
            pHiPo,
            crit2,
            critMultiplier,
            atkModifier2,
            p2AtkBuff + atkPerSuperPerformed[0],
            atkPerAttackPerformed,
            critPerAttackPerformed,
            atkPerSuperPerformed[1:],
            critPerSuperPerformed[1:],
            sa12Crit,
        )
        return pSA[i] * (tempAPT2 + additional12Ki) + (1 - pSA[i]) * (
            pG[i] * (tempAPT1 + normal) + (1 - pG[i]) * (tempAPT0)
        )


def branchAS(i, nAA, pAA, nProcs, pSA, pG, pHiPo):
    """Returns the average number of remaining super attacks in a turn recursively"""
    if i == nAA - 1:  # If no more additional attacks
        return 0.5 * pAA  # Add average HiPo super chance
    else:
        i += 1  # Increment attack counter
        # Calculate extra attack if get additional super and subsequent addditional attacks
        # Add damage if don't get any additional attacks
        tempAA0 = branchAS(i, nAA, pAA, nProcs, pSA, pG, pHiPo)
        tempAA1 = branchAS(i, nAA, pAA + pHiPo * (1 - pHiPo) ** nProcs, nProcs + 1, pSA, pG, pHiPo)
        return pSA[i] * (1 + tempAA1) + (1 - pSA[i]) * (pG[i] * tempAA1 + (1 - pG[i]) * tempAA0)


def branchAA(i, nAA, pAA, nProcs, pSA, pG, pHiPo):
    """Returns the average number of remaining attacks in a turn recursively"""
    if i == nAA - 1:  # If no more additional attacks
        return pAA  # Add average HiPo super chance
    else:
        i += 1  # Increment attack counter
        # Calculate extra attack if get additional super and subsequent addditional attacks
        # Add damage if don't get any additional attacks
        tempAA0 = branchAA(i, nAA, pAA, nProcs, pSA, pG, pHiPo)
        tempAA1 = branchAA(i, nAA, pAA + pHiPo * (1 - pHiPo) ** nProcs, nProcs + 1, pSA, pG, pHiPo)
        return pSA[i] * (1 + tempAA1) + (1 - pSA[i]) * (pG[i] * (1 + tempAA1) + (1 - pG[i]) * tempAA0)


def getAttackDistribution(constantKi, randomKi, intentional12Ki, rarity):
    """Returns the probability of normals, super-attacks and ultra-super-attacks"""
    pN = ZTP_CDF(max(11 - constantKi, 0), randomKi)
    if intentional12Ki or rarity != "LR":
        pSA = 1 - pN
        pUSA = 0
    else:
        pUSA = 1 - ZTP_CDF(max(17 - constantKi, 0), randomKi)
        pSA = 1 - pN - pUSA
    return [pN, pSA, pUSA]


def getAtkStat(ATK, p1Atk, linkAtk, p2Atk, p3Atk, kiMultiplier, saMultiplier):
    return (
        ATK
        * (1 + LEADER_SKILL_STATS)
        * (1 + p1Atk)
        * (1 + linkAtk)
        * (1 + p2Atk)
        * (1 + p3Atk)
        * kiMultiplier
        * saMultiplier
    )


def getDefStat(DEF, p1Def, linkDef, p2Def, p3Def, defMultiplier):
    return (
        DEF * (1 + LEADER_SKILL_STATS) * (1 + p1Def) * (1 + linkDef) * (1 + p2Def) * (1 + p3Def) * (1 + defMultiplier)
    )


def getNormal(kiMod12, ki, ATK, p1Atk, stackedAtk, linkAtkSoT, p2Atk, p3Atk):
    """Returns the ATK stat of a normal"""
    kiMultiplier = KiModifier(kiMod12, ki)
    return getAtkStat(ATK, p1Atk + stackedAtk, linkAtkSoT, p2Atk, p3Atk, kiMultiplier, 1)


def getSA(
    kiMod12,
    ATK,
    p1Atk,
    stackedAtk,
    linkAtkSoT,
    p2Atk,
    p3Atk,
    saMult12,
    nCopies,
    sa12AtkStacks,
    sa12Atk,
):
    """Returns the ATK stat of a super-attack"""
    kiMultiplier = kiMod12
    saMultiplier = SAMultiplier(saMult12, nCopies, sa12AtkStacks, sa12Atk)
    return getAtkStat(ATK, p1Atk, linkAtkSoT, p2Atk, p3Atk, kiMultiplier, saMultiplier + sa12Atk + stackedAtk)


def getUSA(
    kiMod12,
    ki,
    ATK,
    p1Atk,
    stackedAtk,
    linkAtkSoT,
    p2Atk,
    p3Atk,
    saMult18,
    nCopies,
    sa18AtkStacks,
    sa18Atk,
):
    """Returns the ATK stat of an ultra-super-attack"""
    kiMultiplier = KiModifier(kiMod12, max(ki, 18))
    saMultiplier = SAMultiplier(saMult18, nCopies, sa18AtkStacks, sa18Atk)
    return getAtkStat(ATK, p1Atk, linkAtkSoT, p2Atk, p3Atk, kiMultiplier, saMultiplier + sa18Atk + stackedAtk)


def getActiveAtk(
    kiMod12,
    ki,
    ATK,
    p1Atk,
    stackedAtk,
    linkAtkSoT,
    p2Atk,
    p3Atk,
    saMultActive,
    nCopies,
):
    """Returns the ATK stat of an active-skill attack"""
    kiMultiplier = KiModifier(kiMod12, ki)
    saMultiplier = saMultActive + SA_BOOST_INC * HIPO_SA_BOOST[nCopies - 1]
    return getAtkStat(ATK, p1Atk, linkAtkSoT, p2Atk, p3Atk, kiMultiplier, saMultiplier * (1 + stackedAtk))


def getAPT(
    AApSuper,
    saMult12,
    nCopies,
    sa12AtkStacks,
    addSAAtk,
    sa12Atk,
    sa18Atk,
    atk1Buff,
    stackedAtk,
    p1Atk,
    p2Atk,
    normal,
    addSA,
    sa,
    usa,
    HiPopAA,
    aaPGuarantee,
    pCounterSA,
    normalCounterMult,
    saCounterMult,
    pN,
    pSA,
    pUSA,
    rarity,
    slot,
    canAttack,
    crit,
    critMultiplier,
    preAtkModifier,
    atkPerAttackPerformed,
    atkPerSuperPerformed,
    critPerAttackPerformed,
    critPerSuperPerformed,
    addSACrit,
    sa12Crit,
    sa18Crit,
):
    """Returns the APT of a unit in a turn"""
    if canAttack:
        # Number of additional attacks from passive in each turn
        nAA = len(AApSuper)
        i = -1  # iteration counter
        nProcs = 1  # Initialise number of HiPo procs
        saMultiplier = SAMultiplier(saMult12, nCopies, sa12AtkStacks, addSAAtk)
        m12 = saMultiplier + addSAAtk + stackedAtk  # 12 ki multiplier after SA effect
        a12_0 = addSA / m12  # Get 12 ki SA attack stat without multiplier
        baseAtk = 1 + p1Atk + stackedAtk
        n_0 = normal / baseAtk
        pAA = HiPopAA  # Probability of doing an additional attack next
        pAASA = AApSuper  # Probability of doing a super on inbuilt additional
        pG = aaPGuarantee  # Probability of inbuilt additional
        counterAtk = (
            NUM_ATTACKS_DIRECTED[slot - 1] * normalCounterMult
            + NUM_SUPER_ATTACKS_DIRECTED[slot - 1] * pCounterSA * saCounterMult
        ) * normal
        pCrit0 = crit.prob
        crit.updateChance("On Super", critPerAttackPerformed[0], "Crit")
        critN = copy.copy(crit)
        crit.updateChance("On Super", critPerSuperPerformed[0] - critPerAttackPerformed[0], "Crit")
        crit.updateChance("Super Attack Effect", sa12Crit, "Crit")
        critSA = copy.copy(crit)
        crit.updateChance("Super Attack Effect", sa18Crit - sa12Crit, "Crit")
        critUSA = copy.copy(crit)
        if pCrit0 == 1:
            atkModifierN = critMultiplier
            atkModifierSA = critMultiplier
            atkModifierUSA = critMultiplier
        else:
            atkModifierN = (preAtkModifier - critMultiplier * pCrit0) / (1 - pCrit0) * (
                1 - critN.prob
            ) + critN.prob * critMultiplier
            atkModifierSA = (preAtkModifier - critMultiplier * pCrit0) / (1 - pCrit0) * (
                1 - critSA.prob
            ) + critSA.prob * critMultiplier
            atkModifierUSA = (preAtkModifier - critMultiplier * pCrit0) / (1 - pCrit0) * (
                1 - critUSA.prob
            ) + critUSA.prob * critMultiplier

        apt = pN * (
            normal * preAtkModifier * (1 + atk1Buff)
            + branchAPT(
                i,
                nAA,
                m12,
                baseAtk,
                p2Atk,
                pAA,
                nProcs,
                pAASA,
                pG,
                n_0,
                a12_0,
                addSAAtk,
                HiPopAA,
                critN,
                critMultiplier,
                atkModifierN,
                atkPerAttackPerformed[0],
                atkPerAttackPerformed[1:],
                critPerAttackPerformed[1:],
                atkPerSuperPerformed,
                critPerSuperPerformed,
                addSACrit,
            )
        ) + pSA * (
            sa * preAtkModifier * (1 + atk1Buff)
            + branchAPT(
                i,
                nAA,
                m12 + sa12Atk,
                baseAtk + sa12Atk,
                p2Atk,
                pAA,
                nProcs,
                pAASA,
                pG,
                n_0,
                a12_0,
                addSAAtk,
                HiPopAA,
                critSA,
                critMultiplier,
                atkModifierSA,
                atkPerSuperPerformed[0],
                atkPerAttackPerformed,
                critPerAttackPerformed,
                atkPerSuperPerformed[1:],
                critPerSuperPerformed[1:],
                addSACrit,
            )
        )
        if rarity == "LR":  # If  is a LR
            apt += pUSA * (
                usa * preAtkModifier * (1 + atk1Buff)
                + branchAPT(
                    i,
                    nAA,
                    m12 + sa18Atk,
                    baseAtk + sa18Atk,
                    p2Atk,
                    pAA,
                    nProcs,
                    pAASA,
                    pG,
                    n_0,
                    a12_0,
                    addSAAtk,
                    HiPopAA,
                    critUSA,
                    critMultiplier,
                    atkModifierUSA,
                    atkPerSuperPerformed[0],
                    atkPerAttackPerformed,
                    critPerAttackPerformed,
                    atkPerSuperPerformed[1:],
                    critPerSuperPerformed[1:],
                    addSACrit,
                )
            )
        apt += counterAtk * preAtkModifier
    else:
        apt = 0
    return apt


def getDamageTaken(pNullify, pEvade, guard, maxDamage, tdb, dmgRed, avgDef):
    assert pNullify <= 1
    assert pEvade <= 1
    assert guard <= 1
    return max(min(
        -(1 - (pNullify + (1 - pNullify) * (1 - DODGE_CANCEL_FACTOR) * pEvade))
        * (
            guard * GUARD_MOD * (maxDamage * (AVG_GUARD_FACTOR - TDB_INC * tdb) * (1 - dmgRed) - avgDef)
            + (1 - guard) * (maxDamage * (AVG_TYPE_ADVANATGE - TDB_INC * tdb) * (1 - dmgRed) - avgDef)
        )
        / AVG_HEALTH,
        0,
    ), -1)


def aprioriProbMod(p, knownApriori):
    if knownApriori:
        return 1 - (1 - p) ** 2
    else:
        return p


def logisticMap(x, x_max, L=100, d=1, x_min=-7):
    L = L + d
    x_0 = (x_min + x_max) / 2
    k = 2 * np.log((L - d) / d) / (x_max - x_min)
    return L / (1 + np.exp(-k * (x - x_0)))


class MultiChanceBuff:
    def __init__(self, effect):
        self.chances = copy.copy(NULL_MULTI_CHANCE_DICT[effect])
        self.prob = 0

    def calcProb(self):
        return 1 - np.prod([max(1 - p, 0) for p in self.chances.values()])

    def updateAttacksReceivedAndEvaded(self, state):
        pass

    def updateChance(self, chanceKey, increment, effect, state=None):
        self.chances[chanceKey] += increment
        self.prob = self.calcProb()
        if "Evasion" in effect:
            self.updateAttacksReceivedAndEvaded(state)
