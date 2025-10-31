import streamlit as st

pages = {
'':[st.Page("pages/home.py",title='Home'),st.Page('pages/chatbot.py',title='Ask Me')], 
'Analysis':[st.Page("pages/team.py", title="Team Analysis"),
st.Page("pages/player.py", title="Player Analysis")],
'Prediction':[st.Page("pages/match_predict.py", title="Match Prediction")],
}

pg = st.navigation(pages)

pg.run()
