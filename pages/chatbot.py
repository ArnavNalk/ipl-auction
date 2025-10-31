import os
import streamlit as st
import pandas as pd
import pandasai as pai
from dotenv import load_dotenv
from pandasai import Agent, SmartDataframe
from pandasai_litellm.litellm import LiteLLM
import sys

def handle_exception(exc_type, exc_value, exc_traceback):
    print("❌ Exception caught:", exc_value)
    st.error("⚠️ Oops! Something went wrong on our end. Please try again.")
sys.excepthook = handle_exception
load_dotenv()
gemini_key = os.getenv("GOOGLE_API_KEY")

# Only initialize LLM and config once
if 'llm_initialized' not in st.session_state:
    llm = LiteLLM(
        model="gemini/gemini-2.5-flash",
        api_key=gemini_key,
        use_vertex=False
    )

    pai.config.set({
        "llm": llm,
        "verbose": False,
        "use_error_correction_framework": False,
        "max_rows": 8,
        "enforce_privacy": False,
        "save_logs": False,
        "enable_cache": True,
        "open_charts": False,
        "direct_sql":False,
        'conversational':True
    })
    
    st.session_state.llm_initialized = True

def smart_optimize_dataframe(df):
    """Balance memory optimization with data integrity"""
    df = df.copy()
    
    # Drop only truly useless columns
    df = df.dropna(axis=1, how='all')
    
    # Keep column names intact for better query understanding
    # (Don't shorten - helps LLM understand the data better)
    
    # Efficient type conversion
    for col in df.select_dtypes(include=['object']).columns:
        nunique = df[col].nunique()
        if nunique / len(df) < 0.4:
            df[col] = df[col].astype('category')
    
    # Numeric downcasting
    for col in df.select_dtypes(include=['int']).columns:
        df[col] = pd.to_numeric(df[col], downcast='integer')
    
    for col in df.select_dtypes(include=['float']).columns:
        df[col] = pd.to_numeric(df[col], downcast='float')
    
    return df

def smart_strategic_sample(df, max_rows, key_column=None):
    """Strategic sampling that preserves data distribution"""
    if len(df) <= max_rows:
        return df
    
    # For ball-by-ball data: stratified sampling by year/match
    if 'match_id' in df.columns and 'season' in df.columns:
        # Sample proportionally across seasons
        result_dfs = []
        for season in df['season'].unique():
            season_df = df[df['season'] == season]
            season_sample_size = int(max_rows * (len(season_df) / len(df)))
            
            if len(season_df) > season_sample_size:
                # Sample complete matches from this season
                matches = season_df['match_id'].unique()
                n_matches = max(1, season_sample_size // 300)  # ~300 balls per match
                sampled_matches = pd.Series(matches).sample(n=min(n_matches, len(matches)), random_state=42)
                result_dfs.append(season_df[season_df['match_id'].isin(sampled_matches)])
            else:
                result_dfs.append(season_df)
        
        return pd.concat(result_dfs, ignore_index=True)
    
    # For match data: keep all data (it's already small)
    elif 'match_id' in df.columns or 'season' in df.columns:
        return df  # Don't sample match-level data
    
    # For other data: random sample
    return df.sample(n=min(max_rows, len(df)), random_state=42)

@st.cache_data
def load_data():
    """Load with smart optimization"""
    dataframes = {}
    
    files_config = {
        'match': {
            'path': 'data_files/match_details.csv',
            'name': 'Match Details',
            'desc': 'Match results, scores, winners',
            'sample': None  # Keep all match data (usually small)
        },
        'table': {
            'path': 'data_files/IPLTablesData.csv',
            'name': 'Points Table',
            'desc': 'Team standings by season',
            'sample': None  # Keep all table data
        },
        'balls': {
            'path': 'data_files/ball_by_ball.csv',
            'name': 'Ball Data',
            'desc': 'Ball-by-ball delivery details',
            'sample': 25000  # Increased for better accuracy
        },
        'squad': {
            'path': 'data_files/IPLSquads.csv',
            'name': 'Squad Data',
            'desc': 'Player squad and role info',
            'sample': None  # Keep all squad data
        }
    }
    
    for key, config in files_config.items():
        try:
            # Load CSV
            df = pd.read_csv(config['path'], index_col=0)
            
            # Strategic sampling
            if config['sample'] and len(df) > config['sample']:
                df = smart_strategic_sample(df, max_rows=config['sample'])
            
            # Optimize without losing important info
            df = smart_optimize_dataframe(df)
            df = df.drop_duplicates()
            df.name = config['name']
            df.description = config['desc']
            
            dataframes[key] = {
                'df': df,
                'name': config['name'],
                'desc': config['desc']
            }
            
        except FileNotFoundError:
            pass
        except Exception as e:
            st.error(f"❌ Error loading {config['name']}: {str(e)}")
    
    return dataframes

@st.cache_resource
def initialize_agent(_dataframes):
    smart_dfs = []
    for key, data in _dataframes.items():
        df = data['df']
        sdf = SmartDataframe(
            df, 
            config={
                "name": data['name'],
                "description": data['desc']
            }
        )
        smart_dfs.append(sdf)
    return Agent(smart_dfs)

st.title("🤖 IPL Data Chatbot")
dataframes = load_data()
if len(dataframes) ==0:
    st.error("❌ Service currently unavialabe.")
    st.stop()

if 'agent' not in st.session_state:
    with st.spinner("⚙️ Initializing AI chatbot..."):
        st.session_state.agent = initialize_agent(dataframes)
agent = st.session_state.agent

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
                response = agent.chat(prompt)
                
                # Display response
                st.markdown(response)
                
                # Save to history
                st.session_state.chat_messages.append({
                    "role": "assistant", 
                    "content": response
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