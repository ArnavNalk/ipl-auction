import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import google.generativeai as genai
import sqlite3
import sys
import logging

logging.basicConfig(filename='chatbot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def handle_exception(exc_type, exc_value, exc_traceback):
    logging.error("❌ Exception caught:", exc_value)
    st.error("⚠️ Oops! Something went wrong on our end. Please try again.")

sys.excepthook = handle_exception
os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
gemini_key = st.secrets["GOOGLE_API_KEY"]

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")

@st.cache_resource

def get_connection():
    return sqlite3.connect("ipl_auction.db", check_same_thread=False)
conn = get_connection()

SCHEMA = """
IPL DB 2022-2025

TABLE match_details
grain one row per match
match_id INTEGER
winner TEXT match winner only
venue TEXT
date TIMESTAMP
season INTEGER
toss_winner TEXT
toss_decision TEXT bat/bowl
match_type TEXT group/q1/eliminator/q2/final
team_1 TEXT batting first
team_1_score INTEGER
team_1_wickets INTEGER
team_1_balls_faced INTEGER
team_2 TEXT batting second
team_2_score INTEGER
team_2_wickets INTEGER
team_2_balls_faced INTEGER
note IPL champion = team with W in final column of ipltablesdata

TABLE ball_by_ball
grain one row per delivery
match_id INTEGER
inning INTEGER
is_super_over INTEGER
batting_team TEXT
bowling_team TEXT
over INTEGER
ball INTEGER
batter TEXT
non_striker TEXT
bowler TEXT
runs_off_bat INTEGER
extras INTEGER
extras_type TEXT
total_runs INTEGER
is_wicket INTEGER
player_out TEXT
kind TEXT dismissal type
fielder_name TEXT
note extras_type can be contain entries like 'legbyes, noballs'
note use SUM(runs_off_bat) for batter runs
note use SUM(total_runs) for team totals
note exclude run outs from bowler wickets

TABLE iplsquads
grain one row per player-season
player_name TEXT
team TEXT
year INTEGER
price REAL crore value
replacement TEXT
retained TEXT
country TEXT
age INTEGER
role TEXT Batter/Bowler/All-Rounder/Wicketkeeper
batting_style TEXT
bowling_style TEXT
c/u/a TEXT capped/uncapped/associate
base_price REAL

TABLE ipltablesdata
grain one row per team-season
position INTEGER
team TEXT
p INTEGER played
w INTEGER wins
l INTEGER losses
t INTEGER ties
nr INTEGER no result
pts INTEGER
nrr REAL
year INTEGER
q1 TEXT qualifier1 result
e TEXT eliminator result
q2 TEXT qualifier2 result
f TEXT final result
note final winner has f='W'
note position is league standing not IPL champion

TABLE super_over_details
grain one row per super over match
match_id INTEGER
winner TEXT
is_so_match INTEGER
so_team1_name TEXT
so_team2_name TEXT
so_team1_score INTEGER
so_team1_wickets INTEGER
so_team1_balls_faced INTEGER
so_team2_score INTEGER
so_team2_wickets INTEGER
so_team2_balls_faced INTEGER

RELATIONSHIPS
match_details.match_id = ball_by_ball.match_id
match_details.match_id = super_over_details.match_id

COMMON LOGIC
IPL winner = team with f='W'
top batter = SUM(runs_off_bat) by batter
top bowler = COUNT wickets by bowler excluding run outs
team score = SUM(total_runs)
strike rate = runs*100/balls
economy = runs conceded/overs
"""

def generate_sql(question):

    prompt = f"""
    You are an expert IPL analytics SQLite assistant.
    Generate ONLY valid SQLite SQL.
    STRICT RULES:
    - Return ONLY executable SQLite SQL
    - No markdown
    - No explanations
    - No comments
    - Only SELECT queries
    - Never hallucinate columns or tables
    - Use only schema provided
    - Use LIMIT 20 unless aggregation query
    - Use proper GROUP BY when aggregating
    - Use semantic meaning of columns carefully

    Important:
    - match winner != tournament winner
    - Exclude run outs when calculating bowler wickets
    - Use runs_off_bat for batter runs
    - Use total_runs for innings/team totals

    {SCHEMA}

    User Question:
    {question}
    """

    response = model.generate_content(prompt)
    sql = response.text.strip()
    usage = response.usage_metadata
    if not sql.lower().startswith("select"):
        raise ValueError("Only SELECT queries allowed")
    return {
        "sql": sql,
        "prompt_tokens": usage.prompt_token_count,
        "completion_tokens": usage.candidates_token_count,
        "total_tokens": usage.total_token_count
    }

def execute_sql(sql):
    try:
        df = pd.read_sql(sql, conn)
        return df
    except Exception as e:
        return str(e)

def summarize_results(question, df):

    prompt = f"""
    Answer the user's question naturally.
    You MUST trust the query results completely.
    The database results are the source of truth.
    Do NOT override results using world knowledge.
    Question:
    {question}
    Query Results:
    {df.to_string(index=False, max_rows=None, max_cols=None)}
    Give a concise conversational response.
    """
    response = model.generate_content(prompt)
    usage = response.usage_metadata
    return {
        "response": response.text,
        "prompt_tokens": usage.prompt_token_count,
        "completion_tokens": usage.candidates_token_count,
        "total_tokens": usage.total_token_count
    }

st.title("🤖 IPL Data Chatbot")

st.info(
    "🏏 **Ask questions about IPL data (2022-2025)**\n\n"
    "**Popular Questions:**\n"
    "• Who scored the most runs in IPL 2025?\n"
    "• Which team won IPL 2024?\n"
    "• Top 5 wicket takers in 2023\n"
    "• Most expensive player in IPL 2024\n"
    "• Which team has the highest win rate?\n"
)

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if "query_count" not in st.session_state:
    st.session_state.query_count = 0

# Display chat history
for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if question := st.chat_input("Ask a question about IPL data..."):
    prompt = f"""
Answer this question in natural, conversational language. 
Provide a complete sentence with proper formatting.
Do not return raw data tables - explain the answer clearly.

Question: {question}"""
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(question)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("🤔 Analyzing data..."):
            try:
                # Query the agent
                sql_result = generate_sql(question)
                result = execute_sql(sql_result["sql"])
                if isinstance(result, str):
                    st.error(result)
                else:
                    summary_response = summarize_results(question, result)
                    st.markdown(summary_response["response"])
                    sql_prompt_tokens = sql_result["prompt_tokens"]
                    sql_completion_tokens = sql_result["completion_tokens"]
                    sql_total_tokens = sql_result["total_tokens"]
                    summary_prompt_tokens = summary_response["prompt_tokens"]
                    summary_completion_tokens = summary_response["completion_tokens"]
                    summary_total_tokens = summary_response["total_tokens"]
                    grand_total_tokens = (sql_total_tokens +summary_total_tokens)
                    logging.info(f"""
                        QUESTION:{question}
                        GENERATED SQL:{sql_result["sql"]}
                        QUERY RESULTS:{result.to_string(index=False, max_rows=None, max_cols=None)}
                        FINAL RESPONSE:{summary_response["response"]}
                        SQL PROMPT TOKENS:{sql_prompt_tokens}
                        SQL COMPLETION TOKENS:{sql_completion_tokens}
                        SQL TOTAL TOKENS:{sql_total_tokens}
                        SUMMARY PROMPT TOKENS:{summary_prompt_tokens}
                        SUMMARY COMPLETION TOKENS:{summary_completion_tokens}
                        SUMMARY TOTAL TOKENS:{summary_total_tokens}
                        GRAND TOTAL TOKENS:{grand_total_tokens}
                        {'='*80}
                        """)
                st.session_state.chat_messages.append({
                    "role": "assistant", 
                    "content": summary_response["response"]
                })
                
                st.session_state.query_count += 1
                
            except Exception as e:
                error_msg = f"❌ **Error:** {str(e)}"
                print(error_msg)
                st.error('Oops there was an error please try again later')
                
                st.info(
                    "💡 **Tips to get better results:**\n"
                    "• Be specific: mention years (2022-2025), team names, or player names\n"
                    "• For run/wicket queries: specify the season clearly\n"
                    "• For squad queries: mention team name and year\n"
                    "• Try rephrasing if the answer seems incorrect"
                )

# Clear chat button
if st.session_state.query_count > 0:
    if st.button("🔄 Clear Chat History", type="secondary"):
        st.session_state.chat_messages = []
        st.session_state.query_count = 0
        st.rerun()