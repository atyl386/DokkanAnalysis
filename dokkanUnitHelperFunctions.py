import click as clc
from scipy.stats import poisson
from dokkanUnitConstants import *

#################################################### Helper functions #######################################################################


def maxHealthCDF(maxHealth):
    """Returns the probability that health is less than the input"""
    return 4 / 3 * maxHealth**3 - maxHealth**2 + 2 / 3 * maxHealth


def ZTP_CDF(x, Lambda):
    """Returns the cdf(x) of a zero-truncated poisson distribution(lambda)"""
    return (poisson.cdf(x, Lambda) - poisson.cdf(0, Lambda)) / (1 - poisson.cdf(0, Lambda))


def SAMultiplier(multiplier, eza, rarity, nCopies, nStacks, saAtk):
    """Returns the super-attack multiplier of a form"""
    baseMultiplier = superAttackConversion[multiplier][superAttackLevelConversion[rarity][eza]]
    stackingPenalty = 0
    if nStacks > 1:  # If stack attack
        stackingPenalty = saAtk
    return baseMultiplier + SA_BOOST_INC * HIPO_SA_BOOST[nCopies - 1] - stackingPenalty


def KiModifier(base, ki):
    """Returns the ki modifier for a unit"""
    if ki <= 12:
        return 1
    else:
        return (np.linspace(base, 2, 12))[ki - 13]


def branchAtk(i, nAA, m12, mN, pAA, nProcs, pSA, pG, N_0, a12_0, saMult, pHiPo):
    """Returns the total remaining ATK of a unit in a turn recursively"""
    normal = mN * N_0
    additional12Ki = m12 * a12_0
    if i == nAA - 1:  # If no more additional attacks
        return 0.5 * pAA * (additional12Ki + normal)  # Add average hidden-potential attack damage
    else:
        i += 1  # Increment attack counter
        # Calculate extra attack if get additional super and subsequent addditional attacks
        # Add damage if don't get any additional attacks
        tempAtk0 = branchAtk(i, nAA, m12, mN, pAA, nProcs, pSA, pG, N_0, a12_0, saMult, pHiPo)
        tempAtk1 = branchAtk(
            i,
            nAA,
            m12,
            mN,
            pAA + pHiPo * (1 - pHiPo) ** nProcs,
            nProcs + 1,
            pSA,
            pG,
            N_0,
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
            N_0,
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


def getNormal(kiMod12, ki, att, p1Atk, stackedAtk, linkAtkSoT, p2Atk, p3Atk):
    """Returns the ATK stat of a normal"""
    kiMultiplier = KiModifier(kiMod12, ki)
    return (
        att
        * (1 + LEADER_SKILL_STATS)
        * (1 + p1Atk + stackedAtk)
        * (1 + linkAtkSoT)
        * (1 + p2Atk)
        * (1 + p3Atk)
        * kiMultiplier
    )


def getSA(
    kiMod12,
    att,
    p1Atk,
    stackedAtk,
    linkAtkSoT,
    p2Atk,
    p3Atk,
    saMult12,
    eza,
    exclusivity,
    nCopies,
    sa12AtkStacks,
    sa12Atk,
):
    """Returns the ATK stat of a super-attack"""
    kiMultiplier = kiMod12
    SAmultiplier = SAMultiplier(saMult12, eza, exclusivity, nCopies, sa12AtkStacks, sa12Atk)
    return (
        att
        * (1 + LEADER_SKILL_STATS)
        * (1 + p1Atk)
        * (1 + linkAtkSoT)
        * (1 + p2Atk)
        * (1 + p3Atk)
        * kiMultiplier
        * (SAmultiplier + sa12Atk + stackedAtk)
    )


def getUSA(
    kiMod12,
    ki,
    att,
    p1Atk,
    stackedAtk,
    linkAtkSoT,
    p2Atk,
    p3Atk,
    saMult18,
    eza,
    exclusivity,
    nCopies,
    sa18AtkStacks,
    sa18Atk,
):
    """Returns the ATK stat of an ultra-super-attack"""
    kiMultiplier = KiModifier(kiMod12, max(ki, 18))
    SAmultiplier = SAMultiplier(saMult18, eza, exclusivity, nCopies, sa18AtkStacks, sa18Atk)
    return (
        att
        * (1 + LEADER_SKILL_STATS)
        * (1 + p1Atk)
        * (1 + linkAtkSoT)
        * (1 + p2Atk)
        * (1 + p3Atk)
        * kiMultiplier
        * (SAmultiplier + sa18Atk + stackedAtk)
    )


def getActiveAttack(
    kiMod12,
    ki,
    att,
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
    SAmultiplier = saMultActive + SA_BOOST_INC * HIPO_SA_BOOST[nCopies - 1]
    return (
        att
        * (1 + LEADER_SKILL_STATS)
        * (1 + p1Atk)
        * (1 + linkAtkSoT)
        * (1 + p2Atk)
        * (1 + p3Atk)
        * kiMultiplier
        * (1 + stackedAtk)
        * SAmultiplier
    )


def getAvgAtk(
    AApSuper,
    saMult12,
    eza,
    exclusivity,
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
    SAmultiplier = SAMultiplier(saMult12, eza, exclusivity, nCopies, sa12AtkStacks, sa12Atk)
    m12 = SAmultiplier + sa12Atk + stackedAtk  # 12 ki multiplier after SA effect
    a12_0 = sa / m12  # Get 12 ki SA attack stat without multiplier
    if 1 + p1Atk + stackedAtk <= 0:
        N_0 = 0
    else:
        # Get normal attack stat without SoT attack
        N_0 = normal / (1 + p1Atk + stackedAtk)
    pAA = HiPopAA  # Probability of doing an additional attack next
    pSA = AApSuper  # Probability of doing a super on inbuilt additional
    pG = aaPGuarantee  # Probability of inbuilt additional
    counterAtk = (
        NUM_ATTACKS_RECEIVED[slot] * normalCounterMult + NUM_SUPER_ATTACKS[slot] * pCounterSA * saCounterMult
    ) * normal
    avgAtk = pN * (
        normal
        + branchAtk(
            i,
            nAA,
            m12,
            p1Atk + stackedAtk,
            pAA,
            nProcs,
            pSA,
            pG,
            N_0,
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
            p1Atk + stackedAtk + sa18Atk,
            pAA,
            nProcs,
            pSA,
            pG,
            N_0,
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
                p1Atk + stackedAtk + sa18Atk,
                pAA,
                nProcs,
                pSA,
                pG,
                N_0,
                a12_0,
                sa12Atk,
                HiPopAA,
            )
        )
    avgAtk += counterAtk
    return avgAtk
