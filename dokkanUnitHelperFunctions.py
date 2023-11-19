import click as clc
from scipy.stats import poisson
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


def branchAtk(i, nAA, m12, mN, pAA, nProcs, pSA, pG, n_0, a12_0, saMult, pHiPo):
    """Returns the total remaining ATK of a unit in a turn recursively"""
    normal = mN * n_0
    additional12Ki = m12 * a12_0
    if i == nAA - 1:  # If no more additional attacks
        return 0.5 * pAA * (additional12Ki + normal)  # Add average hidden-potential attack damage
    else:
        i += 1  # Increment attack counter
        # Calculate extra attack if get additional super and subsequent addditional attacks
        # Add damage if don't get any additional attacks
        tempAtk0 = branchAtk(i, nAA, m12, mN, pAA, nProcs, pSA, pG, n_0, a12_0, saMult, pHiPo)
        tempAtk1 = branchAtk(
            i,
            nAA,
            m12,
            mN,
            pAA + pHiPo * (1 - pHiPo) ** nProcs,
            nProcs + 1,
            pSA,
            pG,
            n_0,
            a12_0,
            saMult,
            pHiPo,
        )
        tempAtk2 = branchAtk(
            i,
            nAA,
            m12 + saMult,
            mN + saMult,
            pAA + pHiPo * (1 - pHiPo) ** nProcs,
            nProcs + 1,
            pSA,
            pG,
            n_0,
            a12_0,
            saMult,
            pHiPo,
        )
        return pSA[i] * (tempAtk2 + additional12Ki) + (1 - pSA[i]) * (
            pG[i] * (tempAtk1 + normal) + (1 - pG[i]) * (tempAtk0)
        )


def branchAA(i, nAA, pAA, nProcs, pSA, pG, pHiPo):
    """Returns the average number of remaining attacks in a turn recursively"""
    if i == nAA - 1:  # If no more additional attacks
        return 0.5 * pAA  # Add average HiPo super chance
    else:
        i += 1  # Increment attack counter
        # Calculate extra attack if get additional super and subsequent addditional attacks
        # Add damage if don't get any additional attacks
        tempAA0 = branchAA(i, nAA, pAA, nProcs, pSA, pG, pHiPo)
        tempAA1 = branchAA(i, nAA, pAA + pHiPo * (1 - pHiPo) ** nProcs, nProcs + 1, pSA, pG, pHiPo)
        return pSA[i] * (1 + tempAA1) + (1 - pSA[i]) * (pG[i] * tempAA1 + (1 - pG[i]) * tempAA0)


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


def getActiveAttack(
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


def getAvgAtk(
    AApSuper,
    saMult12,
    nCopies,
    sa12AtkStacks,
    sa12Atk,
    sa18Atk,
    stackedAtk,
    p1Atk,
    normal,
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
):
    """Returns the average ATK stat of a unit in a turn"""
    # Number of additional attacks from passive in each turn
    nAA = len(AApSuper)
    i = -1  # iteration counter
    nProcs = 1  # Initialise number of HiPo procs
    saMultiplier = SAMultiplier(saMult12, nCopies, sa12AtkStacks, sa12Atk)
    m12 = saMultiplier + sa12Atk + stackedAtk  # 12 ki multiplier after SA effect
    a12_0 = sa / m12  # Get 12 ki SA attack stat without multiplier
    baseAtk = 1 + p1Atk + stackedAtk
    if baseAtk <= 0:
        n_0 = 0
    else:
        # Get normal attack stat without SoT attack
        n_0 = normal / baseAtk
    pAA = HiPopAA  # Probability of doing an additional attack next
    pAASA = AApSuper  # Probability of doing a super on inbuilt additional
    pG = aaPGuarantee  # Probability of inbuilt additional
    counterAtk = (
        NUM_ATTACKS_DIRECTED[slot] * normalCounterMult + NUM_SUPER_ATTACKS_DIRECTED[slot] * pCounterSA * saCounterMult
    ) * normal
    avgAtk = pN * (
        normal
        + branchAtk(
            i,
            nAA,
            m12,
            baseAtk,
            pAA,
            nProcs,
            pAASA,
            pG,
            n_0,
            a12_0,
            sa12Atk,
            HiPopAA,
        )
    ) + pSA * (
        sa
        + branchAtk(
            i,
            nAA,
            m12 + sa12Atk,
            baseAtk + sa18Atk,
            pAA,
            nProcs,
            pAASA,
            pG,
            n_0,
            a12_0,
            sa12Atk,
            HiPopAA,
        )
    )
    if rarity == "LR":  # If  is a LR
        avgAtk += pUSA * (
            usa
            + branchAtk(
                i,
                nAA,
                m12 + sa18Atk,
                1 + p1Atk + stackedAtk + sa18Atk,
                pAA,
                nProcs,
                pAASA,
                pG,
                n_0,
                a12_0,
                sa12Atk,
                HiPopAA,
            )
        )
    avgAtk += counterAtk
    return avgAtk


def getDamageTaken(pEvade, guard, maxDamage, tdb, dmgRed, avgDef):
    return min(
        -(1 - (1 - DODGE_CANCEL_FACTOR) * pEvade)
        * (
            guard * GUARD_MOD * (maxDamage * (AVG_GUARD_FACTOR - TDB_INC * tdb) * (1 - dmgRed) - avgDef)
            + (1 - guard) * (maxDamage * (AVG_TYPE_ADVANATGE - TDB_INC * tdb) * (1 - dmgRed) - avgDef)
        )
        / (maxDamage * AVG_TYPE_ADVANATGE),
        0,
    )
