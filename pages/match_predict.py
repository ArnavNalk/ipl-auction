import streamlit as st
import pandas as pd
import joblib
import sys

def handle_exception(exc_type, exc_value, exc_traceback):
    print("❌ Exception caught:", exc_value)
    st.error("⚠️ Oops! Something went wrong on our end. Please try again.")

sys.excepthook = handle_exception
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


def compute_latest_team_form():
    match_df = pd.read_csv("data_files/match_details.csv")
    match_df['date'] = pd.to_datetime(match_df['date'])
    match_df.sort_values('date', inplace=True)

    match_df['team_1_win'] = (match_df['team_1'] == match_df['winner']).astype(int)
    match_df['team_2_win'] = (match_df['team_2'] == match_df['winner']).astype(int)

    team1_df = match_df[['date','season','match_id', 'team_1', 'team_1_win']].rename(columns={'team_1': 'team', 'team_1_win': 'win'})
    team2_df = match_df[['date','season','match_id', 'team_2', 'team_2_win']].rename(columns={'team_2': 'team', 'team_2_win': 'win'})

    form_df = pd.concat([team1_df, team2_df]).sort_values(by='date').reset_index(drop=True)
    form_df['form'] = form_df.groupby(['team','season'])['win'].rolling(window=5, min_periods=1).mean().reset_index(level=['team','season'], drop=True)
    form_df['form'] = form_df.groupby(['team','season'])['form'].shift(1)
    form_df.fillna(0, inplace=True)

    # ✅ latest form per team from latest season
    latest_season = form_df['season'].max()
    latest_form = (
        form_df[form_df['season'] == latest_season]
        .sort_values('date')
        .groupby('team')
        .tail(1)
        .set_index('team')['form']
        .to_dict()
    )
    return latest_form

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


latest_form = compute_latest_team_form()
batting_team_form = latest_form.get(batting_team, 0)
bowling_team_form = latest_form.get(bowling_team, 0)

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
            'rrr': [rrr],
            'batting_team_form': [batting_team_form],
            'bowling_team_form': [bowling_team_form]
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