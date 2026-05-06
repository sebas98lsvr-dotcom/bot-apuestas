def calcular_stake(bank, prob, odd, fraccion=0.3):
    edge = (prob * odd) - 1

    if edge <= 0:
        return 0

    kelly = edge / (odd - 1)

    stake = bank * kelly * fraccion

    # límites de seguridad
    stake = max(stake, bank * 0.01)
    stake = min(stake, bank * 0.05)

    return round(stake, 2)