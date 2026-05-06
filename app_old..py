from flask import Flask, render_template_string
import pandas as pd

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<body style="background:black;color:white;text-align:center;">

<h1>🔥 SELECCIONES DEL BOT 🔥</h1>

{% if data|length == 0 %}
<p>No hay picks hoy</p>
{% else %}

<table border="1" style="margin:auto;">
<tr>
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

if __name__ == "__main__":
    app.run(debug=True)