import math

# ====================================
# POISSON PMF
# ====================================

def poisson(k, lam):

    try:

        if lam < 0:
            return 0

        return (lam ** k * math.exp(-lam)) / math.factorial(k)

    except Exception:
        return 0


# ====================================
# LIMITAR PROBABILIDAD
# ====================================

def limitar_probabilidad(prob, min_prob=0.03, max_prob=0.82):

    try:

        if prob is None:
            return min_prob

        return max(min_prob, min(prob, max_prob))

    except Exception:
        return min_prob


# ====================================
# PROBABILIDAD OVER 2.5
# ====================================

def prob_over_25(lamL, lamV):

    try:

        lam = lamL + lamV

        p0 = poisson(0, lam)
        p1 = poisson(1, lam)
        p2 = poisson(2, lam)

        prob = 1 - (p0 + p1 + p2)

        # Over 2.5 puede ser alto, pero no dejamos que se dispare
        return limitar_probabilidad(
            prob,
            min_prob=0.03,
            max_prob=0.82
        )

    except Exception:
        return 0.03


# ====================================
# PROBABILIDAD BTTS CONSERVADORA
# ====================================

def prob_btts(lamL, lamV):

    try:

        p_home_scores = 1 - poisson(0, lamL)
        p_away_scores = 1 - poisson(0, lamV)

        prob = p_home_scores * p_away_scores

        min_lam = min(lamL, lamV)
        max_lam = max(lamL, lamV)

        # Penalización si un equipo tiene poco gol esperado
        if min_lam < 0.70:
            prob *= 0.55

        elif min_lam < 0.85:
            prob *= 0.68

        elif min_lam < 1.00:
            prob *= 0.82

        elif min_lam < 1.10:
            prob *= 0.92

        # Penalización si el partido está muy desbalanceado
        ratio = max_lam / max(min_lam, 0.01)

        if ratio > 3.00:
            prob *= 0.60

        elif ratio > 2.50:
            prob *= 0.72

        elif ratio > 2.10:
            prob *= 0.84

        elif ratio > 1.80:
            prob *= 0.92

        # BTTS no debería quedar inflado por encima de 0.78
        return limitar_probabilidad(
            prob,
            min_prob=0.03,
            max_prob=0.78
        )

    except Exception:
        return 0.03


# ====================================
# EXPECTED VALUE REALISTA
# ====================================

def calcular_value(prob, odd):

    try:

        odd = float(odd)
        prob = float(prob)

        if odd <= 1.01 or odd > 10:
            return -1

        if prob <= 0 or prob >= 1:
            return -1

        # value conservador
        value = ((prob * odd) - 1) / 4

        return round(value, 3)

    except Exception:
        return -1


# ====================================
# STAKE KELLY CONSERVADOR
# ====================================

def calcular_stake(bank, value, odd):

    try:

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

    except Exception:
        return 0