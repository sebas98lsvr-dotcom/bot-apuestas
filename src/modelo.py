import math

def poisson(k, lamb):
    return (lamb**k * math.exp(-lamb)) / math.factorial(k)

def calcular_lambda(goles, partidos):
    if partidos == 0:
        return 1.2
    return goles / partidos

def ajustar_localia(l1, l2):
    return l1 * 1.15, l2 * 0.95

def prob_over_25(l1, l2):
    prob = 0
    for i in range(6):
        for j in range(6):
            if i + j > 2:
                prob += poisson(i, l1) * poisson(j, l2)
    return prob

def prob_btts(l1, l2):
    prob = 0
    for i in range(1,6):
        for j in range(1,6):
            prob += poisson(i,l1)*poisson(j,l2)
    return prob

def calcular_value(prob, odd):
    return prob * odd - 1

def calcular_stake(bank, value, odd):
    stake = bank * (value / odd)
    return max(min(stake, bank*0.05), bank*0.01)