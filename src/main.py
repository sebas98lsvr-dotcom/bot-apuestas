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

        # API suele venir así:
        # 2026-05-14T18:00:00+00:00
        # o así:
        # 2026-05-14T18:00:00Z

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
# CALCULAR LAMBDAS
# ==============================

def calcular_lambdas(p):

    try:

        league_id = p["league"]["id"]
        season = p["league"]["season"]

        home_id = p["teams"]["home"]["id"]
        away_id = p["teams"]["away"]["id"]

        # ==============================
        # STATS TEMPORADA
        # ==============================

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
            return None, None

        # ==============================
        # PROMEDIOS TEMPORADA
        # ==============================

        atk_home_temp = float(
            stats_home["goals"]["for"]["average"]["home"]
        )

        def_home_temp = float(
            stats_home["goals"]["against"]["average"]["home"]
        )

        atk_away_temp = float(
            stats_away["goals"]["for"]["average"]["away"]
        )

        def_away_temp = float(
            stats_away["goals"]["against"]["average"]["away"]
        )

        # ==============================
        # FORMA RECIENTE
        # ==============================

        forma_home = obtener_forma_reciente(
            home_id
        )

        forma_away = obtener_forma_reciente(
            away_id
        )

        # Si falla forma reciente
        if not forma_home or not forma_away:

            lam_local = atk_home_temp * max(def_away_temp, 0.5)
            lam_visit = atk_away_temp * max(def_home_temp, 0.5)

            return (
                min(lam_local, 4),
                min(lam_visit, 4)
            )

        # ==============================
        # MEZCLA TEMPORADA + FORMA
        # ==============================

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

        # ==============================
        # LAMBDAS
        # ==============================

        lam_local = atk_home * max(def_away, 0.5)
        lam_visit = atk_away * max(def_home, 0.5)

        print(
            f"📈 Forma reciente aplicada "
            f"| Home GF: {round(forma_home['gf'],2)} "
            f"| Away GF: {round(forma_away['gf'],2)}"
        )

        return (
            min(lam_local, 4),
            min(lam_visit, 4)
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

    LIGAS_PERMITIDAS = [

        "Premier League",
        "Bundesliga",
        "La Liga",
        "Serie A",
        "Coppa Italia",
        "Primera A",
        "Primera B",
        "Copa Colombia",
        "Liga Profesional Argentina",
        "Copa Argentina",
        "Serie A Brasil",
        "Brasileirao",
        "Serie A",
        "UEFA Champions League",
        "UEFA Europa League"
    ]

    picks = []

    for p in partidos:

        try:

            if p["fixture"]["status"]["short"] != "NS":
                continue

            fixture_id = str(
                p["fixture"]["id"]
            )

            if fixture_id in ENVIADOS:
                continue

            fecha_partido = convertir_fecha_colombia(
                p["fixture"]["date"]
            )

            local = p["teams"]["home"]["name"]
            visitante = p["teams"]["away"]["name"]

            print(f"\n⚽ {local} vs {visitante}")
            print(f"📅 Fecha partido Colombia: {fecha_partido}")

            league_name = p["league"]["name"]

            if league_name not in LIGAS_PERMITIDAS:
                continue

            odds = obtener_odds(fixture_id)

            if not odds:
                continue

            bets = []

            for book in odds:

                if "bets" in book:
                    bets.extend(book["bets"])

            lamL, lamV = calcular_lambdas(p)

            if lamL is None:
                continue

            total_lambda = lamL + lamV

            if total_lambda < 2.1:
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

                                if (
                                    val > 0.02
                                    and prob_o15 > 0.70
                                    and total_lambda > 2.1
                                    and 1.20 <= odd <= 1.80
                                ):

                                    stake = calcular_stake(
                                        BANK,
                                        val,
                                        odd
                                    )

                                    score = (
                                        (val * 100)
                                        + (prob_o15 * 10)
                                        + total_lambda
                                    )

                                    if score < 18:
                                        continue

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

                            except:
                                continue

                        # OVER 2.5

                        if v["value"] == "Over 2.5":

                            try:

                                odd = float(v["odd"])

                                val = calcular_value(
                                    prob_o,
                                    odd
                                )

                                if (
                                    val > 0.03
                                    and prob_o > 0.54
                                    and total_lambda > 2.45
                                    and 1.60 <= odd <= 2.90
                                ):

                                    stake = calcular_stake(
                                        BANK,
                                        val,
                                        odd
                                    )

                                    score = (
                                        (val * 100)
                                        + (prob_o * 10)
                                        + total_lambda
                                    )

                                    if score < 18:
                                        continue

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

                            except:
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

                                if (
                                    val > 0.03
                                    and prob_b > 0.53
                                    and total_lambda > 2.35
                                    and 1.55 <= odd <= 2.70
                                ):

                                    stake = calcular_stake(
                                        BANK,
                                        val,
                                        odd
                                    )

                                    score = (
                                        (val * 100)
                                        + (prob_b * 10)
                                        + total_lambda
                                    )

                                    if score < 18:
                                        continue

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

                            except:
                                continue

            # ==============================
            # SOLO MEJOR PICK
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

    )[:8]

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