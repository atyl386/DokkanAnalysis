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


def getAttackDamageTaken(pEvade, guard, maxDamage, tdb, dmgRed, avgDef, enemyCritChance):
    return min(
        -(1 - pEvade)
        * min(
            (
                guard
                * GUARD_MOD
                * (
                    maxDamage
                    * (AEAAT_MULTIPLIER * enemyCritChance + (1 - enemyCritChance)
                    * (AVG_GUARD_FACTOR - TDB_INC * tdb))
                    * (1 - dmgRed)
                    - avgDef
                )
                + (1 - guard)
                * (
                    enemyCritChance * (maxDamage * (AEAAT_MULTIPLIER - TDB_INC * tdb) * (1 - dmgRed) - avgDef)
                    + (1 - enemyCritChance) * (maxDamage * (AVG_TYPE_ADVANATGE - TDB_INC * tdb) * (1 - dmgRed) - avgDef)
                )
            )
            / AVG_HEALTH,
            1,
        ),
        0,
    )

def dmgThreshold(dmg):
    if dmg < AVG_ENEMY_DMG_THRESHOLD:
        return (1 - ENEMY_DMG_THRESHOLD_CHANCE) * dmg
    else:
        return dmg


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


def processDefBuffStatuses(defBuffStatuses, lastAttackFactor=1):
    defBuffNextStatuses = dict.fromkeys(DEF_STATUS_EVENTS)
    defBuffStatuses0 = dict.fromkeys(defBuffStatuses.keys())
    for event in DEF_STATUS_EVENTS:
        defBuffNextStatuses[event] = copy.deepcopy(defBuffStatuses)
        for key in defBuffStatuses.keys():
            if key[1] in DEF_STATUS_IMPLICATIONS[event]:
                defBuffStatuses0[key] = defBuffNextStatuses[event][key][0]
                if lastAttackFactor == 1:
                    defBuffNextStatuses[event][key] = defBuffNextStatuses[event][key][1:]
                defBuffNextStatuses[event][key][0] *= lastAttackFactor
    return defBuffNextStatuses, defBuffStatuses0
