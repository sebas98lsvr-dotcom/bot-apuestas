import csv
import os
import shutil
from datetime import datetime

# ======================
# RUTAS
# ======================

BASE_DIR = os.path.dirname(
    os.path.dirname(__file__)
)

PICKS_FILE = os.path.join(
    BASE_DIR,
    "picks.csv"
)

BACKUP_DIR = os.path.join(
    BASE_DIR,
    "backups"
)

os.makedirs(
    BACKUP_DIR,
    exist_ok=True
)

# ======================
# VALIDAR ARCHIVO
# ======================

if not os.path.exists(PICKS_FILE):
    print("❌ No existe picks.csv")
    exit()

if os.path.getsize(PICKS_FILE) == 0:
    print("❌ picks.csv está vacío")
    exit()

# ======================
# BACKUP
# ======================

timestamp = datetime.now().strftime(
    "%Y%m%d_%H%M%S"
)

backup_file = os.path.join(
    BACKUP_DIR,
    f"picks_limpieza_backup_{timestamp}.csv"
)

shutil.copy2(
    PICKS_FILE,
    backup_file
)

print(f"🛡️ Backup creado: {backup_file}")

# ======================
# LEER CSV
# ======================

picks = []

with open(
    PICKS_FILE,
    newline="",
    encoding="utf-8"
) as f:

    reader = csv.DictReader(f)

    if not reader.fieldnames:
        print("❌ picks.csv no tiene encabezados")
        exit()

    columnas_originales = list(reader.fieldnames)

    for row in reader:

        if not any(str(v).strip() for v in row.values() if v is not None):
            continue

        picks.append(row)

if len(picks) == 0:
    print("⚠️ No hay picks para limpiar")
    exit()

# ======================
# HELPERS
# ======================

def to_float(valor, default=0.0):

    try:
        if valor is None:
            return default

        valor = str(valor).strip()

        if valor == "":
            return default

        return float(valor)

    except:
        return default


def es_score_valido(score):

    score = str(score).strip()

    if "-" not in score:
        return False

    partes = score.split("-")

    if len(partes) != 2:
        return False

    return (
        partes[0].strip().isdigit()
        and partes[1].strip().isdigit()
    )

# ======================
# LIMPIAR
# ======================

corregidos = 0

for p in picks:

    # asegurar columnas
    if "score" not in p:
        p["score"] = ""

    if "stake" not in p:
        p["stake"] = "30.0"

    if "profit" not in p:
        p["profit"] = "0"

    if "resultado" not in p:
        p["resultado"] = "pendiente"

    if "notificado" not in p:
        p["notificado"] = "no"

    resultado = str(
        p.get("resultado", "pendiente")
    ).strip().lower()

    odd = to_float(
        p.get("odd", 0),
        0
    )

    stake = to_float(
        p.get("stake", 30),
        30
    )

    profit_anterior = str(
        p.get("profit", "")
    ).strip()

    score_anterior = str(
        p.get("score", "")
    ).strip()

    notificado_anterior = str(
        p.get("notificado", "")
    ).strip()

    # ======================
    # SCORE
    # ======================

    # Si score no parece marcador real tipo 1-2, limpiarlo
    if not es_score_valido(score_anterior):
        p["score"] = ""

    # ======================
    # RESULTADOS
    # ======================

    if resultado == "win":

        nuevo_profit = round(
            (odd - 1) * stake,
            2
        )

        p["profit"] = str(nuevo_profit)
        p["notificado"] = "si"

    elif resultado == "loss":

        nuevo_profit = round(
            -stake,
            2
        )

        p["profit"] = str(nuevo_profit)
        p["notificado"] = "si"

    else:

        p["resultado"] = "pendiente"
        p["profit"] = "0"
        p["notificado"] = "no"

    # contar cambios aproximados
    if (
        str(p.get("profit", "")).strip() != profit_anterior
        or str(p.get("score", "")).strip() != score_anterior
        or str(p.get("notificado", "")).strip() != notificado_anterior
    ):
        corregidos += 1

# ======================
# COLUMNAS
# ======================

campos_base = [
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

campos = []

for c in columnas_originales:
    if c not in campos:
        campos.append(c)

for c in campos_base:
    if c not in campos:
        campos.append(c)

for p in picks:
    for key in p.keys():
        if key not in campos:
            campos.append(key)

# ======================
# GUARDAR SEGURO
# ======================

temp_file = PICKS_FILE + ".tmp"

with open(
    temp_file,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=campos,
        extrasaction="ignore"
    )

    writer.writeheader()
    writer.writerows(picks)

os.replace(
    temp_file,
    PICKS_FILE
)

print("✅ Limpieza completada")
print(f"🔧 Filas corregidas: {corregidos}")