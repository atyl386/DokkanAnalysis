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


def KiModifier(base, ki):
    """Returns the ki modifier for a unit (only used for normals and Ultras)"""
    if ki <= 12:
        return 1
    else:
        return np.linspace(base, 2, 13)[ki - 12]


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


def branchAttacksEvaded(
    iA,
    iB,
    nAA,
    nAB,
    evasion,
    pEvadeB,
    pDisableEvasionCancel,
    evasionPerAttackReceived,
    evasionPerAttackEvaded,
):
    """Returns the average remaining attacks evaded by a unit in a turn recursively"""
    pE = (1 - DODGE_CANCEL_FACTOR * (1 - pDisableEvasionCancel)) * evasion.prob
    pReceiveAttack = 1 - pE
    evasionPostEvade = copy.copy(evasion)
    evasionPostHit = copy.copy(evasion)
    evasionPostEvade.updateChance("Start of Turn", evasionPerAttackEvaded[0])
    evasionPostHit.updateChance("Start of Turn", evasionPerAttackReceived[0])
    # If last attack in sequence
    if iA >= nAA - 1 and iB == -1:
        evasionPostEvadeB = copy.copy(evasionPostEvade)
        evasionPostEvadeB.updateChance("Start of Turn", pEvadeB)
        evasionPostHitB = copy.copy(evasionPostHit)
        evasionPostHitB.updateChance("Start of Turn", pEvadeB)
        # mulitply by extra factor if only part is expected. 0 =< nA - i < 1 )
        return pE * (
            nAA
            - iA
            + branchAttacksEvaded(
                iA,
                0,
                nAA,
                nAB,
                evasionPostEvadeB,
                pEvadeB,
                pDisableEvasionCancel,
                evasionPerAttackReceived,
                evasionPerAttackEvaded[1:],
            )
        ) + pReceiveAttack * branchAttacksEvaded(
            iA,
            0,
            nAA,
            nAB,
            evasionPostHitB,
            pEvadeB,
            pDisableEvasionCancel,
            evasionPerAttackReceived[1:],
            evasionPerAttackEvaded,
        )
    elif iA < nAA - 1 or iB < nAB - 1:
        if iA < nAA - 1:
            iA += 1
        else:
            iB += 1
        return pE * (
            1
            + branchAttacksEvaded(
                iA,
                iB,
                nAA,
                nAB,
                evasionPostEvade,
                pDisableEvasionCancel,
                evasionPerAttackReceived,
                evasionPerAttackEvaded[1:],
            )
        ) + pReceiveAttack * branchAttacksEvaded(
            iA,
            iB,
            nAA,
            nAB,
            evasionPostHit,
            pDisableEvasionCancel,
            evasionPerAttackReceived[1:],
            evasionPerAttackEvaded,
        )
    else:
        return pE * (nAB - iB)


def branchDamageTaken(
    iA,
    iB,
    nAA,
    nAB,
    p2Def,
    p2DefB,
    p2DefSuper,
    evasion,
    pEvadeB,
    pEvadeExtra,
    pGuard,
    dmgRed,
    dmgRedB,
    pNullify,
    defence,
    postSuperDefMult,
    postSuperDefMultB,
    pDisableEvasionCancel,
    defPerAttackReceived,
    defPerAttackEvaded,
    defPerAttackGuarded,
    defPerAttackReceivedOrEvaded,
    dmgRedPerAttackReceived,
    dmgRedPerAttackReceivedOrEvaded,
    evasionPerAttackReceived,
    evasionPerAttackEvaded,
    evasionPerAttackReceivedOrEvaded,
    guardPerAttackReceived,
    guardPerAttackReceivedOrEvaded,
    maxDamage,
    enemyCritChance,
    tdb,
):
    """Returns the remaining damage taken by a unit in a turn recursively"""
    # Get damage taken by the attack pre super
    evasion.updateChance("Start of Turn", pEvadeExtra, "")
    pE_N = (1 - DODGE_CANCEL_FACTOR * (1 - pDisableEvasionCancel)) * evasion.prob
    pE = pE_N * (1 - pNullify) + pNullify
    pG = (1 - pE) * pGuard
    pR = 1 - pE - pG
    attackDamageTaken = getAttackDamageTaken(pE, pGuard, maxDamage, tdb, dmgRed, defence, enemyCritChance)
    # If last attack in sequence pre super
    if iA >= nAA - 1 and iB == -1:
        evasionPostEvadeB = copy.deepcopy(evasion)
        evasionPostHitB = copy.deepcopy(evasion)
        evasionPostEvadeB.updateChance(
            "Start of Turn",
            (evasionPerAttackEvaded[0] + evasionPerAttackReceivedOrEvaded[0]) * (nAA - iA) + pEvadeB,
            "",
        )
        evasionPostHitB.updateChance(
            "Start of Turn",
            (evasionPerAttackReceived[0] + evasionPerAttackReceivedOrEvaded[0]) * (nAA - iA) + pEvadeB,
            "",
        )
        # mulitply by extra factor if only part is expected. 0 =< nAA - iA < 1 )
        defPerAttackEvadedB = copy.copy(defPerAttackEvaded)
        defPerAttackGuardedB = copy.copy(defPerAttackGuarded)
        defPerAttackReceivedB = copy.copy(defPerAttackReceived)
        defPerAttackReceivedOrEvadedB = copy.copy(defPerAttackReceivedOrEvaded)
        dmgRedPerAttackReceivedB = copy.copy(dmgRedPerAttackReceived)
        dmgRedPerAttackReceivedOrEvadedB = copy.copy(dmgRedPerAttackReceivedOrEvaded)
        evasionPerAttackEvadedB = copy.copy(evasionPerAttackEvaded)
        evasionPerAttackReceivedB = copy.copy(evasionPerAttackReceived)
        evasionPerAttackReceivedOrEvadedB = copy.copy(evasionPerAttackReceived)
        guardPerAttackReceivedB = copy.copy(guardPerAttackReceived)
        guardPerAttackReceivedOrEvadedB = copy.copy(guardPerAttackReceivedOrEvaded)
        defPerAttackEvadedB[0] *= 1 - (nAA - iA)
        defPerAttackGuardedB[0] *= 1 - (nAA - iA)
        defPerAttackReceivedB[0] *= 1 - (nAA - iA)
        defPerAttackReceivedOrEvadedB[0] *= 1 - (nAA - iA)
        dmgRedPerAttackReceivedB[0] *= 1 - (nAA - iA)
        dmgRedPerAttackReceivedB[0] *= 1 - (nAA - iA)
        evasionPerAttackEvadedB[0] *= 1 - (nAA - iA)
        evasionPerAttackReceivedB[0] *= 1 - (nAA - iA)
        evasionPerAttackReceivedOrEvadedB[0] *= 1 - (nAA - iA)
        guardPerAttackReceivedB[0] *= 1 - (nAA - iA)
        guardPerAttackReceivedB[0] *= 1 - (nAA - iA)
        return (
            attackDamageTaken * (nAA - iA)
            + pE
            * branchDamageTaken(
                iA,
                0,
                nAA,
                nAB,
                p2Def + p2DefB + p2DefSuper + (defPerAttackEvaded[0] + defPerAttackReceivedOrEvaded[0]) * (nAA - iA),
                p2DefB,
                p2DefSuper,
                evasionPostEvadeB,
                pEvadeB,
                0,
                pGuard + guardPerAttackReceivedOrEvaded[0] * (nAA - iA),
                dmgRed + dmgRedB + dmgRedPerAttackReceivedOrEvaded[0] * (nAA - iA),
                dmgRedB,
                pNullify,
                defence
                * (1 + p2Def + p2DefB + p2DefSuper + (defPerAttackEvaded[0] + defPerAttackReceivedOrEvaded[0]) * (nAA - iA))
                / (1 + p2Def)
                * (1 + postSuperDefMultB)
                / (1 + postSuperDefMult),
                postSuperDefMultB,
                postSuperDefMultB,
                pDisableEvasionCancel,
                defPerAttackReceived,
                defPerAttackEvadedB,
                defPerAttackGuarded,
                defPerAttackReceivedOrEvadedB,
                dmgRedPerAttackReceived,
                dmgRedPerAttackReceivedOrEvadedB,
                evasionPerAttackReceived,
                evasionPerAttackEvadedB,
                evasionPerAttackReceivedOrEvadedB,
                guardPerAttackReceived,
                guardPerAttackReceivedOrEvadedB,
                maxDamage,
                enemyCritChance,
                tdb,
            )
            + pG
            * branchDamageTaken(
                iA,
                0,
                nAA,
                nAB,
                p2Def
                + p2DefB
                + p2DefSuper
                + (defPerAttackGuarded[0] + defPerAttackReceived[0] + defPerAttackReceivedOrEvaded[0]) * (nAA - iA),
                p2DefB,
                p2DefSuper,
                evasionPostHitB,
                pEvadeB,
                0,
                pGuard + (guardPerAttackReceived[0] + guardPerAttackReceivedOrEvaded[0]) * (nAA - iA),
                dmgRed + dmgRedB + (dmgRedPerAttackReceived[0] + dmgRedPerAttackReceivedOrEvaded[0]) * (nAA - iA),
                dmgRedB,
                pNullify,
                defence
                * (
                    1
                    + p2Def
                    + p2DefB
                    + p2DefSuper
                    + (defPerAttackGuarded[0] + defPerAttackReceived[0] + defPerAttackReceivedOrEvaded[0]) * (nAA - iA)
                )
                / (1 + p2Def)
                * (1 + postSuperDefMultB)
                / (1 + postSuperDefMult),
                postSuperDefMultB,
                postSuperDefMultB,
                pDisableEvasionCancel,
                defPerAttackReceivedB,
                defPerAttackEvaded,
                defPerAttackGuardedB,
                defPerAttackReceivedOrEvadedB,
                dmgRedPerAttackReceivedB,
                dmgRedPerAttackReceivedOrEvadedB,
                evasionPerAttackReceivedB,
                evasionPerAttackEvaded,
                evasionPerAttackReceivedOrEvadedB,
                guardPerAttackReceivedB,
                guardPerAttackReceivedOrEvadedB,
                maxDamage,
                enemyCritChance,
                tdb,
            )
            + pR
            * branchDamageTaken(
                iA,
                0,
                nAA,
                nAB,
                p2Def + p2DefB + p2DefSuper + (defPerAttackReceived[0] + defPerAttackReceivedOrEvaded[0]) * (nAA - iA),
                p2DefB,
                p2DefSuper,
                evasionPostHitB,
                pEvadeB,
                0,
                pGuard + (guardPerAttackReceived[0] + guardPerAttackReceivedOrEvaded[0]) * (nAA - iA),
                dmgRed + dmgRedB + (dmgRedPerAttackReceived[0] + dmgRedPerAttackReceivedOrEvaded[0]) * (nAA - iA),
                dmgRedB,
                pNullify,
                defence
                * (1 + p2Def + p2DefB + p2DefSuper + (defPerAttackReceived[0] + defPerAttackReceivedOrEvaded[0]) * (nAA - iA))
                / (1 + p2Def)
                * (1 + postSuperDefMultB)
                / (1 + postSuperDefMult),
                postSuperDefMultB,
                postSuperDefMultB,
                pDisableEvasionCancel,
                defPerAttackReceivedB,
                defPerAttackEvaded,
                defPerAttackGuarded,
                defPerAttackReceivedOrEvadedB,
                dmgRedPerAttackReceivedB,
                dmgRedPerAttackReceivedOrEvadedB,
                evasionPerAttackReceivedB,
                evasionPerAttackEvaded,
                evasionPerAttackReceivedOrEvadedB,
                guardPerAttackReceivedB,
                guardPerAttackReceivedOrEvadedB,
                maxDamage,
                enemyCritChance,
                tdb,
            )
        )
    elif iA < nAA - 1 or iB < nAB - 1:
        evasionPostEvade = copy.deepcopy(evasion)
        evasionPostHit = copy.deepcopy(evasion)
        evasionPostEvade.updateChance(
            "Start of Turn", evasionPerAttackEvaded[0] + evasionPerAttackReceivedOrEvaded[0], ""
        )
        evasionPostHit.updateChance(
            "Start of Turn", evasionPerAttackReceived[0] + evasionPerAttackReceivedOrEvaded[0], ""
        )
        if iA < nAA - 1:
            iA += 1
        else:
            iB += 1
        return (
            attackDamageTaken
            + pE
            * branchDamageTaken(
                iA,
                iB,
                nAA,
                nAB,
                p2Def + p2DefSuper + defPerAttackEvaded[0] + defPerAttackReceivedOrEvaded[0],
                p2DefB,
                p2DefSuper,
                evasionPostEvade,
                pEvadeB,
                0,
                pGuard + guardPerAttackReceivedOrEvaded[0],
                dmgRed + dmgRedPerAttackReceivedOrEvaded[0],
                dmgRedB,
                pNullify,
                defence * (1 + p2Def + p2DefSuper + defPerAttackEvaded[0] + defPerAttackReceivedOrEvaded[0]) / (1 + p2Def),
                postSuperDefMult,
                postSuperDefMultB,
                pDisableEvasionCancel,
                defPerAttackReceived,
                defPerAttackEvaded[1:],
                defPerAttackGuarded,
                defPerAttackReceivedOrEvaded[1:],
                dmgRedPerAttackReceived,
                dmgRedPerAttackReceivedOrEvaded[1:],
                evasionPerAttackReceived,
                evasionPerAttackEvaded[1:],
                evasionPerAttackReceivedOrEvaded[1:],
                guardPerAttackReceived,
                guardPerAttackReceivedOrEvaded[1:],
                maxDamage,
                enemyCritChance,
                tdb,
            )
            + pG
            * branchDamageTaken(
                iA,
                iB,
                nAA,
                nAB,
                p2Def + p2DefSuper + defPerAttackGuarded[0] + defPerAttackReceived[0] + defPerAttackReceivedOrEvaded[0],
                p2DefB,
                p2DefSuper,
                evasionPostHit,
                pEvadeB,
                0,
                pGuard + guardPerAttackReceived[0] + guardPerAttackReceivedOrEvaded[0],
                dmgRed + dmgRedPerAttackReceived[0] + dmgRedPerAttackReceivedOrEvaded[0],
                dmgRedB,
                pNullify,
                defence
                * (1 + p2Def + p2DefSuper + defPerAttackGuarded[0] + defPerAttackReceived[0] + defPerAttackReceivedOrEvaded[0])
                / (1 + p2Def),
                postSuperDefMult,
                postSuperDefMultB,
                pDisableEvasionCancel,
                defPerAttackReceived[1:],
                defPerAttackEvaded,
                defPerAttackGuarded[1:],
                defPerAttackReceivedOrEvaded[1:],
                dmgRedPerAttackReceived[1:],
                dmgRedPerAttackReceivedOrEvaded[1:],
                evasionPerAttackReceived[1:],
                evasionPerAttackEvaded,
                evasionPerAttackReceivedOrEvaded[1:],
                guardPerAttackReceived[1:],
                guardPerAttackReceivedOrEvaded[1:],
                maxDamage,
                enemyCritChance,
                tdb,
            )
            + pR
            * branchDamageTaken(
                iA,
                iB,
                nAA,
                nAB,
                p2Def + p2DefSuper + defPerAttackReceived[0] + defPerAttackReceivedOrEvaded[0],
                p2DefB,
                p2DefSuper,
                evasionPostHit,
                pEvadeB,
                0,
                pGuard + guardPerAttackReceived[0] + guardPerAttackReceivedOrEvaded[0],
                dmgRed + dmgRedPerAttackReceived[0] + dmgRedPerAttackReceivedOrEvaded[0],
                dmgRedB,
                pNullify,
                defence * (1 + p2Def + p2DefSuper + defPerAttackReceived[0] + defPerAttackReceivedOrEvaded[0]) / (1 + p2Def),
                postSuperDefMult,
                postSuperDefMultB,
                pDisableEvasionCancel,
                defPerAttackReceived[1:],
                defPerAttackEvaded,
                defPerAttackGuarded,
                defPerAttackReceivedOrEvaded[1:],
                dmgRedPerAttackReceived[1:],
                dmgRedPerAttackReceivedOrEvaded[1:],
                evasionPerAttackReceived[1:],
                evasionPerAttackEvaded,
                evasionPerAttackReceivedOrEvaded[1:],
                guardPerAttackReceived[1:],
                guardPerAttackReceivedOrEvaded[1:],
                maxDamage,
                enemyCritChance,
                tdb,
            )
        )
    else:
        # mulitply by extra factor if only part is expected. 0 =< nAB - iB < 1 )
        return attackDamageTaken * (nAB - iB)


def getAttackDamageTaken(pEvade, guard, maxDamage, tdb, dmgRed, avgDef, enemyCritChance):
    return min(
        -(1 - pEvade)
        * min(
            (
                guard * GUARD_MOD * (maxDamage * (AEAAT_MULTIPLIER * enemyCritChance + (1 - enemyCritChance)) * (AVG_GUARD_FACTOR - TDB_INC * tdb) * (1 - dmgRed) - avgDef)
                + (1 - guard)
                * (
                    enemyCritChance * (maxDamage * (AEAAT_MULTIPLIER - TDB_INC * tdb) * (1 - dmgRed) - avgDef)
                    + (1 - enemyCritChance) * (maxDamage * (AVG_TYPE_ADVANATGE - TDB_INC * tdb) * (1 - dmgRed) - avgDef)
                )
            ) / AVG_HEALTH,
            1),
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
