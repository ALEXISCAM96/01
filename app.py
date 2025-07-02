import streamlit as st
import joblib
import pandas as pd
import numpy as np
import warnings

# Suppress specific warnings that might clutter the output
warnings.filterwarnings('ignore', category=UserWarning, module='sklearn')
warnings.filterwarnings('ignore', category=FutureWarning, module='sklearn')

# Add a title to the Streamlit application
st.title("Football Match Outcome Prediction")

# Here the trained model is loaded from the 'lgb_model.joblib' file.
# Make sure 'lgb_model.joblib' is in the same folder as 'app.py'.
try:
    best_estimator_lgb = joblib.load('lgb_model.joblib')
    st.success("LightGBM model loaded successfully.")
except FileNotFoundError:
    st.error("Error: lgb_model.joblib not found. Please ensure the model file is in the correct directory.")
    st.stop() # Stop the app if the model cannot be loaded

# Here the LabelEncoder is loaded from the 'label_encoder.joblib' file.
# Make sure 'label_encoder.joblib' is in the same folder as 'app.py'.
# It is used to convert the model's numerical results back to text.
try:
    label_encoder = joblib.load('label_encoder.joblib')
    st.success("LabelEncoder loaded successfully.")
except FileNotFoundError:
    st.error("Error: label_encoder.joblib not found. Please ensure the encoder file is in the correct directory.")
    st.stop() # Stop the app if the encoder cannot be loaded

# Here the list of column names is loaded from the 'training_columns.pkl' file.
# Make sure 'training_columns.pkl' is in the same folder as 'app.py'.
# It is used to ensure that the user's input columns match those used for training.
try:
    with open('training_columns.pkl', 'rb') as f:
        training_columns = joblib.load(f)
    st.success("Training columns loaded successfully.")
except FileNotFoundError:
    st.error("Error: training_columns.pkl not found. Please ensure the columns file is in the correct directory.")
    st.stop() # Stop the app if the columns cannot be loaded

st.write("Model and encoder loaded, ready for predictions.")


# Create the input fields for the user
st.header("Enter Match Details and Engineered Features")

# Categorical features
st.subheader("Categorical Features")
tournament = st.text_input("Tournament", "Friendly")
city = st.text_input("City", "Neutral Venue")
country = st.text_input("Country", "Neutral Country")
home_team = st.text_input("Home Team", "Team A")
away_team = st.text_input("Away Team", "Team B")
neutral = st.checkbox("Neutral Venue", False)


# Numerical engineered features
st.subheader("Engineered Features (Calculated based on historical data up to match date)")
st.write("Please enter the pre-calculated engineered features for the match:")

home_team_avg_goals_scored_last_10 = st.number_input("Home Team Avg Goals Scored (Last 10)", value=1.5, format="%.2f")
home_team_avg_goals_conceded_last_10 = st.number_input("Home Team Avg Goals Conceded (Last 10)", value=1.2, format="%.2f")
home_team_win_percentage_last_10 = st.number_input("Home Team Win Percentage (Last 10)", value=0.6, format="%.2f")

away_team_avg_goals_scored_last_10 = st.number_input("Away Team Avg Goals Scored (Last 10)", value=1.3, format="%.2f")
away_team_avg_goals_conceded_last_10 = st.number_input("Away Team Avg Goals Conceded (Last 10)", value=1.4, format="%.2f")
away_team_win_percentage_last_10 = st.number_input("Away Team Win Percentage (Last 10)", value=0.5, format="%.2f")

home_team_h2h_wins = st.number_input("Home Team Head-to-Head Wins", value=0, step=1)
away_team_h2h_wins = st.number_input("Away Team Head-to-Head Wins", value=0, step=1)
h2h_draws = st.number_input("Head-to-Head Draws", value=0, step=1)

# Interaction features (calculated from the averages/percentages)
avg_goals_scored_difference = home_team_avg_goals_scored_last_10 - away_team_avg_goals_scored_last_10
avg_goals_conceded_difference = home_team_avg_goals_conceded_last_10 - away_team_avg_goals_conceded_last_10
win_percentage_difference = home_team_win_percentage_last_10 - away_team_win_percentage_last_10

# Display calculated interaction features (optional, but good for user understanding)
st.subheader("Calculated Interaction Features")
st.write(f"Average Goals Scored Difference (Home - Away): {avg_goals_scored_difference:.2f}")
st.write(f"Average Goals Conceded Difference (Home - Away): {avg_goals_conceded_difference:.2f}")
st.write(f"Win Percentage Difference (Home - Away): {win_percentage_difference:.2f}")


# Prediction button
predict_button = st.button("Predict Outcome")


if predict_button:
    # Create a dictionary with the input data from the Streamlit UI
    input_data = {
        'tournament': [tournament],
        'city': [city],
        'country': [country],
        'neutral': [neutral],
        'home_team_avg_goals_scored_last_10': [home_team_avg_goals_scored_last_10],
        'home_team_avg_goals_conceded_last_10': [home_team_avg_goals_conceded_last_10],
        'home_team_win_percentage_last_10': [home_team_win_percentage_last_10],
        'away_team_avg_goals_scored_last_10': [away_team_avg_goals_scored_last_10],
        'away_team_avg_goals_conceded_last_10': [away_team_avg_goals_conceded_last_10],
        'away_team_win_percentage_last_10': [away_team_win_percentage_last_10],
        'home_team_h2h_wins': [home_team_h2h_wins],
        'away_team_h2h_wins': [away_team_h2h_wins],
        'h2h_draws': [h2h_draws],
        'avg_goals_scored_difference': [avg_goals_scored_difference],
        'avg_goals_conceded_difference': [avg_goals_conceded_difference],
        'win_percentage_difference': [win_percentage_difference],
        # Add placeholder columns that were in the original data but not used as direct features for model input
        # (like home_team, away_team, date, scores, which are handled by engineered features)
        'home_team': ["temp_home"], # Dummy values
        'away_team': ["temp_away"], # Dummy values
         'date': ['2025-01-01'], # Dummy date
         'home_score': [None], # Dummy score
         'away_score': [None]  # Dummy score
    }

    # Create a DataFrame from the input data
    input_df = pd.DataFrame(input_data)

    # Ensure the order of columns in input_df matches the original data structure before encoding
    # This is important for one-hot encoding to work correctly
    original_columns_order = ['date', 'home_team', 'away_team', 'home_score', 'away_score',
                              'tournament', 'city', 'country', 'neutral',
                              'home_team_avg_goals_scored_last_10', 'home_team_avg_goals_conceded_last_10',
                              'home_team_win_percentage_last_10', 'away_team_avg_goals_scored_last_10',
                              'away_team_avg_goals_conceded_last_10', 'away_team_win_percentage_last_10',
                              'home_team_h2h_wins', 'away_team_h2h_wins', 'h2h_draws',
                              'avg_goals_scored_difference', 'avg_goals_conceded_difference', 'win_percentage_difference'] # Reconstruct the feature order


    # Reindex input_df to match the order of original features before encoding
    # Only include columns that were part of the original features used for one-hot encoding and numerical features
    features_before_encoding = [col for col in original_columns_order if col in input_df.columns]
    input_df = input_df[features_before_encoding]


    # Apply the same preprocessing steps as used for training data

    # 1. One-hot encode categorical features
    categorical_cols = ['tournament', 'city', 'country', 'neutral'] # Explicitly list categorical columns
    input_encoded = pd.get_dummies(input_df, columns=categorical_cols, drop_first=False)

    # 2. Align columns with the training data - crucial step
    # Here the list of columns loaded from 'training_columns.pkl' is used
    # to ensure that the user's input columns exactly match the columns
    # the model was trained with.
    # Add missing columns present in training but not in new data (fill with 0)
    for col in training_columns:
        if col not in input_encoded.columns:
            input_encoded[col] = 0

    # Drop extra columns present in new data but not in training (shouldn't happen if input structure is correct)
    extra_cols = [col for col in input_encoded.columns if col not in training_columns]
    input_encoded = input_encoded.drop(columns=extra_cols)

    # Ensure the order of columns is the same as training data
    input_encoded = input_encoded[training_columns]

    # The column names in training_columns are already cleaned for LightGBM,
    # so no extra cleaning is needed here on `input_encoded.columns`.

    # 3. Make prediction
    # Here the model loaded from 'lgb_model.joblib' is used to make the prediction.
    predicted_encoded = best_estimator_lgb.predict(input_encoded)

    # 4. Decode the prediction
    # Here the LabelEncoder loaded from 'label_encoder.joblib' is used
    # to convert the model's numerical prediction back to a readable text
    # ('Home Win', 'Away Win', or 'Draw').
    predicted_result = label_encoder.inverse_transform(predicted_encoded)

    # 5. Display the prediction
    st.subheader("Predicted Outcome")
    st.write(f"The predicted match outcome is: **{predicted_result[0]}**")


# ----------------------------
# NUEVA SECCIÓN: Carga de CSV
# ----------------------------
st.header("📂 Predicción por archivo CSV")

uploaded_file = st.file_uploader("Sube un archivo CSV con partidos para predecir", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.success("Archivo CSV cargado correctamente.")
        st.dataframe(df.head())

        # Preprocesamiento similar al flujo manual
        categorical_cols = ['tournament', 'city', 'country', 'neutral']
        df_encoded = pd.get_dummies(df, columns=categorical_cols, drop_first=False)

        for col in training_columns:
            if col not in df_encoded.columns:
                df_encoded[col] = 0

        extra_cols = [col for col in df_encoded.columns if col not in training_columns]
        df_encoded = df_encoded.drop(columns=extra_cols)
        df_encoded = df_encoded[training_columns]

        predictions_encoded = best_estimator_lgb.predict(df_encoded)
        predictions = label_encoder.inverse_transform(predictions_encoded)

        df["Predicción"] = predictions

        st.subheader("📊 Resultados de la predicción:")
        st.dataframe(df[["home_team", "away_team", "Predicción"]])

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo: {e}")



import requests

import requests

st.header("📊 Estadísticas del último partido de un equipo (API-Football)")

team_name_input = st.text_input("Nombre del equipo (en inglés, ej: Argentina, Brazil, Germany):", "Argentina")

if st.button("Buscar último partido y estadísticas"):
    # Paso 1: buscar ID del equipo
    team_search_url = "https://v3.football.api-sports.io/teams"
    headers = {
        "x-apisports-key": "39a57dc2bceae2bab6870799951ef4b1"
    }
    team_response = requests.get(team_search_url, headers=headers, params={"search": team_name_input})

    if team_response.status_code == 200 and team_response.json()["results"] > 0:
        team_data = team_response.json()["response"][0]
        team_id = team_data["team"]["id"]
        team_name_found = team_data["team"]["name"]

        # Paso 2: buscar últimos partidos (sin limitar por temporada)
        fixture_url = "https://v3.football.api-sports.io/fixtures"
        fixture_response = requests.get(fixture_url, headers=headers, params={
            "team": team_id,
            "last": 1
        })

        if fixture_response.status_code == 200 and fixture_response.json()["results"] > 0:
            match = fixture_response.json()["response"][0]
            stats_url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={match['fixture']['id']}"
            stats_response = requests.get(stats_url, headers=headers)

            home_team = match["teams"]["home"]["name"]
            away_team = match["teams"]["away"]["name"]
            st.subheader(f"{home_team} vs {away_team}")

            if stats_response.status_code == 200:
                stats_data = stats_response.json()["response"]
                if stats_data:
                    for team_stats in stats_data:
                        st.markdown(f"### 📋 {team_stats['team']['name']}")
                        stats_dict = {item['type']: item['value'] for item in team_stats['statistics']}
                        st.json(stats_dict)
                else:
                    st.warning("Estadísticas no disponibles para este partido.")
            else:
                st.error("Error al obtener estadísticas del partido.")
        else:
            st.warning(f"No se encontraron partidos recientes para {team_name_found}.")
    else:
        st.error("Equipo no encontrado. Asegurate de escribirlo correctamente en inglés.")
