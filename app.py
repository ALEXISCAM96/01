
import streamlit as st
import pandas as pd
import requests
import numpy as np
from collections import Counter

st.title("⚽ Predicción Automática de Partidos de Fútbol")

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
            st.error("Uno o ambos equipos no fueron encontrados.")
        else:
            st.success(f"Equipos detectados: {team1_real_name} vs {team2_real_name}")

            def get_last_matches(team_id):
                url = "https://v3.football.api-sports.io/fixtures"
                r = requests.get(url, headers=headers, params={"team": team_id, "last": 10})
                data = r.json()["response"]
                for m in data:
                    m["team_id"] = team_id
                return data

            def analyze_team(matches):
                stats = {"goals_for": [], "goals_against": [], "wins": 0, "draws": 0, "losses": 0}
                for m in matches:
                    is_home = m["teams"]["home"]["id"] == m["team_id"]
                    gf = m["goals"]["home"] if is_home else m["goals"]["away"]
                    ga = m["goals"]["away"] if is_home else m["goals"]["home"]
                    stats["goals_for"].append(gf)
                    stats["goals_against"].append(ga)
                    if gf > ga: stats["wins"] += 1
                    elif gf == ga: stats["draws"] += 1
                    else: stats["losses"] += 1
                return stats

            team1_matches = get_last_matches(team1_id)
            team2_matches = get_last_matches(team2_id)
            team1_stats = analyze_team(team1_matches)
            team2_stats = analyze_team(team2_matches)

            t1_avg_goals = np.mean(team1_stats["goals_for"])
            t2_avg_goals = np.mean(team2_stats["goals_for"])
            t1_avg_conceded = np.mean(team1_stats["goals_against"])
            t2_avg_conceded = np.mean(team2_stats["goals_against"])

            if t1_avg_goals > t2_avg_conceded and t1_avg_goals >= t2_avg_goals:
                winner = team1_real_name
            elif t2_avg_goals > t1_avg_conceded and t2_avg_goals > t1_avg_goals:
                winner = team2_real_name
            else:
                winner = "Empate"

            est_team1_goals = round((t1_avg_goals + t2_avg_conceded) / 2, 1)
            est_team2_goals = round((t2_avg_goals + t1_avg_conceded) / 2, 1)

            st.subheader("🔮 Predicción del Resultado")
            st.write("Resultado probable: {}".format(winner))
            st.write("Goles esperados: {} {} - {} {}".format(team1_real_name, est_team1_goals, est_team2_goals, team2_real_name))

            def estimate_stats(team_id):
                r = requests.get("https://v3.football.api-sports.io/fixtures", headers=headers, params={"team": team_id, "last": 10})
                matches = r.json()["response"]
                corners, yellow, red = [], [], []
                for m in matches:
                    fid = m["fixture"]["id"]
                    s = requests.get("https://v3.football.api-sports.io/fixtures/statistics?fixture={}".format(fid), headers=headers)
                    if s.status_code == 200:
                        stats = s.json()["response"]
                        for t in stats:
                            if t["team"]["id"] == team_id:
                                sd = {i["type"]: i["value"] for i in t["statistics"]}
                                corners.append(sd.get("Corner Kicks", 0) or 0)
                                yellow.append(sd.get("Yellow Cards", 0) or 0)
                                red.append(sd.get("Red Cards", 0) or 0)
                return {
                    "avg_corners": round(np.mean(corners), 1) if corners else 0,
                    "avg_yellow": round(np.mean(yellow), 1) if yellow else 0,
                    "avg_red": round(np.mean(red), 1) if red else 0
                }

            team1_extra = estimate_stats(team1_id)
            team2_extra = estimate_stats(team2_id)

            st.subheader("📊 Estadísticas esperadas")
            st.write("Córners: {} {} - {} {}".format(team1_real_name, team1_extra['avg_corners'], team2_extra['avg_corners'], team2_real_name))
            st.write("Tarjetas amarillas: {} {} - {} {}".format(team1_real_name, team1_extra['avg_yellow'], team2_extra['avg_yellow'], team2_real_name))
            st.write("Tarjetas rojas: {} {} - {} {}".format(team1_real_name, team1_extra['avg_red'], team2_extra['avg_red'], team2_real_name))

            likely = team1_real_name if est_team1_goals > est_team2_goals else team2_real_name
            st.write("🥅 Goleador más probable de: {}".format(likely))

            # Goleadores reales del último partido
            st.subheader("👤 Goleadores recientes (último partido entre ambos)")
            h2h_last_response = requests.get("https://v3.football.api-sports.io/fixtures/headtohead", headers=headers, params={
                "h2h": "{}-{}".format(team1_id, team2_id),
                "last": 1
            })
            if h2h_last_response.status_code == 200:
                h2h_last_data = h2h_last_response.json()["response"]
                if h2h_last_data:
                    last_fixture_id = h2h_last_data[0]["fixture"]["id"]
                    events_response = requests.get("https://v3.football.api-sports.io/fixtures/events?fixture={}".format(last_fixture_id), headers=headers)
                    if events_response.status_code == 200:
                        events = events_response.json()["response"]
                        scorers = [e["player"]["name"] for e in events if e["type"] == "Goal" and e.get("player")]
                        if scorers:
                            top_scorers = Counter(scorers).most_common(3)
                            st.markdown("**Goleadores destacados:**")
                            for name, count in top_scorers:
                                st.markdown("- {} ⚽ x{}".format(name, count))
                        else:
                            st.info("No se registraron goles en el último partido.")
                    else:
                        st.warning("No se pudieron obtener los eventos.")
                else:
                    st.warning("No se encontró un partido reciente entre estos equipos.")
            else:
                st.error("Error al consultar H2H.")

