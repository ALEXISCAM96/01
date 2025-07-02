# Football Match Outcome Prediction App

Esta aplicación está desarrollada con **Streamlit** y predice el resultado de partidos de fútbol utilizando un modelo de machine learning (LightGBM).

---

## 🚀 Características

- Modo individual: ingresa estadísticas de un partido y obtén:
  - Predicción del resultado (local/empate/visitante)
  - Score estimado
  - Análisis de por qué se favorece a un equipo
  - Comparación de estadísticas con radar chart
  - Enlaces a estadísticas externas (FotMob)

- Modo por lote:
  - Sube un archivo CSV con varios partidos (hasta 10)
  - Obtén predicciones masivas ordenadas por confianza
  - Descarga los resultados en CSV

---

## 🧾 Requisitos

Instala los requisitos con:

```bash
pip install -r requirements.txt
```

---

## 🖥️ Ejecución local

```bash
streamlit run app.py
```

---

## 🌐 Despliegue en Streamlit Cloud

1. Sube tu código a un repositorio de GitHub.
2. Incluye:
   - `app.py`
   - `requirements.txt`
   - `lgb_model.joblib`
   - `label_encoder.joblib`
   - `training_columns.pkl`
3. Ve a [https://streamlit.io/cloud](https://streamlit.io/cloud) y conecta tu repositorio.
4. ¡Deploy!

---

## 📄 Formato del CSV por lote

Incluye columnas como:

- home_team, away_team, tournament, city, country, neutral
- home_team_avg_goals_scored_last_10, home_team_avg_goals_conceded_last_10, ...
- h2h_draws, avg_goals_scored_difference, etc.

Puedes usar esta [plantilla CSV de ejemplo](plantilla_predicciones.csv).

---

## 📊 Fuentes de datos sugeridas

- [FotMob](https://www.fotmob.com/es)
- [SofaScore](https://www.sofascore.com)
- [WhoScored](https://www.whoscored.com)

---

## 🧠 Autor

Esta app fue desarrollada como herramienta educativa y de análisis predictivo. Puedes extenderla fácilmente con:
- Nuevos modelos
- Más features (clima, ranking FIFA, lesiones)
- Integración con APIs externas

