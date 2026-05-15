import csv
import os
from datetime import datetime
from dotenv import load_dotenv

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None
    import pytz

from api_datos import obtener_partidos
from odds_api import obtener_odds

from stats_api import (
    obtener_stats_equipo,
    obtener_forma_reciente
)

from modelo import (
    prob_over_25,
    prob_btts,
    calcular_value,
    calcular_stake
)

# ==============================
# ENV
# ==============================

ruta_env = os.path.join(
    os.path.dirname(__file__),
    "..",
    ".env"
)

load_dotenv(ruta_env)

# ==============================
# ARCHIVO ENVIADOS
# ==============================

RUTA_ENVIADOS = os.path.join(
    os.path.dirname(__file__),
    "..",
    "enviados.txt"
)

if not os.path.exists(RUTA_ENVIADOS):

    with open(RUTA_ENVIADOS, "w") as f:
        pass

with open(RUTA_ENVIADOS, "r") as f:

    ENVIADOS = set(
        linea.strip()
        for linea in f.readlines()
    )

# ==============================
# CONVERTIR FECHA A COLOMBIA
# ==============================

def convertir_fecha_colombia(fecha_api):

    try:

        fecha_api = str(fecha_api).strip()

        fecha_utc = datetime.fromisoformat(
            fecha_api.replace("Z", "+00:00")
        )

        if fecha_utc.tzinfo is None:

            if ZoneInfo is not None:
                fecha_utc = fecha_utc.replace(
                    tzinfo=ZoneInfo("UTC")
                )
            else:
                fecha_utc = pytz.utc.localize(
                    fecha_utc
                )

        if ZoneInfo is not None:

            zona_colombia = ZoneInfo(
                "America/Bogota"
            )

            fecha_colombia = fecha_utc.astimezone(
                zona_colombia
            )

        else:

            zona_colombia = pytz.timezone(
                "America/Bogota"
            )

            fecha_colombia = fecha_utc.astimezone(
                zona_colombia
            )

        return fecha_colombia.strftime(
            "%Y-%m-%d %H:%M"
        )

    except Exception as e:

        print(
            "⚠️ Error convirtiendo fecha:",
            e
        )

        return (
            str(fecha_api)[:16]
            .replace("T", " ")
        )

# ==============================
# GUARDAR CSV
# ==============================

def guardar(picks):

    ruta = os.path.join(
        os.path.dirname(__file__),
        "..",
        "picks.csv"
    )

    campos = [
        "fecha",
        "fixture_id",
        "partido",
        "liga",
        "mercado",
        "odd",
        "prob",
        "value",
        "score",
        "stake",
        "resultado",
        "profit",
        "notificado"
    ]

    with open(
        ruta,
        "a",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=campos
        )

        if f.tell() == 0:
            writer.writeheader()

        for p in picks:

            writer.writerow({

                "fecha": p["date"],
                "fixture_id": p["fixture_id"],
                "partido": p["match"],
                "liga": p["league"],
                "mercado": p["market"],
                "odd": p["odd"],
                "prob": round(p["prob"], 2),
                "value": round(p["value"], 2),
                "score": round(p["score"], 2),
                "stake": p["stake"],
                "resultado": "pendiente",
                "profit": 0,
                "notificado": "no"
            })

# ==============================
# PROBABILIDAD OVER 1.5
# ==============================

def prob_over_15(lam_local, lam_visit):

    total = lam_local + lam_visit

    from math import exp

    p0 = exp(-total)
    p1 = total * exp(-total)

    return 1 - (p0 + p1)

# ==============================
# CLASIFICAR LIGAS POR PAÍS + NOMBRE
# ==============================

def obtener_nivel_liga(league_name, country):

    league_name = str(league_name).strip()
    country = str(country).strip()

    LIGAS_TOP = [

        ("England", "Premier League"),
        ("England", "Championship"),

        ("Spain", "La Liga"),
        ("Spain", "LaLiga"),
        ("Spain", "Primera Division"),
        ("Spain", "Primera División"),

        ("Italy", "Serie A"),

        ("Germany", "Bundesliga"),

        ("France", "Ligue 1"),

        ("Portugal", "Primeira Liga"),
        ("Portugal", "Liga Portugal"),

        ("Netherlands", "Eredivisie"),

        ("Brazil", "Serie A"),
        ("Brazil", "Brasileirao"),
        ("Brazil", "Serie A Brasil"),
        ("Brazil", "Brazil Serie A"),

        ("Argentina", "Liga Profesional Argentina"),
        ("Argentina", "Primera División Argentina"),

        ("USA", "MLS"),
        ("USA", "Major League Soccer"),

        ("Mexico", "Liga MX"),

        ("World", "UEFA Champions League"),
        ("World", "UEFA Europa League"),
        ("World", "Copa Libertadores")
    ]

    LIGAS_MEDIAS = [

        ("Colombia", "Primera A"),
        ("Colombia", "Primera B"),
        ("Colombia", "Copa Colombia"),

        ("Belgium", "Jupiler Pro League"),
        ("Belgium", "Belgian Pro League"),

        ("Turkey", "Super Lig"),
        ("Turkey", "Süper Lig"),
        ("Turkey", "1. Lig"),

        ("Scotland", "Premiership"),
        ("Scotland", "Scottish Premiership"),

        ("Switzerland", "Super League"),
        ("Switzerland", "Swiss Super League"),
        ("Switzerland", "Challenge League"),

        ("Austria", "Bundesliga"),
        ("Austria", "Austrian Bundesliga"),

        ("Denmark", "Superliga"),
        ("Denmark", "Danish Superliga"),

        ("Norway", "Eliteserien"),

        ("Sweden", "Allsvenskan"),

        ("Poland", "Ekstraklasa"),
        ("Poland", "Poland Ekstraklasa"),

        ("Hungary", "NB I"),

        ("Romania", "Liga I"),
        ("Romania", "Romania Liga I"),

        ("Serbia", "Super Liga"),
        ("Serbia", "Serbia Super Liga"),

        ("Croatia", "HNL"),
        ("Croatia", "Croatia HNL"),

        ("Greece", "Super League 1"),
        ("Greece", "Greece Super League"),

        ("Czech-Republic", "Czech Liga"),
        ("Czech-Republic", "Czech First League"),

        ("Ecuador", "Liga Pro"),
        ("Ecuador", "Liga Pro Ecuador"),

        ("Chile", "Primera División"),
        ("Chile", "Primera Division"),
        ("Chile", "Primera División Chile"),
        ("Chile", "Primera Division Chile"),

        ("Peru", "Primera División"),
        ("Peru", "Segunda División"),
        ("Peru", "Liga 1"),
        ("Peru", "Liga 1 Peru"),
        ("Peru", "Liga 1 Perú"),

        ("Paraguay", "Division Profesional - Apertura"),
        ("Paraguay", "Primera División Paraguay"),
        ("Paraguay", "Primera Division Paraguay"),

        ("Uruguay", "Primera División - Apertura"),
        ("Uruguay", "Primera División Uruguay"),
        ("Uruguay", "Primera Division Uruguay"),

        ("Venezuela", "Primera División"),

        ("Portugal", "Segunda Liga"),

        ("Italy", "Serie B"),

        ("Spain", "Segunda División"),
        ("Spain", "Segunda Division"),

        ("Ireland", "Premier Division"),

        ("Saudi-Arabia", "Pro League"),

        ("World", "UEFA Conference League"),
        ("World", "Copa Sudamericana"),
        ("World", "CONCACAF Champions Cup")
    ]

    if (country, league_name) in LIGAS_TOP:
        return "TOP"

    if (country, league_name) in LIGAS_MEDIAS:
        return "MEDIA"

    return None

# ==============================
# FILTROS POR NIVEL DE LIGA
# ==============================

def obtener_filtros_mercado(nivel_liga, mercado):

    if nivel_liga == "TOP":

        if mercado == "Over 1.5":
            return {
                "min_value": 0.04,
                "min_prob": 0.78,
                "min_lambda": 2.70,
                "min_odd": 1.35,
                "max_odd": 1.75,
                "min_score": 20
            }

        if mercado == "Over 2.5":
            return {
                "min_value": 0.025,
                "min_prob": 0.58,
                "min_lambda": 2.60,
                "min_odd": 1.45,
                "max_odd": 2.90,
                "min_score": 18
            }

        if mercado == "BTTS":
            return {
                "min_value": 0.03,
                "min_prob": 0.53,
                "min_lambda": 2.35,
                "min_odd": 1.55,
                "max_odd": 2.70,
                "min_score": 18
            }

    if nivel_liga == "MEDIA":

        if mercado == "Over 1.5":
            return {
                "min_value": 0.05,
                "min_prob": 0.82,
                "min_lambda": 2.90,
                "min_odd": 1.40,
                "max_odd": 1.75,
                "min_score": 22
            }

        if mercado == "Over 2.5":
            return {
                "min_value": 0.03,
                "min_prob": 0.60,
                "min_lambda": 2.75,
                "min_odd": 1.45,
                "max_odd": 2.90,
                "min_score": 19
            }

        if mercado == "BTTS":
            return {
                "min_value": 0.04,
                "min_prob": 0.58,
                "min_lambda": 2.55,
                "min_odd": 1.55,
                "max_odd": 2.70,
                "min_score": 20
            }

    return None

# ==============================
# NORMALIZAR LAMBDAS INFLADAS
# ==============================

def normalizar_lambdas(lam_local, lam_visit, max_total=4.2):

    try:

        lam_local = float(lam_local)
        lam_visit = float(lam_visit)

        if lam_local < 0:
            lam_local = 0

        if lam_visit < 0:
            lam_visit = 0

        total = lam_local + lam_visit

        if total <= 0:
            return lam_local, lam_visit

        if total > max_total:

            factor = max_total / total

            lam_local = lam_local * factor
            lam_visit = lam_visit * factor

            print(
                f"⚠️ Lambdas normalizadas "
                f"| Total original: {round(total,2)} "
                f"| Total nuevo: {round(lam_local + lam_visit,2)}"
            )

        return lam_local, lam_visit

    except Exception as e:

        print("⚠️ Error normalizando lambdas:", e)

        return lam_local, lam_visit

# ==============================
# LIMPIAR PROMEDIOS API
# ==============================

def limpiar_promedio(valor, minimo=0.45):

    try:

        if valor is None:
            return minimo

        valor = str(valor).strip()

        if valor == "":
            return minimo

        valor = float(valor)

        if valor <= 0:
            return minimo

        return valor

    except Exception:

        return minimo

# ==============================
# CALCULAR LAMBDAS
# ==============================

def calcular_lambdas(p):

    try:

        league_id = p["league"]["id"]
        season = p["league"]["season"]

        home_id = p["teams"]["home"]["id"]
        away_id = p["teams"]["away"]["id"]

        stats_home = obtener_stats_equipo(
            home_id,
            league_id,
            season
        )

        stats_away = obtener_stats_equipo(
            away_id,
            league_id,
            season
        )

        stats_home = (
            stats_home[0]
            if isinstance(stats_home, list)
            else stats_home
        )

        stats_away = (
            stats_away[0]
            if isinstance(stats_away, list)
            else stats_away
        )

        if not stats_home or not stats_away:
            print("⚠️ No hay stats suficientes para uno de los equipos")
            return None, None

        atk_home_temp = limpiar_promedio(
            stats_home["goals"]["for"]["average"]["home"]
        )

        def_home_temp = limpiar_promedio(
            stats_home["goals"]["against"]["average"]["home"]
        )

        atk_away_temp = limpiar_promedio(
            stats_away["goals"]["for"]["average"]["away"]
        )

        def_away_temp = limpiar_promedio(
            stats_away["goals"]["against"]["average"]["away"]
        )

        forma_home = obtener_forma_reciente(
            home_id,
            league_id,
            season,
            venue="home"
        )

        forma_away = obtener_forma_reciente(
            away_id,
            league_id,
            season,
            venue="away"
        )

        if not forma_home or not forma_away:

            print("⚠️ Sin forma reciente completa, usando solo stats de temporada")

            lam_local = atk_home_temp * max(def_away_temp, 0.5)
            lam_visit = atk_away_temp * max(def_home_temp, 0.5)

            lam_local, lam_visit = normalizar_lambdas(
                lam_local,
                lam_visit
            )

            return (
                min(lam_local, 3.2),
                min(lam_visit, 3.2)
            )

        atk_home = (
            atk_home_temp * 0.7
            + forma_home["gf"] * 0.3
        )

        def_home = (
            def_home_temp * 0.7
            + forma_home["gc"] * 0.3
        )

        atk_away = (
            atk_away_temp * 0.7
            + forma_away["gf"] * 0.3
        )

        def_away = (
            def_away_temp * 0.7
            + forma_away["gc"] * 0.3
        )

        lam_local = atk_home * max(def_away, 0.5)
        lam_visit = atk_away * max(def_home, 0.5)

        lam_local, lam_visit = normalizar_lambdas(
            lam_local,
            lam_visit
        )

        print(
            f"📈 Forma reciente aplicada "
            f"| Home GF: {round(forma_home['gf'],2)} "
            f"| Home GC: {round(forma_home['gc'],2)} "
            f"| Home PJ: {forma_home['partidos']} "
            f"| Away GF: {round(forma_away['gf'],2)} "
            f"| Away GC: {round(forma_away['gc'],2)} "
            f"| Away PJ: {forma_away['partidos']}"
        )

        return (
            min(lam_local, 3.2),
            min(lam_visit, 3.2)
        )

    except Exception as e:

        print("❌ Error lambdas:", e)

        return None, None

# ==============================
# MAIN
# ==============================

def main():

    print("🚀 BOT INICIADO")

    BANK = 1000

    partidos = obtener_partidos()

    print(f"📋 Partidos recibidos desde la API: {len(partidos)}")

    picks = []

    for p in partidos:

        try:

            status = p["fixture"]["status"]["short"]

            fixture_id = str(
                p["fixture"]["id"]
            )

            fecha_partido = convertir_fecha_colombia(
                p["fixture"]["date"]
            )

            local = p["teams"]["home"]["name"]
            visitante = p["teams"]["away"]["name"]
            league_name = p["league"]["name"]
            country = p["league"].get("country", "")

            print("\n==============================")
            print(f"⚽ {local} vs {visitante}")
            print(f"🏆 Liga detectada: {league_name}")
            print(f"🌍 País liga: {country}")
            print(f"📅 Fecha partido Colombia: {fecha_partido}")
            print(f"🆔 Fixture ID: {fixture_id}")
            print(f"📌 Estado API: {status}")

            if status != "NS":
                print(f"⏭️ Partido ignorado porque no está en estado NS: {status}")
                continue

            if fixture_id in ENVIADOS:
                print(f"🔁 Partido ya estaba en enviados.txt: {local} vs {visitante}")
                continue

            nivel_liga = obtener_nivel_liga(
                league_name,
                country
            )

            if nivel_liga is None:
                print(f"⛔ Liga no permitida: {league_name} | País: {country}")
                continue

            if nivel_liga == "TOP":
                print("🟢 Nivel liga: TOP")
            elif nivel_liga == "MEDIA":
                print("🟡 Nivel liga: MEDIA")
            else:
                print("⚪ Nivel liga: permitida sin categoría")

            odds = obtener_odds(fixture_id)

            if not odds:
                print(f"⚠️ Sin odds disponibles: {local} vs {visitante}")
                continue

            bets = []

            for book in odds:

                if "bets" in book:
                    bets.extend(book["bets"])

            print(f"🎲 Mercados encontrados en odds: {len(bets)}")

            lamL, lamV = calcular_lambdas(p)

            if lamL is None:
                print(f"⚠️ Sin lambdas/stats suficientes: {local} vs {visitante}")
                continue

            total_lambda = lamL + lamV

            print(
                f"📊 Lambdas | Local: {round(lamL,2)} "
                f"| Visitante: {round(lamV,2)} "
                f"| Total: {round(total_lambda,2)}"
            )

            if total_lambda < 2.1:
                print(f"⛔ Descartado por lambda baja general: {round(total_lambda,2)}")
                continue

            prob_o = prob_over_25(
                lamL,
                lamV
            )

            prob_b = prob_btts(
                lamL,
                lamV
            )

            prob_o15 = prob_over_15(
                lamL,
                lamV
            )

            print(
                f"🧠 Probabilidades modelo "
                f"| Over 1.5: {round(prob_o15,2)} "
                f"| Over 2.5: {round(prob_o,2)} "
                f"| BTTS: {round(prob_b,2)}"
            )

            picks_partido = []

            for b in bets:

                # ==============================
                # OVERS
                # ==============================

                if b["name"] == "Goals Over/Under":

                    for v in b["values"]:

                        # OVER 1.5

                        if v["value"] == "Over 1.5":

                            try:

                                odd = float(v["odd"])

                                val = calcular_value(
                                    prob_o15,
                                    odd
                                )

                                filtros = obtener_filtros_mercado(
                                    nivel_liga,
                                    "Over 1.5"
                                )

                                score = (
                                    (val * 100)
                                    + (prob_o15 * 10)
                                    + total_lambda
                                )

                                if (
                                    val > filtros["min_value"]
                                    and prob_o15 > filtros["min_prob"]
                                    and total_lambda > filtros["min_lambda"]
                                    and filtros["min_odd"] <= odd <= filtros["max_odd"]
                                ):

                                    stake = calcular_stake(
                                        BANK,
                                        val,
                                        odd
                                    )

                                    if score < filtros["min_score"]:
                                        print(
                                            f"⛔ Over 1.5 descartado por score bajo "
                                            f"| Nivel: {nivel_liga} "
                                            f"| Odd: {odd} "
                                            f"| Value: {round(val,2)} "
                                            f"| Score: {round(score,2)} "
                                            f"| Score mínimo: {filtros['min_score']}"
                                        )
                                        continue

                                    print(
                                        f"✅ Candidato Over 1.5 "
                                        f"| Nivel: {nivel_liga} "
                                        f"| Odd: {odd} "
                                        f"| Prob: {round(prob_o15,2)} "
                                        f"| Value: {round(val,2)} "
                                        f"| Score: {round(score,2)}"
                                    )

                                    picks_partido.append({

                                        "fixture_id": fixture_id,
                                        "date": fecha_partido,
                                        "match": f"{local} vs {visitante}",
                                        "league": league_name,
                                        "market": "Over 1.5",
                                        "odd": odd,
                                        "prob": prob_o15,
                                        "value": val,
                                        "score": round(score, 2),
                                        "stake": stake
                                    })

                                else:
                                    print(
                                        f"❌ Over 1.5 no cumple filtros "
                                        f"| Nivel: {nivel_liga} "
                                        f"| Odd: {odd} "
                                        f"| Prob: {round(prob_o15,2)} "
                                        f"| Value: {round(val,2)} "
                                        f"| Lambda: {round(total_lambda,2)}"
                                    )

                            except Exception as e:
                                print("⚠️ Error evaluando Over 1.5:", e)
                                continue

                        # OVER 2.5

                        if v["value"] == "Over 2.5":

                            try:

                                odd = float(v["odd"])

                                val = calcular_value(
                                    prob_o,
                                    odd
                                )

                                filtros = obtener_filtros_mercado(
                                    nivel_liga,
                                    "Over 2.5"
                                )

                                score = (
                                    (val * 100)
                                    + (prob_o * 10)
                                    + total_lambda
                                )

                                # ==============================
                                # PROTECCIÓN OVER 2.5 CUOTA BAJA
                                # ==============================

                                if odd < 1.55:

                                    if nivel_liga == "TOP" and prob_o < 0.68:
                                        print(
                                            f"⛔ Over 2.5 descartado por cuota baja sin probabilidad premium "
                                            f"| Nivel: {nivel_liga} "
                                            f"| Odd: {odd} "
                                            f"| Prob: {round(prob_o,2)} "
                                            f"| Prob mínima premium: 0.68"
                                        )
                                        continue

                                    if nivel_liga == "MEDIA" and prob_o < 0.70:
                                        print(
                                            f"⛔ Over 2.5 descartado por cuota baja sin probabilidad premium "
                                            f"| Nivel: {nivel_liga} "
                                            f"| Odd: {odd} "
                                            f"| Prob: {round(prob_o,2)} "
                                            f"| Prob mínima premium: 0.70"
                                        )
                                        continue

                                if (
                                    val > filtros["min_value"]
                                    and prob_o > filtros["min_prob"]
                                    and total_lambda > filtros["min_lambda"]
                                    and filtros["min_odd"] <= odd <= filtros["max_odd"]
                                ):

                                    stake = calcular_stake(
                                        BANK,
                                        val,
                                        odd
                                    )

                                    if score < filtros["min_score"]:
                                        print(
                                            f"⛔ Over 2.5 descartado por score bajo "
                                            f"| Nivel: {nivel_liga} "
                                            f"| Odd: {odd} "
                                            f"| Value: {round(val,2)} "
                                            f"| Score: {round(score,2)} "
                                            f"| Score mínimo: {filtros['min_score']}"
                                        )
                                        continue

                                    print(
                                        f"✅ Candidato Over 2.5 "
                                        f"| Nivel: {nivel_liga} "
                                        f"| Odd: {odd} "
                                        f"| Prob: {round(prob_o,2)} "
                                        f"| Value: {round(val,2)} "
                                        f"| Score: {round(score,2)}"
                                    )

                                    picks_partido.append({

                                        "fixture_id": fixture_id,
                                        "date": fecha_partido,
                                        "match": f"{local} vs {visitante}",
                                        "league": league_name,
                                        "market": "Over 2.5",
                                        "odd": odd,
                                        "prob": prob_o,
                                        "value": val,
                                        "score": round(score, 2),
                                        "stake": stake
                                    })

                                else:
                                    print(
                                        f"❌ Over 2.5 no cumple filtros "
                                        f"| Nivel: {nivel_liga} "
                                        f"| Odd: {odd} "
                                        f"| Prob: {round(prob_o,2)} "
                                        f"| Value: {round(val,2)} "
                                        f"| Lambda: {round(total_lambda,2)}"
                                    )

                            except Exception as e:
                                print("⚠️ Error evaluando Over 2.5:", e)
                                continue

                # ==============================
                # BTTS
                # ==============================

                if b["name"] == "Both Teams Score":

                    for v in b["values"]:

                        if v["value"] == "Yes":

                            try:

                                odd = float(v["odd"])

                                val = calcular_value(
                                    prob_b,
                                    odd
                                )

                                filtros = obtener_filtros_mercado(
                                    nivel_liga,
                                    "BTTS"
                                )

                                score = (
                                    (val * 100)
                                    + (prob_b * 10)
                                    + total_lambda
                                )

                                # ==============================
                                # PROTECCIÓN BTTS EQUILIBRIO
                                # ==============================

                                if lamL < 0.95 or lamV < 0.95:
                                    print(
                                        f"⛔ BTTS descartado por lambda individual baja "
                                        f"| Local: {round(lamL,2)} "
                                        f"| Visitante: {round(lamV,2)} "
                                        f"| Mínimo: 0.95"
                                    )
                                    continue

                                if abs(lamL - lamV) > 1.35:
                                    print(
                                        f"⛔ BTTS descartado por desequilibrio de lambdas "
                                        f"| Local: {round(lamL,2)} "
                                        f"| Visitante: {round(lamV,2)} "
                                        f"| Diferencia: {round(abs(lamL - lamV),2)} "
                                        f"| Máximo: 1.35"
                                    )
                                    continue

                                if odd < 1.65:

                                    if nivel_liga == "TOP" and prob_b < 0.68:
                                        print(
                                            f"⛔ BTTS descartado por cuota baja sin probabilidad premium "
                                            f"| Nivel: {nivel_liga} "
                                            f"| Odd: {odd} "
                                            f"| Prob: {round(prob_b,2)} "
                                            f"| Prob mínima premium: 0.68"
                                        )
                                        continue

                                    if nivel_liga == "MEDIA" and prob_b < 0.70:
                                        print(
                                            f"⛔ BTTS descartado por cuota baja sin probabilidad premium "
                                            f"| Nivel: {nivel_liga} "
                                            f"| Odd: {odd} "
                                            f"| Prob: {round(prob_b,2)} "
                                            f"| Prob mínima premium: 0.70"
                                        )
                                        continue

                                if (
                                    val > filtros["min_value"]
                                    and prob_b > filtros["min_prob"]
                                    and total_lambda > filtros["min_lambda"]
                                    and filtros["min_odd"] <= odd <= filtros["max_odd"]
                                ):

                                    stake = calcular_stake(
                                        BANK,
                                        val,
                                        odd
                                    )

                                    if score < filtros["min_score"]:
                                        print(
                                            f"⛔ BTTS descartado por score bajo "
                                            f"| Nivel: {nivel_liga} "
                                            f"| Odd: {odd} "
                                            f"| Value: {round(val,2)} "
                                            f"| Score: {round(score,2)} "
                                            f"| Score mínimo: {filtros['min_score']}"
                                        )
                                        continue

                                    print(
                                        f"✅ Candidato BTTS "
                                        f"| Nivel: {nivel_liga} "
                                        f"| Odd: {odd} "
                                        f"| Prob: {round(prob_b,2)} "
                                        f"| Value: {round(val,2)} "
                                        f"| Score: {round(score,2)}"
                                    )

                                    picks_partido.append({

                                        "fixture_id": fixture_id,
                                        "date": fecha_partido,
                                        "match": f"{local} vs {visitante}",
                                        "league": league_name,
                                        "market": "BTTS",
                                        "odd": odd,
                                        "prob": prob_b,
                                        "value": val,
                                        "score": round(score, 2),
                                        "stake": stake
                                    })

                                else:
                                    print(
                                        f"❌ BTTS no cumple filtros "
                                        f"| Nivel: {nivel_liga} "
                                        f"| Odd: {odd} "
                                        f"| Prob: {round(prob_b,2)} "
                                        f"| Value: {round(val,2)} "
                                        f"| Lambda: {round(total_lambda,2)}"
                                    )

                            except Exception as e:
                                print("⚠️ Error evaluando BTTS:", e)
                                continue

            # ==============================
            # SOLO MEJOR PICK POR PARTIDO
            # ==============================

            if picks_partido:

                mejor_pick = max(
                    picks_partido,
                    key=lambda x: x["score"]
                )

                picks.append(
                    mejor_pick
                )

                print(
                    f"🏆 Mejor pick: "
                    f"{mejor_pick['market']} "
                    f"| Score: {round(mejor_pick['score'],2)}"
                )

                with open(
                    RUTA_ENVIADOS,
                    "a"
                ) as f:

                    f.write(
                        fixture_id + "\n"
                    )

            else:
                print(f"❌ Sin mercado válido para: {local} vs {visitante}")

        except Exception as e:

            print(
                "❌ Error partido:",
                e
            )

    # ==============================
    # ELIMINAR DUPLICADOS
    # ==============================

    ruta_csv = os.path.join(
        os.path.dirname(__file__),
        "..",
        "picks.csv"
    )

    existentes = set()

    if os.path.exists(ruta_csv):

        with open(
            ruta_csv,
            newline="",
            encoding="utf-8"
        ) as f:

            reader = csv.DictReader(f)

            for row in reader:

                clave = (
                    str(row["fixture_id"])
                    + "_"
                    + row["mercado"]
                )

                existentes.add(clave)

    picks_unicos = {}

    for p in picks:

        clave = (
            str(p["fixture_id"])
            + "_"
            + p["market"]
        )

        if clave in existentes:
            print(
                f"🔁 Pick ya existía en picks.csv y no se guardará otra vez: "
                f"{p['match']} | {p['market']}"
            )
            continue

        if (
            clave not in picks_unicos
            or p["score"] > picks_unicos[clave]["score"]
        ):

            picks_unicos[clave] = p

    picks = list(
        picks_unicos.values()
    )

    # ==============================
    # ORDENAR PICKS
    # ==============================

    picks = sorted(

        picks,

        key=lambda x: x["score"],

        reverse=True

    )[:12]

    print(
        f"🔥 Picks finales: {len(picks)}"
    )

    # ==============================
    # GUARDAR PICKS
    # ==============================

    if picks:

        guardar(
            picks
        )

        print(f"💾 Picks guardadas: {len(picks)}")
        print("📌 Picks guardadas con notificado = no")
        print("📨 El envío a Telegram lo hará enviar_telegram.py")

    else:

        print(
            "⚠️ No hubo picks nuevas"
        )

# ==============================
# START
# ==============================

if __name__ == "__main__":

    main()