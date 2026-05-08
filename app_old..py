import threading
import subprocess
from flask import Flask, render_template_string
import pandas as pd

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Bot Apuestas</title>
</head>

<body style="background:black;color:white;text-align:center;font-family:Arial;">

<h1>🔥 SELECCIONES DEL BOT 🔥</h1>

{% if data|length == 0 %}
<p>No hay picks hoy</p>
{% else %}

<table border="1" style="margin:auto;border-collapse:collapse;width:80%;">

<tr style="background:#222;">
<th>Partido</th>
<th>Mercado</th>
<th>Odds</th>
<th>Prob</th>
<th>Value</th>
<th>Stake</th>
</tr>

{% for row in data %}
<tr>
<td>{{row.get("partido","-")}}</td>
<td>{{row.get("mercado","-")}}</td>
<td>{{row.get("odd","-")}}</td>
<td>{{row.get("prob","-")}}</td>
<td>{{row.get("value","-")}}</td>
<td>{{row.get("stake","-")}}</td>
</tr>
{% endfor %}

</table>

{% endif %}

</body>
</html>
"""

@app.route("/")
def home():

    try:
        df = pd.read_csv("picks.csv")
        data = df.to_dict(orient="records")

    except:
        data = []

    return render_template_string(HTML, data=data)


# 🔥 INICIAR BOT AUTOMÁTICO
def iniciar_bot():
    subprocess.Popen(["python", "src/auto_run.py"])


# 🔥 EJECUTAR BOT EN SEGUNDO PLANO
threading.Thread(target=iniciar_bot).start()


# 🔥 INICIAR FLASK
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)