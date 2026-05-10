import csv
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

from api_datos import obtener_partidos
from odds_api import obtener_odds
from stats_api import obtener_stats_equipo
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

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

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
# TELEGRAM
# ==============================

def enviar_telegram(mensaje):

    try:

        url = (
            f"https://api.telegram.org/bot"
            f"{TELEGRAM_TOKEN}/sendMessage"
        )

        requests.get(
            url,
            params={
                "chat_id": CHAT_ID,
                "text": mensaje
            },
            timeout=20
        )

        print("✅ Mensaje enviado")

    except Exception as e:

        print("❌ Error Telegram:", e)

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

                "fecha": datetime.now(),
                "fixture_id": p["fixture_id"],
                "partido": p["match"],
                "liga": p["league"],
                "mercado": p["market"],
                "odd": p["odd"],
                "prob": round(p["prob"], 2),
                "value": round(p["value"], 2),
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

        atk_home = float(
            stats_home["goals"]["for"]["average"]["home"]
        )

        def_home = float(
            stats_home["goals"]["against"]["average"]["home"]
        )

        atk_away = float(
            stats_away["goals"]["for"]["average"]["away"]
        )

        def_away = float(
            stats_away["goals"]["against"]["average"]["away"]
        )

        lam_local = atk_home * max(def_away, 0.5)
        lam_visit = atk_away * max(def_home, 0.5)

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

    # ==============================
    # LIGAS PERMITIDAS
    # ==============================

    LIGAS_PERMITIDAS = [

        # INGLATERRA
        "Premier League",

        # ALEMANIA
        "Bundesliga",

        # ESPAÑA
        "La Liga",

        # ITALIA
        "Serie A",
        "Coppa Italia",

        # COLOMBIA
        "Primera A",
        "Primera B",
        "Copa Colombia",

        # ARGENTINA
        "Liga Profesional Argentina",
        "Copa Argentina",

        # BRASIL
        "Serie A Brasil",
        "Brasileirao",
        "Serie A",

        # EUROPA
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

            fecha_partido = (
                p["fixture"]["date"][:16]
                .replace("T", " ")
            )

            local = p["teams"]["home"]["name"]
            visitante = p["teams"]["away"]["name"]

            print(f"\n⚽ Analizando: {local} vs {visitante}")

            league_name = p["league"]["name"]

            print(f"🏆 Liga detectada: {league_name}")

            if league_name not in LIGAS_PERMITIDAS:

                print(f"❌ Liga bloqueada: {league_name}")

                continue

            print(f"✅ Liga permitida: {league_name}")

            odds = obtener_odds(fixture_id)

            if not odds:

                print("❌ Sin odds")

                continue

            bets = []

            for book in odds:

                if "bets" in book:
                    bets.extend(book["bets"])

            print(f"💰 Odds válidas: {len(bets)}")

            lamL, lamV = calcular_lambdas(p)

            if lamL is None:

                print("❌ Sin lambdas")

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

            print(f"📊 Lambda total: {round(total_lambda,2)}")
            print(f"📈 Prob Over2.5: {round(prob_o,2)}")
            print(f"📈 Prob BTTS: {round(prob_b,2)}")
            print(f"📈 Prob Over1.5: {round(prob_o15,2)}")

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

                                    print(f"🔥 PICK ENCONTRADA: {local} vs {visitante}")

                                    stake = calcular_stake(
                                        BANK,
                                        val,
                                        odd
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

                                    print(f"🔥 PICK ENCONTRADA: {local} vs {visitante}")

                                    stake = calcular_stake(
                                        BANK,
                                        val,
                                        odd
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

                                    print(f"🔥 PICK ENCONTRADA: {local} vs {visitante}")

                                    stake = calcular_stake(
                                        BANK,
                                        val,
                                        odd
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
                                        "stake": stake
                                    })

                            except:
                                continue

            if picks_partido:

                picks.extend(
                    picks_partido
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
            or p["value"] > picks_unicos[clave]["value"]
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

        key=lambda x: x["value"],

        reverse=True

    )[:8]

    print(
        f"🔥 Picks finales: {len(picks)}"
    )

    # ==============================
    # TELEGRAM
    # ==============================

    mensaje = "🔥 PICKS DEL BOT 🔥\n\n"

    agrupados = {}

    for p in picks:

        partido = p["match"]

        if partido not in agrupados:
            agrupados[partido] = []

        agrupados[partido].append(p)

    for partido, lista in agrupados.items():

        primera = lista[0]

        mensaje += (
            f"⚽ {partido}\n"
            f"🏆 {primera['league']}\n"
            f"📅 {primera['date']}\n\n"
            f"🔥 POSIBLES PICKS\n"
        )

        for p in lista:

            mensaje += (
                f"• {p['market']} → {p['odd']}\n"
            )

        mejor = max(
            lista,
            key=lambda x: x["value"]
        )

        mensaje += (
            f"\n📊 Mejor Pick: {mejor['market']}\n"
            f"🔥 Value: {round(mejor['value'],2)}\n"
            f"💵 Stake: {mejor['stake']}\n\n"
        )

    # ==============================
    # GUARDAR Y ENVIAR
    # ==============================

    if picks:

        guardar(
            picks
        )

        print(f"💾 Picks guardadas: {len(picks)}")

        enviar_telegram(
            mensaje
        )

    else:

        print(
            "⚠️ No hubo picks nuevos"
        )

# ==============================
# START
# ==============================

if __name__ == "__main__":

    main()