import streamlit as st

pages = {
'':[st.Page("pages/home.py",title='Home'),st.Page('pages/chatbot.py',title='Ask Me')], 
'Analysis':[st.Page("pages/team.py", title="Team Analysis", icon="📊"),
st.Page("pages/player.py", title="Player Analysis", icon="💰")],
'Prediction':[st.Page("pages/match_predict.py", title="Match Prediction", icon="📊"),
st.Page("pages/price_predict.py", title="Price Prediction", icon="💰")],
}

pg = st.navigation(pages)

pg.run()
