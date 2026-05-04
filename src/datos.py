from api_datos import obtener_ultimos_partidos


def calcular_stats(team_id):
    partidos = obtener_ultimos_partidos(team_id)

    if not partidos:
        return None

    goles_anotados = 0
    goles_recibidos = 0
    validos = 0

    for p in partidos:
        if p["goals"]["home"] is None or p["goals"]["away"] is None:
            continue

        home_id = p["teams"]["home"]["id"]
        gh = p["goals"]["home"]
        ga = p["goals"]["away"]

        if team_id == home_id:
            goles_anotados += gh
            goles_recibidos += ga
        else:
            goles_anotados += ga
            goles_recibidos += gh

        validos += 1

    if validos == 0:
        return None

    return {
        "goles_anotados": goles_anotados / validos,
        "goles_recibidos": goles_recibidos / validos
    }