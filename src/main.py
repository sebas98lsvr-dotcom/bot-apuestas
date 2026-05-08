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

# crear archivo si no existe
if not os.path.exists(RUTA_ENVIADOS):

    with open(RUTA_ENVIADOS, "w") as f:
        pass

# cargar enviados
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
        "profit"
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

        # escribir header solo si vacío
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

        "Premier League",
        "La Liga",
        "Bundesliga",
        "Serie A",
        "Ligue 1",
        "Eredivisie",
        "Primeira Liga",

        "Championship",
        "2. Bundesliga",

        "Liga Profesional Argentina",

        "Primera B",
        "Copa Colombia",

        "CONMEBOL Libertadores",
        "CONMEBOL Sudamericana"
    ]

    picks = []

    for p in partidos:

        try:

            if p["fixture"]["status"]["short"] != "NS":
                continue

            fixture_id = str(
                p["fixture"]["id"]
            )

            # ======================
            # NO REPETIR PICKS
            # ======================

            if fixture_id in ENVIADOS:
                continue

            fecha_partido = (
                p["fixture"]["date"][:16]
                .replace("T", " ")
            )

            local = p["teams"]["home"]["name"]
            visitante = p["teams"]["away"]["name"]

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

            # ======================
            # FILTRO OFENSIVO
            # ======================

            total_lambda = lamL + lamV

            # evitar partidos cerrados
            if total_lambda < 2.4:
                continue

            prob_o = prob_over_25(lamL, lamV)
            prob_b = prob_btts(lamL, lamV)

            picks_partido = []

            for b in bets:

                # ======================
                # OVER 2.5
                # ======================

                if b["name"] == "Goals Over/Under":

                    for v in b["values"]:

                        if v["value"] == "Over 2.5":

                            try:

                                odd = float(v["odd"])

                                val = calcular_value(
                                    prob_o,
                                    odd
                                )

                                if (
                                    val > 0.06
                                    and prob_o > 0.60
                                    and total_lambda > 2.8
                                    and 1.70 <= odd <= 2.80
                                ):

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

                # ======================
                # BTTS
                # ======================

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
                                    val > 0.05
                                    and prob_b > 0.58
                                    and total_lambda > 2.6
                                    and 1.70 <= odd <= 2.60
                                ):

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

            # ======================
            # GUARDAR ENVIADOS
            # ======================

            if picks_partido:

                picks.extend(picks_partido)

                with open(
                    RUTA_ENVIADOS,
                    "a"
                ) as f:

                    f.write(
                        fixture_id + "\n"
                    )

        except Exception as e:
            print("❌ Error partido:", e)

    # ======================
    # ELIMINAR DUPLICADOS
    # ======================

    picks_unicos = {}

    for p in picks:

        clave = (
            p["match"]
            + "_"
            + p["market"]
        )

        # guardar solo mejor odd
        if (
            clave not in picks_unicos
            or p["odd"] > picks_unicos[clave]["odd"]
        ):

            picks_unicos[clave] = p

    # convertir nuevamente a lista
    picks = list(
        picks_unicos.values()
    )

    # ======================
    # ORDENAR PICKS
    # ======================

    picks = sorted(
        picks,
        key=lambda x: x["value"],
        reverse=True
    )[:5]

    print(f"🔥 Picks finales: {len(picks)}")

    # ======================
    # TELEGRAM
    # ======================

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

    # ======================
    # ENVIAR
    # ======================

    if picks:

        enviar_telegram(mensaje)

        guardar(picks)

    else:
        print("⚠️ No hubo picks nuevos")

# ==============================
# START
# ==============================

if __name__ == "__main__":
    main()