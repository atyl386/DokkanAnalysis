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
    pCrit,
    critMultiplier,
    atkModifer,
    p2AtkBuff,
    critBuff,
    atkPerAttackPerformed,
    critPerAttackPerformed,
    atkPerSuperPerformed,
    critPerSuperPerformed,
    saCrit,
    sa12Crit,
):
    """Returns the total remaining APT of a unit in a turn recursively"""
    p2AtkFactor = (p2Atk + p2AtkBuff) / p2Atk
    normal = mN * n_0 * p2AtkFactor * atkModifer
    additional12Ki = m12 * a12_0 * p2AtkFactor * atkModifer
    if i == nAA - 1:  # If no more additional attacks
        return 0.5 * pAA * (additional12Ki + normal)  # Add average hidden-potential attack damage
    else:
        i += 1  # Increment attack counter
        # Calculate extra attack if get additional super and subsequent addditional attacks
        # Add damage if don't get any additional attacks
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
            pCrit,
            critMultiplier,
            atkModifer,
            p2AtkBuff,
            critBuff,
            atkPerAttackPerformed,
            critPerAttackPerformed,
            atkPerSuperPerformed,
            critPerSuperPerformed,
            saCrit,
            sa12Crit,
        )
        pCrit1 = min(
            (pCrit - critBuff) / (1 - critBuff) * (1 - critPerAttackPerformed[0]) + critPerAttackPerformed[0], 1
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
            pCrit1,
            critMultiplier,
            (atkModifer - critMultiplier * pCrit) / (1 - pCrit) * (1 - pCrit1) + pCrit1 * critMultiplier,
            atkPerAttackPerformed[0],
            critPerAttackPerformed[0],
            atkPerAttackPerformed[1:],
            critPerAttackPerformed[1:],
            atkPerSuperPerformed,
            critPerSuperPerformed,
            saCrit,
            sa12Crit,
        )
        saCrit2 = saCrit + sa12Crit
        pCrit2 = min(
            (((pCrit - critBuff) / (1 - critBuff) - saCrit) / (1 - saCrit) * (1 - saCrit2) + saCrit2)
            * (1 - critPerSuperPerformed[0])
            + critPerSuperPerformed[0],
            1,
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
            pCrit2,
            critMultiplier,
            (atkModifer - critMultiplier * pCrit) / (1 - pCrit) * (1 - pCrit2) + pCrit2 * critMultiplier,
            atkPerSuperPerformed[0],
            critPerSuperPerformed[0],
            atkPerAttackPerformed,
            critPerAttackPerformed,
            atkPerSuperPerformed[1:],
            critPerSuperPerformed[1:],
            saCrit2,
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
        tempAA0 = branchAS(i, nAA, pAA, nProcs, pSA, pG, pHiPo)
        tempAA1 = branchAS(i, nAA, pAA + pHiPo * (1 - pHiPo) ** nProcs, nProcs + 1, pSA, pG, pHiPo)
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
    sa12Atk,
    sa18Atk,
    stackedAtk,
    p1Atk,
    p2Atk,
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
    canAttack,
    pCrit0,
    critMultiplier,
    preAtkModifier,
    atkPerAttackPerformed,
    atkPerSuperPerformed,
    critPerAttackPerformed,
    critPerSuperPerformed,
    sa12Crit,
    sa18Crit,
):
    """Returns the APT of a unit in a turn"""
    if canAttack:
        # Number of additional attacks from passive in each turn
        nAA = len(AApSuper)
        i = -1  # iteration counter
        nProcs = 1  # Initialise number of HiPo procs
        saMultiplier = SAMultiplier(saMult12, nCopies, sa12AtkStacks, sa12Atk)
        m12 = saMultiplier + sa12Atk + stackedAtk  # 12 ki multiplier after SA effect
        a12_0 = sa / m12  # Get 12 ki SA attack stat without multiplier
        baseAtk = 1 + p1Atk + stackedAtk
        n_0 = normal / baseAtk
        pAA = HiPopAA  # Probability of doing an additional attack next
        pAASA = AApSuper  # Probability of doing a super on inbuilt additional
        pG = aaPGuarantee  # Probability of inbuilt additional
        counterAtk = (
            NUM_ATTACKS_DIRECTED[slot - 1] * normalCounterMult
            + NUM_SUPER_ATTACKS_DIRECTED[slot - 1] * pCounterSA * saCounterMult
        ) * normal
        pCritN = min(pCrit0 + (1 - pCrit0) * critPerAttackPerformed[0], 1)
        pCritSA = min(pCrit0 + (1 - pCrit0) * (critPerSuperPerformed[0] + (1 - critPerSuperPerformed[0]) * sa12Crit), 1)
        pCritUSA = min(
            pCrit0 + (1 - pCrit0) * (critPerSuperPerformed[0] + (1 - critPerSuperPerformed[0]) * sa18Crit), 1
        )
        apt = pN * (
            normal * preAtkModifier
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
                sa12Atk,
                HiPopAA,
                pCritN,
                critMultiplier,
                (preAtkModifier - critMultiplier * pCrit0) / (1 - pCrit0) * (1 - pCritN) + pCritN * critMultiplier,
                atkPerAttackPerformed[0],
                critPerAttackPerformed[0],
                atkPerAttackPerformed[1:],
                critPerAttackPerformed[1:],
                atkPerSuperPerformed,
                critPerSuperPerformed,
                0,
                sa12Crit,
            )
        ) + pSA * (
            sa * preAtkModifier
            + branchAPT(
                i,
                nAA,
                m12 + sa12Atk,
                baseAtk + sa18Atk,
                p2Atk,
                pAA,
                nProcs,
                pAASA,
                pG,
                n_0,
                a12_0,
                sa12Atk,
                HiPopAA,
                pCritSA,
                critMultiplier,
                (preAtkModifier - critMultiplier * pCrit0) / (1 - pCrit0) * (1 - pCritSA) + pCritSA * critMultiplier,
                atkPerSuperPerformed[0],
                critPerSuperPerformed[0],
                atkPerAttackPerformed,
                critPerAttackPerformed,
                atkPerSuperPerformed[1:],
                critPerSuperPerformed[1:],
                sa12Crit,
                sa12Crit,
            )
        )
        if rarity == "LR":  # If  is a LR
            apt += pUSA * (
                usa * preAtkModifier
                + branchAPT(
                    i,
                    nAA,
                    m12 + sa18Atk,
                    1 + p1Atk + stackedAtk + sa18Atk,
                    p2Atk,
                    pAA,
                    nProcs,
                    pAASA,
                    pG,
                    n_0,
                    a12_0,
                    sa12Atk,
                    HiPopAA,
                    pCritUSA,
                    critMultiplier,
                    (preAtkModifier - critMultiplier * pCrit0) / (1 - pCrit0) * (1 - pCritSA)
                    + pCritUSA * critMultiplier,
                    atkPerSuperPerformed[0],
                    critPerSuperPerformed[0],
                    atkPerAttackPerformed,
                    critPerAttackPerformed,
                    atkPerSuperPerformed[1:],
                    critPerSuperPerformed[1:],
                    sa18Crit,
                    sa12Crit,
                )
            )
        apt += counterAtk * preAtkModifier
    else:
        apt = 0
    return apt


def getDamageTaken(pNullify, pEvade, guard, maxDamage, tdb, dmgRed, avgDef):
    return min(
        -(1 - (pNullify + (1 - pNullify) * (1 - DODGE_CANCEL_FACTOR) * pEvade))
        * (
            guard * GUARD_MOD * (maxDamage * (AVG_GUARD_FACTOR - TDB_INC * tdb) * (1 - dmgRed) - avgDef)
            + (1 - guard) * (maxDamage * (AVG_TYPE_ADVANATGE - TDB_INC * tdb) * (1 - dmgRed) - avgDef)
        )
        / (maxDamage * AVG_TYPE_ADVANATGE),
        0,
    )


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
