import os
import pandas as pd
from flask import Flask, render_template

app = Flask(__name__)

# =========================
# RUTA CSV
# =========================

BASE_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)

ruta_csv = os.path.join(
    BASE_DIR,
    "picks.csv"
)

print("📂 CSV:", ruta_csv)

# =========================
# HOME
# =========================

@app.route("/")
def home():

    try:

        df = pd.read_csv(ruta_csv)

    except Exception as e:

        print("Error CSV:", e)

        df = pd.DataFrame()

    # =========================
    # VARIABLES
    # =========================

    total = len(df)

    wins = 0
    losses = 0
    pendientes = 0

    profit = 0
    stake_total = 0

    score_promedio = 0

    historial = []
    top_picks = []

    # =========================
    # ESTADISTICAS
    # =========================

    if not df.empty:

        wins = len(
            df[df["resultado"] == "win"]
        )

        losses = len(
            df[df["resultado"] == "loss"]
        )

        pendientes = len(
            df[df["resultado"] == "pendiente"]
        )

        # =========================
        # SOLO PICKS CERRADAS
        # =========================

        cerradas = df[
            df["resultado"] != "pendiente"
        ]

        profit = round(
            cerradas["profit"].sum(),
            2
        )

        stake_total = round(
            cerradas["stake"].sum(),
            2
        )

        # =========================
        # SCORE PROMEDIO
        # =========================

        if "score" in df.columns:

            score_promedio = round(
                df["score"].mean(),
                2
            )

        # =========================
        # HISTORIAL
        # =========================

        historial = df.sort_values(
            by="fecha",
            ascending=False
        ).fillna("").to_dict(
            orient="records"
        )

        # =========================
        # TOP PICKS
        # =========================

        if "score" in df.columns:

            top_picks = df.sort_values(
                by="score",
                ascending=False
            ).head(10).fillna("").to_dict(
                orient="records"
            )

    # =========================
    # WINRATE
    # =========================

    if (wins + losses) > 0:

        winrate = round(
            (wins / (wins + losses)) * 100,
            2
        )

    else:

        winrate = 0

    # =========================
    # ROI REAL
    # =========================

    if stake_total > 0:

        roi = round(
            (profit / stake_total) * 100,
            2
        )

    else:

        roi = 0

    # =========================
    # MERCADOS
    # =========================

    mercados = []

    if not df.empty:

        for mercado in df["mercado"].unique():

            d = df[
                df["mercado"] == mercado
            ]

            total_m = len(d)

            w = len(
                d[d["resultado"] == "win"]
            )

            l = len(
                d[d["resultado"] == "loss"]
            )

            if (w + l) > 0:

                wr = round(
                    (w / (w + l)) * 100,
                    2
                )

            else:

                wr = 0

            profit_m = round(
                d["profit"].sum(),
                2
            )

            mercados.append({

                "mercado": mercado,
                "total": total_m,
                "winrate": wr,
                "profit": profit_m
            })

    # =========================
    # LIGAS
    # =========================

    ligas = []

    if not df.empty:

        for liga in df["liga"].unique():

            d = df[
                df["liga"] == liga
            ]

            total_l = len(d)

            w = len(
                d[d["resultado"] == "win"]
            )

            l = len(
                d[d["resultado"] == "loss"]
            )

            if (w + l) > 0:

                wr = round(
                    (w / (w + l)) * 100,
                    2
                )

            else:

                wr = 0

            profit_l = round(
                d["profit"].sum(),
                2
            )

            ligas.append({

                "liga": liga,
                "total": total_l,
                "winrate": wr,
                "profit": profit_l
            })

    # =========================
    # GRAFICA PROFIT
    # =========================

    profits = []

    if not df.empty:

        df["profit_acumulado"] = (
            df["profit"].cumsum()
        )

        profits = df[
            "profit_acumulado"
        ].tolist()

    # =========================
    # GRAFICA WINRATE
    # =========================

    winrates = []

    if not df.empty:

        acumulado_w = 0
        acumulado_total = 0

        for _, row in df.iterrows():

            if row["resultado"] == "win":

                acumulado_w += 1

            if row["resultado"] != "pendiente":

                acumulado_total += 1

            if acumulado_total > 0:

                wr = (
                    acumulado_w
                    / acumulado_total
                ) * 100

            else:

                wr = 0

            winrates.append(
                round(wr, 2)
            )

    # =========================
    # STATS
    # =========================

    stats = {

        "total": total,
        "wins": wins,
        "losses": losses,
        "pendientes": pendientes,
        "winrate": winrate,
        "roi": roi,
        "profit_total": profit,
        "stake_total": stake_total,
        "score_promedio": score_promedio,

        "grafica_labels": list(
            range(len(profits))
        ),

        "grafica_profit": profits,

        "profit_acumulado": profits,

        "mercados_labels": [
            m["mercado"]
            for m in mercados
        ],

        "mercados_profit": [
            m["profit"]
            for m in mercados
        ],

        "mercados_winrate": [
            m["winrate"]
            for m in mercados
        ],

        "mercados": {}
    }

    for m in mercados:

        stats["mercados"][m["mercado"]] = {

            "total": m["total"],
            "winrate": m["winrate"],
            "profit": m["profit"]
        }

    # =========================
    # RENDER
    # =========================

    return render_template(

        "index.html",

        stats=stats,
        historial=historial,
        mercados=mercados,
        ligas=ligas,
        profits=profits,
        winrates=winrates,
        top_picks=top_picks
    )

# =========================
# START
# =========================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",
        port=10000,
        debug=False
    )