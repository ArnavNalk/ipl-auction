import streamlit as st

st.set_page_config(
    page_title="IPL Analysis Home",
    page_icon="🏏",
    layout='wide'
)

st.title("IPL Auction and Match Analysis Dashboard")
st.write("Welcome to the IPL analysis dashboard!")
st.markdown(
    """
    This dashboard provides an in-depth look at IPL data from 2022-2025.
    **Select an analysis from the top navigation bar** to get started.
    ### What you can find:
    - **Auction Analysis:** A deep dive into player auction prices and team spending.
    - **Match Analysis:** Visualizations of match results, team performance, and key metrics.
    """
)