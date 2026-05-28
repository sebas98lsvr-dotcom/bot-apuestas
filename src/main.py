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
    prob_under_25,
    prob_btts,
    calcular_value,
    calcular_stake_por_nivel
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
        "nivel",
        "stake",
        "resultado",
        "profit",
        "notificado",
        "version_estrategia",
        "contexto"
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
                "nivel": p.get("nivel", "NORMAL"),
                "stake": p["stake"],
                "resultado": "pendiente",
                "profit": 0,
                "notificado": "no",
                "version_estrategia": p.get(
                    "version_estrategia",
                    "multi_market_context_v6_under25_observacion"
                ),
                "contexto": p.get(
                    "contexto",
                    ""
                )
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

    # ==================================================
    # IMPORTANTE:
    # Estos filtros están calibrados con la fórmula real:
    #
    # score = (value * 100) + (prob * 10) + total_lambda
    #
    # Para Under 2.5 se usa:
    #
    # score = (value * 100) + (prob * 10) + ((3.0 - total_lambda) * 2)
    #
    # ==================================================

    if nivel_liga == "TOP":

        if mercado == "Over 1.5":
            return {
                "min_value": 0.035,
                "min_prob": 0.76,
                "min_lambda": 2.55,
                "min_odd": 1.30,
                "max_odd": 1.78,
                "min_score": 12.5
            }

        if mercado == "Over 2.5":
            return {
                "min_value": 0.025,
                "min_prob": 0.60,
                "min_lambda": 2.70,
                "min_odd": 1.55,
                "max_odd": 2.70,
                "min_score": 14
            }

        if mercado == "Under 2.5":
            return {
                "min_value": 0.035,
                "min_prob": 0.58,
                "max_lambda": 2.35,
                "min_odd": 1.55,
                "max_odd": 2.35,
                "min_score": 12.5,
            }

        if mercado == "BTTS":
            return {
                "min_value": 0.04,
                "min_prob": 0.60,
                "min_lambda": 2.50,
                "min_odd": 1.65,
                "max_odd": 2.35,
                "min_score": 14
            }

    if nivel_liga == "MEDIA":

        if mercado == "Over 1.5":
            return {
                "min_value": 0.04,
                "min_prob": 0.79,
                "min_lambda": 2.70,
                "min_odd": 1.35,
                "max_odd": 1.78,
                "min_score": 12.5
            }

        if mercado == "Over 2.5":
            return {
                "min_value": 0.045,
                "min_prob": 0.67,
                "min_lambda": 3.05,
                "min_odd": 1.65,
                "max_odd": 2.40,
                "min_score": 16
            }

        if mercado == "Under 2.5":
            return {
                "min_value": 0.04,
                "min_prob": 0.60,
                "max_lambda": 2.25,
                "min_odd": 1.60,
                "max_odd": 2.30,
                "min_score": 13.8
            }

        if mercado == "BTTS":
            return {
                "min_value": 0.045,
                "min_prob": 0.64,
                "min_lambda": 2.70,
                "min_odd": 1.70,
                "max_odd": 2.30,
                "min_score": 14.2
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
# VALIDAR OVER 1.5 CONTEXTO
# ==============================

def validar_over15_contexto(
    nivel_liga,
    lamL,
    lamV,
    total_lambda,
    prob_o15,
    odd,
    forma_home,
    forma_away
):

    razones = []

    if forma_home is None or forma_away is None:
        razones.append(
            "Sin forma reciente suficiente para validar Over 1.5"
        )
        return False, razones

    home_pj = forma_home.get("partidos", 0)
    away_pj = forma_away.get("partidos", 0)

    home_avg_total = forma_home.get("avg_total_goals", 0)
    away_avg_total = forma_away.get("avg_total_goals", 0)

    home_gf = forma_home.get("gf", 0)
    home_gc = forma_home.get("gc", 0)

    away_gf = forma_away.get("gf", 0)
    away_gc = forma_away.get("gc", 0)

    home_failed_to_score = forma_home.get("failed_to_score", 0)
    away_failed_to_score = forma_away.get("failed_to_score", 0)

    home_clean_sheets = forma_home.get("clean_sheets", 0)
    away_clean_sheets = forma_away.get("clean_sheets", 0)

    home_under25 = forma_home.get("under25", 0)
    away_under25 = forma_away.get("under25", 0)

    if home_pj < 4 or away_pj < 4:
        razones.append(
            f"Muestra baja Over 1.5: home {home_pj}, away {away_pj}"
        )

    if total_lambda < 2.55:
        razones.append(
            f"Lambda baja para Over 1.5: {round(total_lambda,2)}"
        )

    if nivel_liga == "MEDIA" and total_lambda < 2.70:
        razones.append(
            f"Lambda baja para Over 1.5 en liga media: {round(total_lambda,2)}"
        )

    if prob_o15 < 0.76:
        razones.append(
            f"Probabilidad baja para Over 1.5: {round(prob_o15,2)}"
        )

    if nivel_liga == "MEDIA" and prob_o15 < 0.79:
        razones.append(
            f"Probabilidad baja para Over 1.5 en liga media: {round(prob_o15,2)}"
        )

    if home_avg_total < 2.00 and away_avg_total < 2.00:
        razones.append(
            f"Promedio reciente bajo para Over 1.5: home {round(home_avg_total,2)}, away {round(away_avg_total,2)}"
        )

    if home_gf < 0.85 and away_gf < 0.85:
        razones.append(
            f"Ambos equipos marcan poco: home GF {round(home_gf,2)}, away GF {round(away_gf,2)}"
        )

    if home_gc < 0.75 and away_gc < 0.75:
        razones.append(
            f"Ambos equipos reciben poco: home GC {round(home_gc,2)}, away GC {round(away_gc,2)}"
        )

    if home_failed_to_score >= max(3, home_pj // 2) and away_failed_to_score >= max(3, away_pj // 2):
        razones.append(
            f"Ambos se quedan mucho sin marcar: home {home_failed_to_score}/{home_pj}, away {away_failed_to_score}/{away_pj}"
        )

    if home_clean_sheets >= max(3, home_pj // 2) and away_clean_sheets >= max(3, away_pj // 2):
        razones.append(
            f"Ambos con muchas porterías en cero: home {home_clean_sheets}/{home_pj}, away {away_clean_sheets}/{away_pj}"
        )

    if home_under25 >= max(5, home_pj - 1) and away_under25 >= max(5, away_pj - 1):
        razones.append(
            f"Ambos muy under 2.5: home {home_under25}/{home_pj}, away {away_under25}/{away_pj}"
        )

    if odd < 1.30:
        razones.append(
            f"Odd demasiado baja para Over 1.5: {odd}"
        )

    if razones:
        return False, razones

    contexto = (
        f"OK Over15 | "
        f"Lambda {round(total_lambda,2)} | "
        f"Prob {round(prob_o15,2)} | "
        f"Home avg {round(home_avg_total,2)} | "
        f"Away avg {round(away_avg_total,2)} | "
        f"Home GF {round(home_gf,2)} | "
        f"Away GF {round(away_gf,2)}"
    )

    return True, [contexto]

# ==============================
# VALIDAR OVER 2.5 CONTEXTO ESTRICTO
# ==============================

def validar_over25_contexto(
    nivel_liga,
    lamL,
    lamV,
    total_lambda,
    prob_o,
    odd,
    forma_home,
    forma_away
):

    razones = []

    if forma_home is None or forma_away is None:
        razones.append(
            "Sin forma reciente suficiente para validar Over 2.5"
        )
        return False, razones

    home_pj = forma_home.get("partidos", 0)
    away_pj = forma_away.get("partidos", 0)

    home_over25 = forma_home.get("over25", 0)
    away_over25 = forma_away.get("over25", 0)

    home_under25 = forma_home.get("under25", 0)
    away_under25 = forma_away.get("under25", 0)

    home_avg_total = forma_home.get("avg_total_goals", 0)
    away_avg_total = forma_away.get("avg_total_goals", 0)

    home_gf = forma_home.get("gf", 0)
    home_gc = forma_home.get("gc", 0)

    away_gf = forma_away.get("gf", 0)
    away_gc = forma_away.get("gc", 0)

    home_btts = forma_home.get("btts", 0)
    away_btts = forma_away.get("btts", 0)

    away_clean_sheets = forma_away.get("clean_sheets", 0)
    away_failed_to_score = forma_away.get("failed_to_score", 0)

    if home_pj < 4 or away_pj < 4:
        razones.append(
            f"Muestra baja: home {home_pj} partidos, away {away_pj} partidos"
        )

    if home_over25 <= 2 and away_over25 <= 2:
        razones.append(
            f"Ambos equipos con baja tendencia Over 2.5: home {home_over25}/{home_pj}, away {away_over25}/{away_pj}"
        )

    if home_over25 <= 2 and away_over25 <= 4 and total_lambda < 3.30:
        razones.append(
            f"Local muy under para Over 2.5 y lambda no premium: home {home_over25}/{home_pj}, away {away_over25}/{away_pj}, lambda {round(total_lambda,2)}"
        )

    if nivel_liga == "MEDIA":

        if home_over25 <= 3 and away_over25 <= 3:
            razones.append(
                f"Liga media con tendencia Over 2.5 débil: home {home_over25}/{home_pj}, away {away_over25}/{away_pj}"
            )

        if total_lambda < 2.95:
            razones.append(
                f"Lambda justa para Over 2.5 en liga media: {round(total_lambda, 2)}"
            )

        if prob_o < 0.64:
            razones.append(
                f"Probabilidad baja para Over 2.5 en liga media: {round(prob_o, 2)}"
            )

    if home_avg_total < 2.30 and away_avg_total < 2.30:
        razones.append(
            f"Promedio reciente de goles bajo: home {round(home_avg_total,2)}, away {round(away_avg_total,2)}"
        )

    if away_gc <= 0.90 and away_over25 <= 3:
        razones.append(
            f"Visitante defensivo: GC away {round(away_gc,2)} y Over 2.5 {away_over25}/{away_pj}"
        )

    if away_clean_sheets >= max(2, away_pj // 2):
        razones.append(
            f"Visitante con muchas porterías en cero: {away_clean_sheets}/{away_pj}"
        )

    if lamV < 0.95:
        razones.append(
            f"Lambda visitante baja para Over 2.5: {round(lamV,2)}"
        )

    if away_gf < 0.85:
        razones.append(
            f"Visitante marca poco fuera: GF away {round(away_gf,2)}"
        )

    if away_failed_to_score >= max(2, away_pj // 2):
        razones.append(
            f"Visitante se queda mucho sin marcar: {away_failed_to_score}/{away_pj}"
        )

    if lamL >= 2.10 and lamV < 0.80:
        razones.append(
            f"Over 2.5 depende demasiado del local: lamL {round(lamL,2)}, lamV {round(lamV,2)}"
        )

    if home_btts <= 1 and away_btts <= 1:
        razones.append(
            f"BTTS reciente muy bajo: home {home_btts}/{home_pj}, away {away_btts}/{away_pj}"
        )

    if home_under25 >= max(3, home_pj - 1) and away_under25 >= max(3, away_pj - 1):
        razones.append(
            f"Ambos equipos con muchos Under 2.5: home {home_under25}/{home_pj}, away {away_under25}/{away_pj}"
        )

    if razones:
        return False, razones

    contexto = (
        f"OK Over25 | "
        f"Home O2.5 {home_over25}/{home_pj} | "
        f"Away O2.5 {away_over25}/{away_pj} | "
        f"Home avg {round(home_avg_total,2)} | "
        f"Away avg {round(away_avg_total,2)} | "
        f"Away GC {round(away_gc,2)}"
    )

    return True, [contexto]

# ==============================
# VALIDAR UNDER 2.5 CONTEXTO
# ==============================

def validar_under25_contexto(
    nivel_liga,
    lamL,
    lamV,
    total_lambda,
    prob_u25,
    odd,
    forma_home,
    forma_away
):

    razones = []

    if forma_home is None or forma_away is None:
        razones.append(
            "Sin forma reciente suficiente para validar Under 2.5"
        )
        return False, razones

    home_pj = forma_home.get("partidos", 0)
    away_pj = forma_away.get("partidos", 0)

    home_over25 = forma_home.get("over25", 0)
    away_over25 = forma_away.get("over25", 0)

    home_under25 = forma_home.get("under25", 0)
    away_under25 = forma_away.get("under25", 0)

    home_avg_total = forma_home.get("avg_total_goals", 0)
    away_avg_total = forma_away.get("avg_total_goals", 0)

    home_gf = forma_home.get("gf", 0)
    home_gc = forma_home.get("gc", 0)

    away_gf = forma_away.get("gf", 0)
    away_gc = forma_away.get("gc", 0)

    home_btts = forma_home.get("btts", 0)
    away_btts = forma_away.get("btts", 0)

    home_clean_sheets = forma_home.get("clean_sheets", 0)
    away_clean_sheets = forma_away.get("clean_sheets", 0)

    home_failed_to_score = forma_home.get("failed_to_score", 0)
    away_failed_to_score = forma_away.get("failed_to_score", 0)

    if home_pj < 4 or away_pj < 4:
        razones.append(
            f"Muestra baja Under 2.5: home {home_pj}, away {away_pj}"
        )

    if nivel_liga == "TOP":

        if total_lambda > 2.35:
            razones.append(
                f"Lambda alta para Under 2.5 en liga TOP: {round(total_lambda,2)}"
            )

        if prob_u25 < 0.58:
            razones.append(
                f"Probabilidad baja para Under 2.5 en liga TOP: {round(prob_u25,2)}"
            )

    if nivel_liga == "MEDIA":

        if total_lambda > 2.25:
            razones.append(
                f"Lambda alta para Under 2.5 en liga media: {round(total_lambda,2)}"
            )

        if prob_u25 < 0.60:
            razones.append(
                f"Probabilidad baja para Under 2.5 en liga media: {round(prob_u25,2)}"
            )

    if lamL >= 1.75:
        razones.append(
            f"Lambda local alta para Under 2.5: {round(lamL,2)}"
        )

    if lamV >= 1.75:
        razones.append(
            f"Lambda visitante alta para Under 2.5: {round(lamV,2)}"
        )

    if home_over25 >= max(5, home_pj - 2) and away_over25 >= max(5, away_pj - 2):
        razones.append(
            f"Ambos equipos vienen muy Over 2.5: home {home_over25}/{home_pj}, away {away_over25}/{away_pj}"
        )

    if home_avg_total >= 2.80 and away_avg_total >= 2.80:
        razones.append(
            f"Promedios recientes altos contra Under 2.5: home {round(home_avg_total,2)}, away {round(away_avg_total,2)}"
        )

    if home_gf >= 1.75 and away_gf >= 1.50:
        razones.append(
            f"Ataques fuertes contra Under 2.5: home GF {round(home_gf,2)}, away GF {round(away_gf,2)}"
        )

    if home_gc >= 1.80 and away_gc >= 1.80:
        razones.append(
            f"Defensas débiles contra Under 2.5: home GC {round(home_gc,2)}, away GC {round(away_gc,2)}"
        )

    if home_btts >= max(5, home_pj - 2) and away_btts >= max(5, away_pj - 2):
        razones.append(
            f"BTTS reciente alto contra Under 2.5: home {home_btts}/{home_pj}, away {away_btts}/{away_pj}"
        )

    # Señales positivas mínimas.
    señales_under = 0

    if home_under25 >= max(4, home_pj // 2):
        señales_under += 1

    if away_under25 >= max(4, away_pj // 2):
        señales_under += 1

    if home_avg_total <= 2.25:
        señales_under += 1

    if away_avg_total <= 2.25:
        señales_under += 1

    if home_gf <= 1.20:
        señales_under += 1

    if away_gf <= 1.20:
        señales_under += 1

    if home_gc <= 1.20:
        señales_under += 1

    if away_gc <= 1.20:
        señales_under += 1

    if home_btts <= max(3, home_pj // 2):
        señales_under += 1

    if away_btts <= max(3, away_pj // 2):
        señales_under += 1

    if home_clean_sheets >= 2 or away_clean_sheets >= 2:
        señales_under += 1

    if home_failed_to_score >= 2 or away_failed_to_score >= 2:
        señales_under += 1

    if señales_under < 4:
        razones.append(
            f"Pocas señales reales de Under 2.5: {señales_under}"
        )

    if odd < 1.55:
        razones.append(
            f"Odd demasiado baja para Under 2.5: {odd}"
        )

    if odd > 2.35:
        razones.append(
            f"Odd demasiado alta/riesgosa para Under 2.5: {odd}"
        )

    if razones:
        return False, razones

    contexto = (
        f"OK Under25 | "
        f"Home U2.5 {home_under25}/{home_pj} | "
        f"Away U2.5 {away_under25}/{away_pj} | "
        f"Home avg {round(home_avg_total,2)} | "
        f"Away avg {round(away_avg_total,2)} | "
        f"Home GF {round(home_gf,2)} | "
        f"Away GF {round(away_gf,2)} | "
        f"Home GC {round(home_gc,2)} | "
        f"Away GC {round(away_gc,2)} | "
        f"BTTS H/A {home_btts}/{home_pj}-{away_btts}/{away_pj}"
    )

    return True, [contexto]

# ==============================
# VALIDAR BTTS CONTEXTO ESTRICTO
# ==============================

def validar_btts_contexto(
    nivel_liga,
    lamL,
    lamV,
    total_lambda,
    prob_b,
    odd,
    forma_home,
    forma_away
):

    razones = []

    if forma_home is None or forma_away is None:
        razones.append(
            "Sin forma reciente suficiente para validar BTTS"
        )
        return False, razones

    home_pj = forma_home.get("partidos", 0)
    away_pj = forma_away.get("partidos", 0)

    home_btts = forma_home.get("btts", 0)
    away_btts = forma_away.get("btts", 0)

    home_gf = forma_home.get("gf", 0)
    home_gc = forma_home.get("gc", 0)

    away_gf = forma_away.get("gf", 0)
    away_gc = forma_away.get("gc", 0)

    home_avg_total = forma_home.get("avg_total_goals", 0)
    away_avg_total = forma_away.get("avg_total_goals", 0)

    home_clean_sheets = forma_home.get("clean_sheets", 0)
    away_clean_sheets = forma_away.get("clean_sheets", 0)

    home_failed_to_score = forma_home.get("failed_to_score", 0)
    away_failed_to_score = forma_away.get("failed_to_score", 0)

    if home_pj < 4 or away_pj < 4:
        razones.append(
            f"Muestra baja BTTS: home {home_pj} partidos, away {away_pj} partidos"
        )

    if lamL < 1.00:
        razones.append(
            f"Lambda local baja para BTTS: {round(lamL, 2)}"
        )

    if lamV < 1.00:
        razones.append(
            f"Lambda visitante baja para BTTS: {round(lamV, 2)}"
        )

    if total_lambda < 2.50:
        razones.append(
            f"Lambda total baja para BTTS: {round(total_lambda,2)}"
        )

    if nivel_liga == "MEDIA" and total_lambda < 2.70:
        razones.append(
            f"Lambda total baja para BTTS en liga media: {round(total_lambda,2)}"
        )

    if abs(lamL - lamV) > 1.20:
        razones.append(
            f"BTTS desbalanceado por lambdas: local {round(lamL,2)}, visitante {round(lamV,2)}"
        )

    if home_btts <= 2 and away_btts <= 2:
        razones.append(
            f"Ambos equipos con baja tendencia BTTS: home {home_btts}/{home_pj}, away {away_btts}/{away_pj}"
        )

    if nivel_liga == "MEDIA" and home_btts <= 3 and away_btts <= 3:
        razones.append(
            f"Liga media con BTTS débil: home {home_btts}/{home_pj}, away {away_btts}/{away_pj}"
        )

    if home_gf < 1.00:
        razones.append(
            f"Local marca poco en casa: GF home {round(home_gf,2)}"
        )

    if away_gf < 1.00:
        razones.append(
            f"Visitante marca poco fuera: GF away {round(away_gf,2)}"
        )

    if home_failed_to_score >= max(2, home_pj // 2):
        razones.append(
            f"Local se queda mucho sin marcar: {home_failed_to_score}/{home_pj}"
        )

    if away_failed_to_score >= max(2, away_pj // 2):
        razones.append(
            f"Visitante se queda mucho sin marcar: {away_failed_to_score}/{away_pj}"
        )

    if home_gc < 0.80:
        razones.append(
            f"Local recibe poco en casa: GC home {round(home_gc,2)}"
        )

    if away_gc < 0.80:
        razones.append(
            f"Visitante recibe poco fuera: GC away {round(away_gc,2)}"
        )

    if home_clean_sheets >= max(2, home_pj // 2):
        razones.append(
            f"Local con muchas porterías en cero: {home_clean_sheets}/{home_pj}"
        )

    if away_clean_sheets >= max(2, away_pj // 2):
        razones.append(
            f"Visitante con muchas porterías en cero: {away_clean_sheets}/{away_pj}"
        )

    if home_avg_total < 2.10 and away_avg_total < 2.10:
        razones.append(
            f"Promedio total bajo para BTTS: home {round(home_avg_total,2)}, away {round(away_avg_total,2)}"
        )

    if nivel_liga == "MEDIA" and prob_b < 0.64:
        razones.append(
            f"Probabilidad BTTS baja en liga media: {round(prob_b,2)}"
        )

    if nivel_liga == "TOP" and prob_b < 0.60:
        razones.append(
            f"Probabilidad BTTS baja en liga TOP: {round(prob_b,2)}"
        )

    if odd < 1.65:
        razones.append(
            f"Odd BTTS demasiado baja: {odd}"
        )

    if odd > 2.35:
        razones.append(
            f"Odd BTTS demasiado alta/riesgosa: {odd}"
        )

    if razones:
        return False, razones

    contexto = (
        f"OK BTTS | "
        f"Home BTTS {home_btts}/{home_pj} | "
        f"Away BTTS {away_btts}/{away_pj} | "
        f"Home GF {round(home_gf,2)} | "
        f"Away GF {round(away_gf,2)} | "
        f"Home GC {round(home_gc,2)} | "
        f"Away GC {round(away_gc,2)}"
    )

    return True, [contexto]

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
            return None, None, None, None

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
                min(lam_visit, 3.2),
                None,
                None
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
            f"| Home O2.5: {forma_home.get('over25', 0)}/{forma_home['partidos']} "
            f"| Home U2.5: {forma_home.get('under25', 0)}/{forma_home['partidos']} "
            f"| Away GF: {round(forma_away['gf'],2)} "
            f"| Away GC: {round(forma_away['gc'],2)} "
            f"| Away PJ: {forma_away['partidos']} "
            f"| Away O2.5: {forma_away.get('over25', 0)}/{forma_away['partidos']} "
            f"| Away U2.5: {forma_away.get('under25', 0)}/{forma_away['partidos']}"
        )

        return (
            min(lam_local, 3.2),
            min(lam_visit, 3.2),
            forma_home,
            forma_away
        )

    except Exception as e:

        print("❌ Error lambdas:", e)

        return None, None, None, None

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

            lamL, lamV, forma_home, forma_away = calcular_lambdas(p)

            if lamL is None:
                print(f"⚠️ Sin lambdas/stats suficientes: {local} vs {visitante}")
                continue

            total_lambda = lamL + lamV

            print(
                f"📊 Lambdas | Local: {round(lamL,2)} "
                f"| Visitante: {round(lamV,2)} "
                f"| Total: {round(total_lambda,2)}"
            )

            # Antes se descartaba todo con lambda < 2.1.
            # Ahora NO hacemos ese descarte global porque Under 2.5
            # precisamente puede vivir en lambdas bajas.
            # Los mercados Over/BTTS ya tienen sus propios filtros.

            prob_o = prob_over_25(
                lamL,
                lamV
            )

            prob_u25 = prob_under_25(
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
                f"| Under 2.5: {round(prob_u25,2)} "
                f"| BTTS: {round(prob_b,2)}"
            )

            picks_partido = []

            for b in bets:

                # ==============================
                # GOALS OVER/UNDER
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
                                    (val * 70)
                                    + (prob_o15 * 10)
                                    + total_lambda
                                )

                                ok_contexto_o15, razones_contexto_o15 = validar_over15_contexto(
                                    nivel_liga,
                                    lamL,
                                    lamV,
                                    total_lambda,
                                    prob_o15,
                                    odd,
                                    forma_home,
                                    forma_away
                                )

                                if not ok_contexto_o15:
                                    print(
                                        f"⛔ Over 1.5 bloqueado por contexto "
                                        f"| {local} vs {visitante}"
                                    )

                                    for razon in razones_contexto_o15:
                                        print(f"   - {razon}")

                                    continue

                                contexto_o15_ok = " | ".join(
                                    razones_contexto_o15
                                )

                                if (
                                    val > filtros["min_value"]
                                    and prob_o15 > filtros["min_prob"]
                                    and total_lambda > filtros["min_lambda"]
                                    and filtros["min_odd"] <= odd <= filtros["max_odd"]
                                ):

                                    nivel_pick, stake = calcular_stake_por_nivel(
                                        mercado="Over 1.5",
                                        score=score,
                                        prob=prob_o15,
                                        value=val,
                                        odd=odd,
                                        total_lambda=total_lambda,
                                        nivel_liga=nivel_liga
                                    )

                                    if nivel_pick == "DESCARTADA":
                                        print(
                                            f"⛔ Over 1.5 descartado por nivel "
                                            f"| Nivel liga: {nivel_liga} "
                                            f"| Odd: {odd} "
                                            f"| Prob: {round(prob_o15,2)} "
                                            f"| Value: {round(val,2)} "
                                            f"| Score: {round(score,2)}"
                                        )
                                        continue

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
                                        f"| Score: {round(score,2)} "
                                        f"| Nivel pick: {nivel_pick} "
                                        f"| Stake: {stake} "
                                        f"| Contexto: {contexto_o15_ok}"
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
                                        "nivel": nivel_pick,
                                        "stake": stake,
                                        "version_estrategia": "multi_market_context_v6_under25_observacion",
                                        "contexto": contexto_o15_ok
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
                                    (val * 70)
                                    + (prob_o * 10)
                                    + total_lambda
                                )

                                # Over 2.5 premium
                                score -= 1.0

                                if odd < 1.60:

                                    if nivel_liga == "TOP" and prob_o < 0.70:
                                        print(
                                            f"⛔ Over 2.5 descartado por cuota baja sin probabilidad premium "
                                            f"| Nivel: {nivel_liga} "
                                            f"| Odd: {odd} "
                                            f"| Prob: {round(prob_o,2)} "
                                            f"| Prob mínima premium: 0.70"
                                        )
                                        continue

                                    if nivel_liga == "MEDIA":
                                        print(
                                            f"⛔ Over 2.5 descartado por cuota baja en liga media "
                                            f"| Nivel: {nivel_liga} "
                                            f"| Odd: {odd}"
                                        )
                                        continue

                                ok_contexto, razones_contexto = validar_over25_contexto(
                                    nivel_liga,
                                    lamL,
                                    lamV,
                                    total_lambda,
                                    prob_o,
                                    odd,
                                    forma_home,
                                    forma_away
                                )

                                if not ok_contexto:
                                    print(
                                        f"⛔ Over 2.5 bloqueado por contexto "
                                        f"| {local} vs {visitante}"
                                    )

                                    for razon in razones_contexto:
                                        print(f"   - {razon}")

                                    continue

                                contexto_ok = " | ".join(
                                    razones_contexto
                                )

                                if (
                                    val > filtros["min_value"]
                                    and prob_o > filtros["min_prob"]
                                    and total_lambda > filtros["min_lambda"]
                                    and filtros["min_odd"] <= odd <= filtros["max_odd"]
                                ):

                                    nivel_pick, stake = calcular_stake_por_nivel(
                                        mercado="Over 2.5",
                                        score=score,
                                        prob=prob_o,
                                        value=val,
                                        odd=odd,
                                        total_lambda=total_lambda,
                                        nivel_liga=nivel_liga
                                    )

                                    # Reducir exposición Over 2.5
                                    stake = round(stake * 0.70, 2)

                                    if nivel_pick == "DESCARTADA":
                                        print(
                                            f"⛔ Over 2.5 descartado por nivel "
                                            f"| Nivel liga: {nivel_liga} "
                                            f"| Odd: {odd} "
                                            f"| Prob: {round(prob_o,2)} "
                                            f"| Value: {round(val,2)} "
                                            f"| Score: {round(score,2)}"
                                        )
                                        continue

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
                                        f"| Score: {round(score,2)} "
                                        f"| Nivel pick: {nivel_pick} "
                                        f"| Stake: {stake} "
                                        f"| Contexto: {contexto_ok}"
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
                                        "nivel": nivel_pick,
                                        "stake": stake,
                                        "version_estrategia": "multi_market_context_v6_under25_observacion",
                                        "contexto": contexto_ok
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

                        # UNDER 2.5

                        if v["value"] == "Under 2.5":

                            try:

                                odd = float(v["odd"])

                                val = calcular_value(
                                    prob_u25,
                                    odd
                                )

                                filtros = obtener_filtros_mercado(
                                    nivel_liga,
                                    "Under 2.5"
                                )

                                if filtros is None:
                                    print(
                                        f"⛔ Sin filtros para Under 2.5 "
                                        f"| Nivel liga: {nivel_liga}"
                                    )
                                    continue

                                score = (
                                    (val * 70)
                                    + (prob_u25 * 10)
                                    + ((3.0 - total_lambda) * 2)
                                )

                                ok_under_contexto, razones_under_contexto = validar_under25_contexto(
                                    nivel_liga,
                                    lamL,
                                    lamV,
                                    total_lambda,
                                    prob_u25,
                                    odd,
                                    forma_home,
                                    forma_away
                                )

                                if not ok_under_contexto:
                                    print(
                                        f"⛔ Under 2.5 bloqueado por contexto "
                                        f"| {local} vs {visitante}"
                                    )

                                    for razon in razones_under_contexto:
                                        print(f"   - {razon}")

                                    continue

                                contexto_under_ok = " | ".join(
                                    razones_under_contexto
                                )

                                if (
                                    val > filtros["min_value"]
                                    and prob_u25 > filtros["min_prob"]
                                    and total_lambda <= filtros["max_lambda"]
                                    and filtros["min_odd"] <= odd <= filtros["max_odd"]
                                ):

                                    nivel_pick, stake = calcular_stake_por_nivel(
                                        mercado="Under 2.5",
                                        score=score,
                                        prob=prob_u25,
                                        value=val,
                                        odd=odd,
                                        total_lambda=total_lambda,
                                        nivel_liga=nivel_liga
                                    )

                                    if nivel_pick == "DESCARTADA":
                                        print(
                                            f"⛔ Under 2.5 descartado por nivel "
                                            f"| Nivel liga: {nivel_liga} "
                                            f"| Odd: {odd} "
                                            f"| Prob: {round(prob_u25,2)} "
                                            f"| Value: {round(val,2)} "
                                            f"| Score: {round(score,2)} "
                                            f"| Lambda: {round(total_lambda,2)}"
                                        )
                                        continue

                                    if score < filtros["min_score"]:
                                        print(
                                            f"⛔ Under 2.5 descartado por score bajo "
                                            f"| Nivel: {nivel_liga} "
                                            f"| Odd: {odd} "
                                            f"| Value: {round(val,2)} "
                                            f"| Score: {round(score,2)} "
                                            f"| Score mínimo: {filtros['min_score']}"
                                        )
                                        continue

                                    print(
                                        f"✅ Candidato Under 2.5 "
                                        f"| Nivel: {nivel_liga} "
                                        f"| Odd: {odd} "
                                        f"| Prob: {round(prob_u25,2)} "
                                        f"| Value: {round(val,2)} "
                                        f"| Score: {round(score,2)} "
                                        f"| Nivel pick: {nivel_pick} "
                                        f"| Stake: {stake} "
                                        f"| Contexto: {contexto_under_ok}"
                                    )

                                    picks_partido.append({

                                        "fixture_id": fixture_id,
                                        "date": fecha_partido,
                                        "match": f"{local} vs {visitante}",
                                        "league": league_name,
                                        "market": "Under 2.5",
                                        "odd": odd,
                                        "prob": prob_u25,
                                        "value": val,
                                        "score": round(score, 2),
                                        "nivel": nivel_pick,
                                        "stake": stake,
                                        "version_estrategia": "multi_market_context_v6_under25_observacion",
                                        "contexto": contexto_under_ok
                                    })

                                else:
                                    print(
                                        f"❌ Under 2.5 no cumple filtros "
                                        f"| Nivel: {nivel_liga} "
                                        f"| Odd: {odd} "
                                        f"| Prob: {round(prob_u25,2)} "
                                        f"| Value: {round(val,2)} "
                                        f"| Lambda: {round(total_lambda,2)}"
                                    )

                            except Exception as e:
                                print("⚠️ Error evaluando Under 2.5:", e)
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
                                    (val * 70)
                                    + (prob_b * 10)
                                    + total_lambda
                                )

                                ok_btts_contexto, razones_btts_contexto = validar_btts_contexto(
                                    nivel_liga,
                                    lamL,
                                    lamV,
                                    total_lambda,
                                    prob_b,
                                    odd,
                                    forma_home,
                                    forma_away
                                )

                                if not ok_btts_contexto:
                                    print(
                                        f"⛔ BTTS bloqueado por contexto "
                                        f"| {local} vs {visitante}"
                                    )

                                    for razon in razones_btts_contexto:
                                        print(f"   - {razon}")

                                    continue

                                contexto_btts_ok = " | ".join(
                                    razones_btts_contexto
                                )

                                if (
                                    val > filtros["min_value"]
                                    and prob_b > filtros["min_prob"]
                                    and total_lambda > filtros["min_lambda"]
                                    and filtros["min_odd"] <= odd <= filtros["max_odd"]
                                ):

                                    nivel_pick, stake = calcular_stake_por_nivel(
                                        mercado="BTTS",
                                        score=score,
                                        prob=prob_b,
                                        value=val,
                                        odd=odd,
                                        total_lambda=total_lambda,
                                        nivel_liga=nivel_liga
                                    )

                                    if nivel_pick == "DESCARTADA":
                                        print(
                                            f"⛔ BTTS descartado por nivel "
                                            f"| Nivel liga: {nivel_liga} "
                                            f"| Odd: {odd} "
                                            f"| Prob: {round(prob_b,2)} "
                                            f"| Value: {round(val,2)} "
                                            f"| Score: {round(score,2)}"
                                        )
                                        continue

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
                                        f"| Score: {round(score,2)} "
                                        f"| Nivel pick: {nivel_pick} "
                                        f"| Stake: {stake} "
                                        f"| Contexto: {contexto_btts_ok}"
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
                                        "nivel": nivel_pick,
                                        "stake": stake,
                                        "version_estrategia": "multi_market_context_v6_under25_observacion",
                                        "contexto": contexto_btts_ok
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
                    f"| Score: {round(mejor_pick['score'],2)} "
                    f"| Nivel: {mejor_pick.get('nivel', 'NORMAL')} "
                    f"| Stake: {mejor_pick['stake']}"
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
    # Nota:
    # No limitamos a pocas picks por miedo al volumen.
    # La calidad debe venir de los filtros, contexto, nivel y stake.
    # Se permiten hasta 20 picks si realmente cumplen los criterios.

    picks = sorted(

        picks,

        key=lambda x: x["score"],

        reverse=True

    )[:20]

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

        # ==============================
        # MARCAR FIXTURES COMO ENVIADOS
        # SOLO DESPUÉS DE GUARDAR
        # ==============================

        with open(
            RUTA_ENVIADOS,
            "a"
        ) as f:

            for p in picks:

                fixture_id = str(
                    p["fixture_id"]
                )

                if fixture_id not in ENVIADOS:

                    f.write(
                        fixture_id + "\n"
                    )

                    ENVIADOS.add(
                        fixture_id
                    )

        print("🧾 enviados.txt actualizado después de guardar picks")

    else:

        print(
            "⚠️ No hubo picks nuevas"
        )

# ==============================
# START
# ==============================

if __name__ == "__main__":

    main()