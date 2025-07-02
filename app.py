
import streamlit as st
import requests
import numpy as np
from collections import Counter

# ✅ FIX CRÍTICO: Definimos headers globalmente
headers = { "x-apisports-key": "39a57dc2bceae2bab6870799951ef4b1" }

st.set_page_config(page_title="Predicción Fútbol 360°", layout="wide")
st.title("⚽ Predicción Fútbol 360° - Multifuente")

match_input = st.text_input("Escribe un partido (ej: Real Madrid vs Barcelona):", "Real Madrid vs Barcelona")

if st.button("Analizar partido"):
    if " vs " not in match_input.lower():
        st.error("Formato incorrecto. Usa: Equipo A vs Equipo B")
    else:
        team1_name, team2_name = [t.strip() for t in match_input.split("vs")]

        def get_team_id(name):
            url = "https://v3.football.api-sports.io/teams"
            r = requests.get(url, headers=headers, params={"search": name})
            data = r.json()
            if data["results"] > 0:
                return data["response"][0]["team"]["id"], data["response"][0]["team"]["name"]
            return None, None

        team1_id, team1_real = get_team_id(team1_name)
        team2_id, team2_real = get_team_id(team2_name)

        if not team1_id or not team2_id:
            st.error("Uno o ambos equipos no se encontraron.")
        else:
            st.success(f"Equipos detectados: {team1_real} vs {team2_real}")

            def get_last_matches(team_id):
                url = "https://v3.football.api-sports.io/fixtures"
                r = requests.get(url, headers=headers, params={"team": team_id, "last": 10})
                data = r.json()["response"]
                result = []
                for idx, m in enumerate(data):
                    if m["goals"]["home"] is not None and m["goals"]["away"] is not None:
                        m["weight"] = 1.0 - (idx * 0.06)
                        m["team_id"] = team_id
                        result.append(m)
                return result

            def weighted_score(matches):
                score = 0
                total_weight = 0
                for m in matches:
                    is_home = m["teams"]["home"]["id"] == m["team_id"]
                    gf = m["goals"]["home"] if is_home else m["goals"]["away"]
                    ga = m["goals"]["away"] if is_home else m["goals"]["home"]
                    w = m["weight"]
                    if gf is None or ga is None:
                        continue
                    pts = 3 if gf > ga else (1 if gf == ga else 0)
                    score += pts * w
                    total_weight += w
                return round(score / total_weight, 2) if total_weight > 0 else None

            st.subheader("🧠 Forma reciente (últimos 10 partidos)")
            t1_matches = get_last_matches(team1_id)
            t2_matches = get_last_matches(team2_id)
            t1_score = weighted_score(t1_matches)
            t2_score = weighted_score(t2_matches)

            if t1_score is not None:
                st.write(f"{team1_real}: {t1_score}")
            else:
                st.warning(f"No hay datos para {team1_real}")

            if t2_score is not None:
                st.write(f"{team2_real}: {t2_score}")
            else:
                st.warning(f"No hay datos para {team2_real}")

            st.subheader("📚 H2H")
            h2h_url = "https://v3.football.api-sports.io/fixtures/headtohead"
            h2h_response = requests.get(h2h_url, headers=headers, params={"h2h": f"{team1_id}-{team2_id}", "last": 5})
            h2h_data = h2h_response.json()["response"]
            if h2h_data:
                for m in h2h_data:
                    st.write(f"{m['fixture']['date'][:10]} → {m['teams']['home']['name']} {m['goals']['home']} - {m['goals']['away']} {m['teams']['away']['name']}")
            else:
                st.info("No hay historial reciente.")
