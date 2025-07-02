
import streamlit as st
import requests
import numpy as np
from collections import Counter

st.title("⚽ Predicción Avanzada Multimodelo (Mejorada)")

match_input = st.text_input("Escribe un partido (ej: Real Madrid vs Barcelona):", "Real Madrid vs Borussia Dortmund")

if st.button("Analizar partido"):
    if " vs " not in match_input.lower():
        st.error("Por favor escribe el partido en formato: Equipo A vs Equipo B")
    else:
        team1_name, team2_name = [t.strip() for t in match_input.split("vs")]
        headers = {"x-apisports-key": "39a57dc2bceae2bab6870799951ef4b1"}

        def get_team_id(name):
            r = requests.get("https://v3.football.api-sports.io/teams", headers=headers, params={"search": name})
            data = r.json()
            if data["results"] > 0:
                return data["response"][0]["team"]["id"], data["response"][0]["team"]["name"]
            return None, None

        team1_id, team1_real = get_team_id(team1_name)
        team2_id, team2_real = get_team_id(team2_name)

        if not team1_id or not team2_id:
            st.error("No se encontraron los equipos.")
        else:
            st.success(f"Equipos detectados: {team1_real} vs {team2_real}")

            def get_last_matches_unfiltered(team_id):
                url = "https://v3.football.api-sports.io/fixtures"
                r = requests.get(url, headers=headers, params={"team": team_id, "last": 15})
                data = r.json()["response"]
                result = []
                for idx, m in enumerate(data):
                    m["team_id"] = team_id
                    m["weight"] = 1.0 - (idx * 0.06)  # peso decreciente más suave
                    # Solo incluir si hay goles
                    home_goals = m["goals"]["home"]
                    away_goals = m["goals"]["away"]
                    if home_goals is not None and away_goals is not None:
                        result.append(m)
                return result[:10]  # máximo 10 válidos

            def weighted_score(matches):
                score = 0
                total_weight = 0
                for m in matches:
                    w = m["weight"]
                    is_home = m["teams"]["home"]["id"] == m["team_id"]
                    gf = m["goals"]["home"] if is_home else m["goals"]["away"]
                    ga = m["goals"]["away"] if is_home else m["goals"]["home"]
                    if gf is None or ga is None:
                        continue
                    result = 3 if gf > ga else (1 if gf == ga else 0)
                    score += result * w
                    total_weight += w
                return round(score / total_weight, 2) if total_weight > 0 else None

            st.subheader("🧠 Forma Actual Ponderada (últimos partidos jugados)")

            t1_matches = get_last_matches_unfiltered(team1_id)
            t2_matches = get_last_matches_unfiltered(team2_id)

            t1_score = weighted_score(t1_matches)
            t2_score = weighted_score(t2_matches)

            if t1_score is not None:
                st.write(f"{team1_real}: {t1_score}")
            else:
                st.warning(f"No hay suficientes partidos válidos para {team1_real}")

            if t2_score is not None:
                st.write(f"{team2_real}: {t2_score}")
            else:
                st.warning(f"No hay suficientes partidos válidos para {team2_real}")

            if t1_score is not None and t2_score is not None:
                if t1_score > t2_score + 0.3:
                    st.success(f"➡️ Predicción por forma: Gana {team1_real}")
                    forma_winner = team1_real
                elif t2_score > t1_score + 0.3:
                    st.success(f"➡️ Predicción por forma: Gana {team2_real}")
                    forma_winner = team2_real
                else:
                    st.info("➡️ Predicción por forma: Empate probable")
                    forma_winner = "Empate"
            else:
                forma_winner = None

            # Modelo 2: H2H
            st.subheader("📚 Historial H2H (últimos 5 enfrentamientos)")
            h2h_url = "https://v3.football.api-sports.io/fixtures/headtohead"
            h2h_response = requests.get(h2h_url, headers=headers, params={"h2h": f"{team1_id}-{team2_id}", "last": 5})
            h2h_data = h2h_response.json()["response"]

            if h2h_data:
                team1_wins = 0
                team2_wins = 0
                draws = 0
                for m in h2h_data:
                    g1 = m["goals"]["home"]
                    g2 = m["goals"]["away"]
                    if g1 is None or g2 is None:
                        continue
                    if g1 == g2:
                        draws += 1
                    elif m["teams"]["home"]["id"] == team1_id:
                        if g1 > g2:
                            team1_wins += 1
                        else:
                            team2_wins += 1
                    else:
                        if g2 > g1:
                            team1_wins += 1
                        else:
                            team2_wins += 1
                st.write(f"{team1_real} ganó {team1_wins} / {team2_real} ganó {team2_wins} / Empates: {draws}")
                if team1_wins > team2_wins:
                    h2h_winner = team1_real
                elif team2_wins > team1_wins:
                    h2h_winner = team2_real
                else:
                    h2h_winner = "Empate"
                st.success(f"➡️ Predicción por H2H: {h2h_winner}")
            else:
                st.warning("No hay historial reciente entre estos equipos.")
                h2h_winner = None

            # Modelo combinado final
            st.subheader("🧮 Predicción combinada")
            votes = [forma_winner, h2h_winner]
            votes = [v for v in votes if v]
            if votes:
                final_vote = Counter(votes).most_common(1)[0][0]
                st.success(f"✅ Predicción final combinada: {final_vote}")
            else:
                st.warning("No hay suficientes datos confiables para generar una predicción.")
