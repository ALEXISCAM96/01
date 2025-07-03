import streamlit as st
import requests
import numpy as np
from collections import Counter

# ✅ Header global
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
            # ⚽ Estimación de goles por equipo
            st.subheader("⚽ Goles esperados")
            def get_avg_goals(matches, team_id):
                gf_list, gc_list = [], []
                for m in matches:
                    is_home = m["teams"]["home"]["id"] == team_id
                    gf = m["goals"]["home"] if is_home else m["goals"]["away"]
                    gc = m["goals"]["away"] if is_home else m["goals"]["home"]
                    if gf is not None and gc is not None:
                        gf_list.append(gf)
                        gc_list.append(gc)
                return (
                    round(np.mean(gf_list), 2) if gf_list else None,
                    round(np.mean(gc_list), 2) if gc_list else None
                )

            t1_gf, t1_gc = get_avg_goals(t1_matches, team1_id)
            t2_gf, t2_gc = get_avg_goals(t2_matches, team2_id)

            if t1_gf and t2_gc:
                t1_exp = round((t1_gf + t2_gc) / 2, 1)
            else:
                t1_exp = "N/D"

            if t2_gf and t1_gc:
                t2_exp = round((t2_gf + t1_gc) / 2, 1)
            else:
                t2_exp = "N/D"

            st.write(f"{team1_real}: {t1_exp} goles esperados")
            st.write(f"{team2_real}: {t2_exp} goles esperados")

            # 🟨 Estadísticas: córners y tarjetas
            st.subheader("🟨 Promedios de córners y tarjetas")
            def get_stats_per_team(team_id, matches):
                stats_url = "https://v3.football.api-sports.io/fixtures/statistics"
                total_corners, total_yellow, total_red = [], [], []
                for m in matches:
                    fid = m["fixture"]["id"]
                    r = requests.get(stats_url, headers=headers, params={"fixture": fid})
                    if r.status_code == 200:
                        all_stats = r.json()["response"]
                        for team_stats in all_stats:
                            if team_stats["team"]["id"] == team_id:
                                d = {i["type"]: i["value"] or 0 for i in team_stats["statistics"]}
                                total_corners.append(d.get("Corner Kicks", 0))
                                total_yellow.append(d.get("Yellow Cards", 0))
                                total_red.append(d.get("Red Cards", 0))
                return {
                    "corners": round(np.mean(total_corners), 1) if total_corners else "N/D",
                    "yellow": round(np.mean(total_yellow), 1) if total_yellow else "N/D",
                    "red": round(np.mean(total_red), 1) if total_red else "N/D"
                }

            t1_stats = get_stats_per_team(team1_id, t1_matches)
            t2_stats = get_stats_per_team(team2_id, t2_matches)

            st.write(f"{team1_real} → Córners: {t1_stats['corners']}, Amarillas: {t1_stats['yellow']}, Rojas: {t1_stats['red']}")
            st.write(f"{team2_real} → Córners: {t2_stats['corners']}, Amarillas: {t2_stats['yellow']}, Rojas: {t2_stats['red']}")
            # 🥅 Goleadores recientes
            st.subheader("🥅 Goleadores destacados del último partido entre ambos")

            def get_last_h2h_fixture(team1_id, team2_id):
                url = "https://v3.football.api-sports.io/fixtures/headtohead"
                r = requests.get(url, headers=headers, params={"h2h": f"{team1_id}-{team2_id}", "last": 1})
                data = r.json()["response"]
                return data[0]["fixture"]["id"] if data else None

            def get_goal_events(fixture_id):
                url = f"https://v3.football.api-sports.io/fixtures/events?fixture={fixture_id}"
                r = requests.get(url, headers=headers)
                if r.status_code == 200:
                    events = r.json()["response"]
                    return [e["player"]["name"] for e in events if e["type"] == "Goal" and e.get("player")]
                return []

            last_fixture_id = get_last_h2h_fixture(team1_id, team2_id)
            if last_fixture_id:
                scorers = get_goal_events(last_fixture_id)
                if scorers:
                    top_scorers = Counter(scorers).most_common(5)
                    for name, count in top_scorers:
                        st.markdown(f"- {name} ⚽ x{count}")
                else:
                    st.info("No se registraron goles en el último enfrentamiento.")
            else:
                st.warning("No se encontró un partido reciente entre estos equipos.")

            # 📚 Historial H2H (últimos 5 partidos)
            st.subheader("📚 Historial entre ambos equipos")
            h2h_url = "https://v3.football.api-sports.io/fixtures/headtohead"
            h2h_response = requests.get(h2h_url, headers=headers, params={"h2h": f"{team1_id}-{team2_id}", "last": 5})
            h2h_data = h2h_response.json()["response"]
            if h2h_data:
                for m in h2h_data:
                    st.write(f"{m['fixture']['date'][:10]} → {m['teams']['home']['name']} {m['goals']['home']} - {m['goals']['away']} {m['teams']['away']['name']}")
            else:
                st.info("No hay historial reciente.")

