
import streamlit as st
import pandas as pd
import requests
import numpy as np

st.title("⚽ Predicción Inteligente basada en forma actual")

match_input = st.text_input("Escribe un partido (ej: Real Madrid vs Barcelona):", "Real Madrid vs Barcelona")

if st.button("Analizar partido"):
    if " vs " not in match_input.lower():
        st.error("Por favor escribe el partido en formato: Equipo A vs Equipo B")
    else:
        team1_name, team2_name = [t.strip() for t in match_input.split("vs")]
        headers = { "x-apisports-key": "39a57dc2bceae2bab6870799951ef4b1" }

        def get_team_id(name):
            r = requests.get("https://v3.football.api-sports.io/teams", headers=headers, params={"search": name})
            data = r.json()
            if data["results"] > 0:
                return data["response"][0]["team"]["id"], data["response"][0]["team"]["name"]
            return None, None

        team1_id, team1_real_name = get_team_id(team1_name)
        team2_id, team2_real_name = get_team_id(team2_name)

        if not team1_id or not team2_id:
            st.error("No se encontraron los equipos.")
        else:
            def get_last_matches(team_id):
                r = requests.get("https://v3.football.api-sports.io/fixtures", headers=headers, params={"team": team_id, "last": 10})
                data = r.json()["response"]
                for idx, m in enumerate(data):
                    m["team_id"] = team_id
                    m["weight"] = 1.0 - (idx * 0.08)  # peso decreciente
                return data

            def calculate_weighted_score(matches):
                score = 0
                total_weight = 0
                for m in matches:
                    weight = m["weight"]
                    is_home = m["teams"]["home"]["id"] == m["team_id"]
                    gf = m["goals"]["home"] if is_home else m["goals"]["away"]
                    ga = m["goals"]["away"] if is_home else m["goals"]["home"]

                    result_score = 3 if gf > ga else (1 if gf == ga else 0)
                    score += result_score * weight
                    total_weight += weight
                return round(score / total_weight, 2) if total_weight > 0 else 0

            team1_matches = get_last_matches(team1_id)
            team2_matches = get_last_matches(team2_id)

            team1_score = calculate_weighted_score(team1_matches)
            team2_score = calculate_weighted_score(team2_matches)

            st.subheader("📊 Puntuación de forma (ponderada)")
            st.write(f"{team1_real_name}: {team1_score}")
            st.write(f"{team2_real_name}: {team2_score}")

            if team1_score > team2_score + 0.3:
                prediction = f"Gana {team1_real_name}"
            elif team2_score > team1_score + 0.3:
                prediction = f"Gana {team2_real_name}"
            else:
                prediction = "Empate probable"

            st.subheader("🔮 Predicción ajustada por forma reciente")
            st.success(f"Resultado estimado: {prediction}")
