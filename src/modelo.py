import math

# ====================================
# POISSON PMF
# ====================================

def poisson(k, lam):

    try:
        return (lam ** k * math.exp(-lam)) / math.factorial(k)

    except:
        return 0


# ====================================
# LIMITAR PROBABILIDAD
# ====================================

def limitar_probabilidad(prob):

    return max(0.05, min(prob, 0.85))


# ====================================
# PROBABILIDAD OVER 2.5
# ====================================

def prob_over_25(lamL, lamV):

    lam = lamL + lamV

    p0 = poisson(0, lam)
    p1 = poisson(1, lam)
    p2 = poisson(2, lam)

    prob = 1 - (p0 + p1 + p2)

    return limitar_probabilidad(prob)


# ====================================
# PROBABILIDAD BTTS
# ====================================

def prob_btts(lamL, lamV):

    p_home_0 = poisson(0, lamL)
    p_away_0 = poisson(0, lamV)

    prob = 1 - (
        p_home_0 +
        p_away_0 -
        (p_home_0 * p_away_0)
    )

    return limitar_probabilidad(prob)


# ====================================
# EXPECTED VALUE REALISTA
# ====================================

def calcular_value(prob, odd):

    if odd <= 1.01 or odd > 10:
        return -1

    # value más conservador
    value = ((prob * odd) - 1) / 4

    return round(value, 3)


# ====================================
# STAKE KELLY CONSERVADOR
# ====================================

def calcular_stake(bank, value, odd):

    if value <= 0:
        return 0

    if odd <= 1:
        return 0

    kelly = value / (odd - 1)

    # máximo 3% del bank
    kelly = max(0.005, min(kelly, 0.03))

    stake = bank * kelly

    # stake mínimo/máximo
    stake = max(5, min(stake, bank * 0.03))

    return round(stake, 2)