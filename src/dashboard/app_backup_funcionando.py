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

        print("✅ CSV cargado correctamente")
        print("📊 Filas cargadas:", len(df))

    except Exception as e:

        print("❌ Error CSV:", e)

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

    elite_picks = []

    mercados = []

    ligas = []

    profits = []

    winrates = []

    # =========================
    # SI HAY DATA
    # =========================

    if not df.empty:

        # =========================
        # LIMPIEZA BASICA
        # =========================

        df.columns = df.columns.str.strip()

        # =========================
        # ASEGURAR COLUMNAS
        # =========================

        columnas_necesarias = [
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

        for col in columnas_necesarias:

            if col not in df.columns:

                df[col] = ""

        # =========================
        # LIMPIAR RESULTADO
        # =========================

        df["resultado"] = (
            df["resultado"]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        # =========================
        # CONVERTIR NUMEROS
        # =========================

        columnas_numericas = [
            "odd",
            "prob",
            "value",
            "score",
            "stake",
            "profit"
        ]

        for col in columnas_numericas:

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            ).fillna(0)

        # =========================
        # FECHA PARA ORDENAR
        # ARREGLO FUERTE
        # =========================

        df["fecha_limpia"] = (
            df["fecha"]
            .astype(str)
            .str.strip()
            .str.slice(0, 16)
        )

        df["fecha_orden"] = pd.to_datetime(
            df["fecha_limpia"],
            format="%Y-%m-%d %H:%M",
            errors="coerce"
        )

        df["fecha_orden"] = df["fecha_orden"].fillna(
            pd.Timestamp.min
        )

        # =========================
        # ESTADISTICAS
        # =========================

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

        try:

            score_promedio = round(
                df["score"].mean(),
                2
            )

        except:

            score_promedio = 0

        # =========================
        # HISTORIAL
        # NUEVO A VIEJO
        # =========================

        historial_df = df.sort_values(
            by="fecha_orden",
            ascending=False
        ).copy()

        print("🧾 ORDEN HISTORIAL:")
        print(
            historial_df[
                [
                    "fecha",
                    "fecha_limpia",
                    "fecha_orden",
                    "partido",
                    "resultado"
                ]
            ].head(10)
        )

        historial = (
            historial_df
            .drop(
                columns=[
                    "fecha_orden",
                    "fecha_limpia",
                    "score_num"
                ],
                errors="ignore"
            )
            .fillna("")
            .to_dict(
                orient="records"
            )
        )

        # =========================
        # TOP PICKS
        # =========================

        df["score_num"] = pd.to_numeric(
            df["score"],
            errors="coerce"
        ).fillna(0)

        top_picks = (
            df
            .sort_values(
                by="score_num",
                ascending=False
            )
            .head(10)
            .drop(
                columns=[
                    "fecha_orden",
                    "fecha_limpia",
                    "score_num"
                ],
                errors="ignore"
            )
            .fillna("")
            .to_dict(
                orient="records"
            )
        )

        elite_picks = (
            df[df["score_num"] >= 25]
            .sort_values(
                by="score_num",
                ascending=False
            )
            .drop(
                columns=[
                    "fecha_orden",
                    "fecha_limpia",
                    "score_num"
                ],
                errors="ignore"
            )
            .fillna("")
            .to_dict(
                orient="records"
            )
        )

        # =========================
        # MERCADOS
        # =========================

        for mercado in df["mercado"].dropna().unique():

            if mercado == "":

                continue

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

        for liga in df["liga"].dropna().unique():

            if liga == "":

                continue

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
        # VIEJO A NUEVO
        # =========================

        df_grafica = df.sort_values(
            by="fecha_orden",
            ascending=True
        ).copy()

        df_grafica["profit_acumulado"] = (
            df_grafica["profit"].cumsum()
        )

        profits = (
            df_grafica["profit_acumulado"]
            .round(2)
            .tolist()
        )

        # =========================
        # GRAFICA WINRATE
        # VIEJO A NUEVO
        # =========================

        acumulado_w = 0
        acumulado_total = 0

        for _, row in df_grafica.iterrows():

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
        top_picks=top_picks,
        elite_picks=elite_picks
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