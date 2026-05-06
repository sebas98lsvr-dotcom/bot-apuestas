import csv
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

from api_datos import obtener_partidos
from odds_api import obtener_odds
from stats_api import obtener_stats_equipo
from modelo import prob_over_25, prob_btts, calcular_value
from corners_model import calcular_corners_esperados
from bankroll import calcular_stake

# ==============================
# ENV
# ==============================
ruta_env = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(ruta_env)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ==============================
# TELEGRAM
# ==============================
def enviar_telegram(mensaje):

    try:

        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

        requests.get(url, params={
            "chat_id": CHAT_ID,
            "text": mensaje
        })

        print("✅ Mensaje enviado")

    except Exception as e:
        print("Error Telegram:", e)

# ==============================
# GUARDAR CSV
# ==============================
def guardar(picks):

    ruta = os.path.join(
        os.path.dirname(__file__),
        "..",
        "picks.csv"
    )

    crear = not os.path.exists(ruta)

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
        "profit"
    ]

    with open(ruta, "a", newline="", encoding="utf-8") as f:

        writer = csv.DictWriter(
            f,
            fieldnames=campos
        )

        if crear:
            writer.writeheader()

        for p in picks:

            writer.writerow({
                "fecha": datetime.now(),
                "fixture_id": p["fixture_id"],
                "partido": p["match"],
                "liga": p["league"],
                "mercado": p["market"],
                "odd": p["odd"],
                "prob": round(p["prob"],2),
                "value": round(p["value"],2),
                "stake": p["stake"],
                "resultado": "pendiente",
                "profit": 0
            })

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

        stats_home = stats_home[0] if isinstance(stats_home, list) else stats_home
        stats_away = stats_away[0] if isinstance(stats_away, list) else stats_away

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

        return (
            atk_home * max(def_away,0.5),
            atk_away * max(def_home,0.5)
        )

    except:
        return None, None

# ==============================
# MAIN
# ==============================
def main():

    print("🚀 BOT INICIADO")

    BANK = 1000

    partidos = obtener_partidos()

    picks = []

    for p in partidos:

        try:

            if p["fixture"]["status"]["short"] != "NS":
                continue

            fixture_id = p["fixture"]["id"]

            local = p["teams"]["home"]["name"]
            visitante = p["teams"]["away"]["name"]

            league_name = p["league"]["name"]
            league_id = p["league"]["id"]
            season = p["league"]["season"]

            odds = obtener_odds(fixture_id)

            if not odds:
                continue

            bets = odds[0]["bookmakers"][0]["bets"]

            # ======================
            # CORNERS
            # ======================
            corners = calcular_corners_esperados(
                p["teams"]["home"]["id"],
                p["teams"]["away"]["id"],
                league_id,
                season
            )

            if corners:

                for b in bets:

                    if "Corner" in b["name"]:

                        for v in b["values"]:

                            if "Over" in v["value"]:

                                linea = float(
                                    v["value"].split(" ")[1]
                                )

                                odd = float(v["odd"])

                                prob = min(
                                    max((corners-linea)/3+0.5,0),
                                    1
                                )

                                value = prob - (1/odd)

                                if value > 0.03:

                                    stake = calcular_stake(
                                        BANK,
                                        prob,
                                        odd
                                    )

                                    picks.append({
                                        "fixture_id": fixture_id,
                                        "match": f"{local} vs {visitante}",
                                        "league": league_name,
                                        "market": f"Corners Over {linea}",
                                        "odd": odd,
                                        "prob": prob,
                                        "value": value,
                                        "stake": stake
                                    })

            # ======================
            # GOLES
            # ======================
            lamL, lamV = calcular_lambdas(p)

            if lamL is None:
                continue

            prob_o = prob_over_25(lamL, lamV)
            prob_b = prob_btts(lamL, lamV)

            for b in bets:

                # ======================
                # OVER 2.5
                # ======================
                if b["name"] == "Goals Over/Under":

                    for v in b["values"]:

                        if v["value"] == "Over 2.5":

                            odd = float(v["odd"])

                            val = calcular_value(
                                prob_o,
                                odd
                            )

                            if val > 0.03 and prob_o > 0.50:

                                stake = calcular_stake(
                                    BANK,
                                    prob_o,
                                    odd
                                )

                                picks.append({
                                    "fixture_id": fixture_id,
                                    "match": f"{local} vs {visitante}",
                                    "league": league_name,
                                    "market": "Over 2.5",
                                    "odd": odd,
                                    "prob": prob_o,
                                    "value": val,
                                    "stake": stake
                                })

                # ======================
                # BTTS
                # ======================
                if b["name"] == "Both Teams Score":

                    for v in b["values"]:

                        if v["value"] == "Yes":

                            odd = float(v["odd"])

                            val = calcular_value(
                                prob_b,
                                odd
                            )

                            if val > 0.03 and prob_b > 0.50:

                                stake = calcular_stake(
                                    BANK,
                                    prob_b,
                                    odd
                                )

                                picks.append({
                                    "fixture_id": fixture_id,
                                    "match": f"{local} vs {visitante}",
                                    "league": league_name,
                                    "market": "BTTS",
                                    "odd": odd,
                                    "prob": prob_b,
                                    "value": val,
                                    "stake": stake
                                })

        except Exception as e:
            print("Error:", e)

    # ======================
    # ELIMINAR PICKS REPETIDAS
    # ======================

    picks_unicos = []

    vistos = set()

    for p in picks:

        # ======================
        # NORMALIZAR MERCADOS
        # ======================

        market_base = p["market"]

        # CORNERS
        if "Corners Over" in market_base:
            market_base = "Corners"

        # OVER 2.5
        elif "Over 2.5" in market_base:
            market_base = "Over 2.5"

        # BTTS
        elif "BTTS" in market_base:
            market_base = "BTTS"

        # ======================
        # CLAVE UNICA
        # ======================

        clave = (
            p["fixture_id"],
            market_base
        )

        # ======================
        # EVITAR DUPLICADAS
        # ======================

        if clave not in vistos:

            vistos.add(clave)

            picks_unicos.append(p)

    # Reemplazar lista
    picks = picks_unicos

    # ======================
    # ORDENAR PICKS
    # ======================

    picks = sorted(
        picks,
        key=lambda x: x["value"],
        reverse=True
    )[:8]

    print(f"🔥 Picks finales: {len(picks)}")

    # ======================
    # MENSAJE
    # ======================

    mensaje = "🔥 PICKS DEL BOT 🔥\n\n"

    for p in picks:

        mensaje += (
            f"⚽ {p['match']}\n"
            f"🏆 {p['league']}\n"
            f"👉 {p['market']}\n"
            f"💰 Odd: {p['odd']}\n"
            f"📊 Prob: {round(p['prob'],2)}\n"
            f"🔥 Value: {round(p['value'],2)}\n"
            f"💵 Stake: {p['stake']}\n\n"
        )

    # ======================
    # ENVIAR
    # ======================

    if picks:

        enviar_telegram(mensaje)

        guardar(picks)

    else:
        print("⚠️ No hubo picks")

# ==============================
# START
# ==============================
if __name__ == "__main__":
    main()