import streamlit as st
import pandas as pd
import joblib

# --- Load the pre-trained model and data ---

# Load the machine learning pipeline
try:
    with open('models/best_chase_prediction_model.pkl', 'rb') as f:
        pipeline = joblib.load(f)
except FileNotFoundError:
    st.error("Model file not found. Make sure 'best_chase_prediction_model.pkl' is in the main directory.")
    st.stop()

# Load the match data to get a list of unique venues
try:
    match_df = pd.read_csv('data_files/match_details.csv')
    # Clean up venue names to match the training data
    match_df['venue'] = match_df['venue'].replace('Maharaja Yadavindra Singh International Cricket Stadium, Mullanpur', 'Maharaja Yadavindra Singh International Cricket Stadium, New Chandigarh')
    all_venues = sorted(match_df['venue'].unique())
except FileNotFoundError:
    st.error("Data file not found. Make sure 'data_files/match_details.csv' is in the correct folder.")
    st.stop()


# --- Streamlit Page Configuration ---

st.set_page_config(
    page_title="IPL Chase Predictor",
    page_icon="🏏",
    layout="wide"
)

# --- User Interface ---

st.title("IPL Chase Win Predictor")
st.markdown("This app predicts the probability of the chasing team winning an IPL match based on the live match scenario.")

st.markdown("---")

st.header("Enter Live Match Scenario")

# Create columns for a clean layout
col1, col2, col3 = st.columns(3)

with col1:
    batting_team = st.selectbox("Select the Batting Team", sorted(match_df['team_1'].unique()))
    bowling_team = st.selectbox("Select the Bowling Team", sorted(match_df['team_1'].unique()))
    selected_venue = st.selectbox("Select Venue", all_venues)

with col2:
    target = st.number_input("Target Score", min_value=0, step=1, value=0)
    score = st.number_input("Current Score", min_value=0, step=1, value=0)
    wickets = st.number_input("Wickets Down", min_value=0, max_value=9, step=1, value=0)

with col3:
    overs_completed = st.number_input("Overs Completed", min_value=0, max_value=19, step=1, value=0)
    balls_of_over = st.slider("Balls of Current Over Completed", 0, 5, 0)


# --- Prediction Logic ---

if st.button("Predict Win Probability"):
    if batting_team == bowling_team:
        st.error("Batting and Bowling teams cannot be the same.")
    else:
        # Calculate the features from user input
        runs_required = target - score
        balls_bowled = (overs_completed * 6) + balls_of_over
        balls_remaining = 120 - balls_bowled
        wickets_remaining = 10 - wickets
        
        # Avoid division by zero errors
        crr = (score * 6) / balls_bowled if balls_bowled > 0 else 0
        rrr = (runs_required * 6) / balls_remaining if balls_remaining > 0 else float('inf')

        # Create a DataFrame from the input with the correct column names and order
        input_data = pd.DataFrame({
            'venue': [selected_venue],
            'runs_required': [runs_required],
            'balls_remaining': [balls_remaining],
            'wickets_remaining': [wickets_remaining],
            'target_score': [target],
            'crr': [crr],
            'rrr': [rrr]
        })

        # The pipeline automatically handles the one-hot encoding
        win_probability = pipeline.predict_proba(input_data)[0][1]
        loss_probability = pipeline.predict_proba(input_data)[0][0]

        st.markdown("---")
        st.header("Prediction")
        
        # Use columns for a cleaner display
        pred_col1, pred_col2 = st.columns(2)
        with pred_col1:
            st.metric(f"{batting_team} Win %", f"{win_probability:.0%}")
        with pred_col2:
            st.metric(f"{bowling_team} Win %", f"{loss_probability:.0%}")

        # Display a progress bar for visualization
        st.progress(win_probability, text=f"{win_probability:.0%} Win Probability for {batting_team}")