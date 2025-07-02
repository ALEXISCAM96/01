
import streamlit as st
import requests
import numpy as np
from collections import Counter
import time

st.set_page_config(page_title="Predicción Fútbol 360°", layout="wide")
st.title("⚽ Predicción Fútbol 360° - Multifuente")

match_input = st.text_input("Escribe un partido (ej: Real Madrid vs Barcelona):", "Real Madrid vs Borussia Dortmund")

if st.button("Analizar partido"):
    if " vs " not in match_input.lower():
        st.error("Formato incorrecto. Usa: Equipo A vs Equipo B")
    else:
        team1_name, team2_name = [t.strip() for t in match_input.split("vs")]
        headers = {"x-apisports-key": "39a57dc2bceae2bab6870799951ef4b1"}

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

            # --- Datos por API-Football ---
            def get_last_matches(team_id):
                url = "https://v3.football.api-sports.io/fixtures"
                r = requests.get(url, headers=headers, params={"team": team_id, "last": 15})
                data = r.json()["response"]
                result = []
                for idx, m in enumerate(data):
                    if m["goals"]["home"] is not None and m["goals"]["away"] is not None:
                        m["weight"] = 1.0 - (idx * 0.06)
                        m["team_id"] = team_id
                        result.append(m)
                return result[:10]

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

            fuente_forma = "API-Football"
            if t1_score is None or t2_score is None:
                fuente_forma = "FotMob (próximamente)"

            if t1_score:
                st.write(f"{team1_real}: {t1_score} (fuente: {fuente_forma})")
            else:
                st.warning(f"No hay datos de forma para {team1_real}")

            if t2_score:
                st.write(f"{team2_real}: {t2_score} (fuente: {fuente_forma})")
            else:
                st.warning(f"No hay datos de forma para {team2_real}")

            # Modelo básico de predicción
            st.subheader("🔮 Predicción preliminar")
            if t1_score and t2_score:
                if t1_score > t2_score + 0.3:
                    st.success(f"Predicción: Gana {team1_real}")
                elif t2_score > t1_score + 0.3:
                    st.success(f"Predicción: Gana {team2_real}")
                else:
                    st.info("Predicción: Empate probable")
            else:
                st.info("Sin suficientes datos para predecir resultado")

            # H2H (últimos 5)
            st.subheader("📚 Historial H2H (últimos 5 enfrentamientos)")
            h2h_url = "https://v3.football.api-sports.io/fixtures/headtohead"
            h2h_response = requests.get(h2h_url, headers=headers, params={"h2h": f"{team1_id}-{team2_id}", "last": 5})
            h2h_data = h2h_response.json()["response"]

            if h2h_data:
                team1_wins, team2_wins, draws = 0, 0, 0
                for m in h2h_data:
                    g1 = m["goals"]["home"]
                    g2 = m["goals"]["away"]
                    if g1 is None or g2 is None:
                        continue
                    if g1 == g2: draws += 1
                    elif m["teams"]["home"]["id"] == team1_id:
                        if g1 > g2: team1_wins += 1
                        else: team2_wins += 1
                    else:
                        if g2 > g1: team1_wins += 1
                        else: team2_wins += 1
                st.write(f"{team1_real}: {team1_wins} victorias | {team2_real}: {team2_wins} | Empates: {draws}")
            else:
                st.info("No se encontraron enfrentamientos recientes.")

            
            # Estimar goles esperados
            st.subheader("⚽ Goles esperados por equipo")
            def get_avg_goals(matches, team_id):
                gf_list = []
                gc_list = []
                for m in matches:
                    is_home = m["teams"]["home"]["id"] == team_id
                    gf = m["goals"]["home"] if is_home else m["goals"]["away"]
                    gc = m["goals"]["away"] if is_home else m["goals"]["home"]
                    if gf is not None and gc is not None:
                        gf_list.append(gf)
                        gc_list.append(gc)
                return (round(np.mean(gf_list), 2) if gf_list else None,
                        round(np.mean(gc_list), 2) if gc_list else None)

            t1_gf, t1_gc = get_avg_goals(t1_matches, team1_id)
            t2_gf, t2_gc = get_avg_goals(t2_matches, team2_id)

            if t1_gf is not None and t2_gc is not None:
                t1_expected = round((t1_gf + t2_gc) / 2, 1)
            else:
                t1_expected = "Sin datos"

            if t2_gf is not None and t1_gc is not None:
                t2_expected = round((t2_gf + t1_gc) / 2, 1)
            else:
                t2_expected = "Sin datos"

            st.write(f"{team1_real}: {t1_expected} goles esperados")
            st.write(f"{team2_real}: {t2_expected} goles esperados")

            # Estadísticas por equipo: córners y tarjetas
            st.subheader("🟨 Córners y tarjetas (últimos 10 partidos)")

            def get_stats_teams(team_id, matches):
                corners, yellow, red = [], [], []
                for m in matches:
                    fid = m["fixture"]["id"]
                    s = requests.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fid}", headers=headers)
                    if s.status_code == 200:
                        stats = s.json()["response"]
                        for team_stats in stats:
                            if team_stats["team"]["id"] == team_id:
                                sd = {i["type"]: i["value"] for i in team_stats["statistics"]}
                                if "Corner Kicks" in sd: corners.append(sd["Corner Kicks"] or 0)
                                if "Yellow Cards" in sd: yellow.append(sd["Yellow Cards"] or 0)
                                if "Red Cards" in sd: red.append(sd["Red Cards"] or 0)
                return {
                    "corners": round(np.mean(corners), 1) if corners else "Sin datos",
                    "yellow": round(np.mean(yellow), 1) if yellow else "Sin datos",
                    "red": round(np.mean(red), 1) if red else "Sin datos"
                }

            t1_stats = get_stats_teams(team1_id, t1_matches)
            t2_stats = get_stats_teams(team2_id, t2_matches)

            st.markdown(f"**{team1_real}**: {t1_stats['corners']} córners, {t1_stats['yellow']} amarillas, {t1_stats['red']} rojas")
            st.markdown(f"**{team2_real}**: {t2_stats['corners']} córners, {t2_stats['yellow']} amarillas, {t2_stats['red']} rojas")



            # Goleadores recientes
            st.subheader("🥅 Goleadores recientes en enfrentamientos directos")

            def get_last_h2h_fixture(team1_id, team2_id):
                url = "https://v3.football.api-sports.io/fixtures/headtohead"
                r = requests.get(url, headers=headers, params={"h2h": f"{team1_id}-{team2_id}", "last": 1})
                data = r.json()["response"]
                return data[0]["fixture"]["id"] if data else None

            def get_goals_from_fixture(fixture_id):
                url = f"https://v3.football.api-sports.io/fixtures/events?fixture={fixture_id}"
                r = requests.get(url, headers=headers)
                if r.status_code == 200:
                    events = r.json()["response"]
                    goal_scorers = [e["player"]["name"] for e in events if e["type"] == "Goal" and e.get("player")]
                    return Counter(goal_scorers).most_common(3)
                return []

            last_fixture_id = get_last_h2h_fixture(team1_id, team2_id)
            if last_fixture_id:
                top_scorers = get_goals_from_fixture(last_fixture_id)
                if top_scorers:
                    st.markdown("**Goleadores destacados del último encuentro:**")
                    for name, count in top_scorers:
                        st.markdown(f"- {name} ⚽ x{count}")
                else:
                    st.info("No se registraron goles en el último enfrentamiento.")
            else:
                st.warning("No se encontró un partido reciente entre estos equipos.")


# Próximamente:
            st.subheader("📈 Próximamente: Goles esperados, córners, tarjetas y goleadores")
            st.markdown("- Estimación de goles por equipo (⚽)")
            st.markdown("- Córners y tarjetas por promedio (🟨)")
            st.markdown("- Goleadores más probables (🥅)")
            st.markdown("- Predicción 360° final basada en múltiples fuentes")
