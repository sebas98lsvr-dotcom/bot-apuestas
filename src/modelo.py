import math

# Poisson PMF
def poisson(k, lam):
    return (lam**k * math.exp(-lam)) / math.factorial(k)

# Prob Over 2.5 (>=3 goles)
def prob_over_25(lamL, lamV):
    lam = lamL + lamV
    p0 = poisson(0, lam)
    p1 = poisson(1, lam)
    p2 = poisson(2, lam)
    return 1 - (p0 + p1 + p2)

# Prob BTTS (ambos anotan)
def prob_btts(lamL, lamV):
    p_home_0 = poisson(0, lamL)
    p_away_0 = poisson(0, lamV)
    return 1 - (p_home_0 + p_away_0 - (p_home_0 * p_away_0))

# Value simple
def calcular_value(prob, odd):
    return prob - (1 / odd)

# Stake (Kelly fraccional muy conservador)
def calcular_stake(bank, value, odd):
    if value <= 0:
        return 0
    kelly = (value / (odd - 1)) if odd > 1 else 0
    kelly = max(0, min(kelly, 0.05))  # cap 5%
    return bank * kelly