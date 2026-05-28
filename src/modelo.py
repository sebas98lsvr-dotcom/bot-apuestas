import math

# ====================================
# MODELO.PY
# Versión: v7_prioridad_estabilidad
# Fecha: 2026-05-27
#
# Objetivo:
# - Priorizar Over 1.5, BTTS y Under 2.5.
# - Convertir Over 2.5 en mercado premium.
# - Reducir picks falsas de Over 2.5.
# - Mantener compatibilidad total con main.py.
# ====================================


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

        return limitar_probabilidad(
            prob,
            min_prob=0.03,
            max_prob=0.82
        )

    except Exception:
        return 0.03


# ====================================
# PROBABILIDAD UNDER 2.5
# ====================================

def prob_under_25(lamL, lamV):

    try:

        lam = lamL + lamV

        p0 = poisson(0, lam)
        p1 = poisson(1, lam)
        p2 = poisson(2, lam)

        prob = p0 + p1 + p2

        return limitar_probabilidad(
            prob,
            min_prob=0.03,
            max_prob=0.82
        )

    except Exception:
        return 0.03


# ====================================
# PROBABILIDAD OVER 1.5
# ====================================

def prob_over_15(lamL, lamV):

    try:

        lam = lamL + lamV

        p0 = poisson(0, lam)
        p1 = poisson(1, lam)

        prob = 1 - (p0 + p1)

        return limitar_probabilidad(
            prob,
            min_prob=0.03,
            max_prob=0.90
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

        if min_lam < 0.70:
            prob *= 0.55

        elif min_lam < 0.85:
            prob *= 0.68

        elif min_lam < 1.00:
            prob *= 0.82

        elif min_lam < 1.10:
            prob *= 0.92

        ratio = max_lam / max(min_lam, 0.01)

        if ratio > 3.00:
            prob *= 0.60

        elif ratio > 2.50:
            prob *= 0.72

        elif ratio > 2.10:
            prob *= 0.84

        elif ratio > 1.80:
            prob *= 0.92

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

        value = ((prob * odd) - 1) / 4

        return round(value, 3)

    except Exception:
        return -1


# ====================================
# CLASIFICAR NIVEL DE PICK
# ====================================

def clasificar_nivel_pick(
    mercado,
    score,
    prob,
    value,
    odd,
    total_lambda=None,
    nivel_liga=None
):

    try:
        score = float(score)
        prob = float(prob)
        value = float(value)
        odd = float(odd)

        if total_lambda is not None:
            total_lambda = float(total_lambda)

    except Exception:
        return "DESCARTADA"

    nivel = "DESCARTADA"

    # ==========================
    # OVER 1.5
    # ==========================

    if mercado == "Over 1.5":

        if (
            score >= 12.5
            and prob >= 0.82
            and value >= 0.015
            and total_lambda is not None
            and total_lambda >= 3.00
            and 1.28 <= odd <= 1.78
        ):
            nivel = "CONSERVADORA"

        if (
            score >= 12.8
            and prob >= 0.79
            and value >= 0.035
            and total_lambda is not None
            and total_lambda >= 2.70
            and 1.35 <= odd <= 1.78
        ):
            nivel = "NORMAL"

        if (
            score >= 15.5
            and prob >= 0.83
            and value >= 0.050
            and total_lambda is not None
            and total_lambda >= 3.00
            and 1.35 <= odd <= 1.70
        ):
            nivel = "FUERTE"

        if (
            score >= 18.0
            and prob >= 0.86
            and value >= 0.070
            and total_lambda is not None
            and total_lambda >= 3.25
            and 1.35 <= odd <= 1.65
        ):
            nivel = "ELITE"

    # ==========================
    # OVER 2.5 PREMIUM
    # ==========================

    elif mercado == "Over 2.5":

        if (
            score >= 15.5
            and prob >= 0.67
            and value >= 0.045
            and total_lambda is not None
            and total_lambda >= 3.05
            and 1.65 <= odd <= 2.40
        ):
            nivel = "NORMAL"

        if (
            score >= 17
            and prob >= 0.70
            and value >= 0.060
            and total_lambda is not None
            and total_lambda >= 3.25
            and 1.65 <= odd <= 2.20
        ):
            nivel = "FUERTE"

        if (
            score >= 19
            and prob >= 0.74
            and value >= 0.080
            and total_lambda is not None
            and total_lambda >= 3.50
            and 1.65 <= odd <= 2.00
        ):
            nivel = "ELITE"

        if nivel_liga == "MEDIA":

            if odd >= 2.00 and nivel == "ELITE":
                nivel = "FUERTE"

            if odd >= 2.20 and nivel == "FUERTE":
                nivel = "NORMAL"

    # ==========================
    # UNDER 2.5
    # ==========================

    elif mercado == "Under 2.5":

        if total_lambda is None:
            return "DESCARTADA"

        if (
            score >= 12.8
            and prob >= 0.58
            and value >= 0.035
            and total_lambda <= 2.35
            and 1.55 <= odd <= 2.35
        ):
            nivel = "NORMAL"

        if (
            score >= 15.0
            and prob >= 0.61
            and value >= 0.045
            and total_lambda <= 2.25
            and 1.60 <= odd <= 2.25
        ):
            nivel = "FUERTE"

        if (
            score >= 17.0
            and prob >= 0.64
            and value >= 0.060
            and total_lambda <= 2.10
            and 1.65 <= odd <= 2.10
        ):
            nivel = "ELITE"

        if nivel_liga == "MEDIA":

            if odd >= 2.05 and nivel == "ELITE":
                nivel = "FUERTE"

            if odd >= 2.20 and nivel == "FUERTE":
                nivel = "NORMAL"

        if total_lambda > 2.45:
            nivel = "DESCARTADA"

    # ==========================
    # BTTS
    # ==========================

    elif mercado == "BTTS":

        if (
            score >= 13.8
            and prob >= 0.60
            and value >= 0.040
            and total_lambda is not None
            and total_lambda >= 2.50
            and 1.65 <= odd <= 2.35
        ):
            nivel = "NORMAL"

        if (
            score >= 16.5
            and prob >= 0.64
            and value >= 0.060
            and total_lambda is not None
            and total_lambda >= 2.80
            and 1.70 <= odd <= 2.20
        ):
            nivel = "FUERTE"

        if (
            score >= 18.5
            and prob >= 0.68
            and value >= 0.080
            and total_lambda is not None
            and total_lambda >= 3.00
            and 1.75 <= odd <= 2.05
        ):
            nivel = "ELITE"

        if nivel_liga == "MEDIA":

            if odd >= 2.15 and nivel == "ELITE":
                nivel = "FUERTE"

            if odd >= 2.25 and nivel == "FUERTE":
                nivel = "NORMAL"

    return nivel


# ====================================
# STAKE POR NIVEL
# ====================================

def stake_por_nivel(nivel):

    if nivel == "ELITE":
        return 25.0

    if nivel == "FUERTE":
        return 15.0

    if nivel == "NORMAL":
        return 10.0

    if nivel == "CONSERVADORA":
        return 5.0

    return 0.0


# ====================================
# STAKE CONTROLADO POR NIVEL
# ====================================

def calcular_stake_por_nivel(
    mercado,
    score,
    prob,
    value,
    odd,
    total_lambda=None,
    nivel_liga=None
):

    nivel = clasificar_nivel_pick(
        mercado=mercado,
        score=score,
        prob=prob,
        value=value,
        odd=odd,
        total_lambda=total_lambda,
        nivel_liga=nivel_liga
    )

    stake = stake_por_nivel(nivel)

    return nivel, stake


# ====================================
# STAKE KELLY CONSERVADOR
# ====================================

def calcular_stake(bank, value, odd):

    try:

        bank = float(bank)
        value = float(value)
        odd = float(odd)

        if value <= 0:
            return 0

        if odd <= 1:
            return 0

        kelly = value / (odd - 1)

        kelly = max(0.003, min(kelly, 0.015))

        stake = bank * kelly

        stake = max(3, min(stake, bank * 0.015))

        return round(stake, 2)

    except Exception:
        return 0