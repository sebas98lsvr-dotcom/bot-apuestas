import requests
import os
from dotenv import load_dotenv

# =========================
# CARGAR ENV
# =========================

ruta_env = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(ruta_env)

API_KEY = os.getenv("API_FOOTBALL_KEY")

HEADERS = {
    "x-apisports-key": API_KEY
}

BASE_URL = "https://v3.football.api-sports.io"

# =========================
# BOOKMAKERS CONFIABLES
# =========================

BOOKMAKERS_VALIDOS = [
    "Bet365",
    "1xBet",
    "Betano",
    "Bwin",
    "William Hill"
]

# =========================
# VALIDAR ODDS
# =========================

def odd_valida(odd):

    try:

        odd = float(odd)

        # evitar cuotas absurdas
        return 1.20 <= odd <= 8

    except:
        return False

# =========================
# OBTENER ODDS LIMPIAS
# =========================

def obtener_odds(fixture_id):

    try:

        url = f"{BASE_URL}/odds"

        params = {
            "fixture": fixture_id
        }

        r = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=20
        )

        if r.status_code != 200:
            return []

        data = r.json().get("response", [])

        odds_limpias = []

        # =========================
        # LIMPIAR BOOKMAKERS
        # =========================

        for item in data:

            bookmakers = item.get(
                "bookmakers",
                []
            )

            for book in bookmakers:

                nombre_book = book.get(
                    "name",
                    ""
                )

                # ignorar books raras
                if nombre_book not in BOOKMAKERS_VALIDOS:
                    continue

                bets = book.get(
                    "bets",
                    []
                )

                bets_limpias = []

                for bet in bets:

                    valores = bet.get(
                        "values",
                        []
                    )

                    valores_validos = []

                    for v in valores:

                        odd = v.get("odd")

                        if not odd_valida(odd):
                            continue

                        valores_validos.append(v)

                    # ignorar mercado vacío
                    if valores_validos:

                        bet["values"] = valores_validos
                        bets_limpias.append(bet)

                # ignorar bookmaker vacío
                if bets_limpias:

                    book["bets"] = bets_limpias
                    odds_limpias.append(book)

        print(
            f"💰 Odds válidas: {len(odds_limpias)}"
        )

        return odds_limpias

    except Exception as e:

        print("💥 Error odds:", e)

        return []