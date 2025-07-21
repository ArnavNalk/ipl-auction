import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from io import StringIO
import matplotlib.pyplot as plt
import seaborn as sns
def scrape_player_data(st_year, end_year, type):
    player_data = []
    for year in range(st_year, end_year):
        url = f'https://sports.ndtv.com/ipl-{year}/auction/{type}'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        teams = ['CSK', 'DC', 'MI',
                'LSG', 'GT', 'KKR',
                'PBKS', 'RR', 'RCB',
                'SRH']

        for team in teams:
            table = soup.find('table', id=re.compile(team))
            if table:
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        player_name = player_name = cells[1].get_text(strip=True).replace(cells[2].get_text(strip=True), '').strip()
                        role = cells[2].get_text(strip=True)
                        price = cells[3].get_text(strip=True)
                        spans = cells[1].find_all('span')
                        Origin = 'Unknown'
                        for span in spans:
                            class_attr = span.get('class', [])
                            if 'vj-sp_india-flag' in class_attr:
                                Origin = 'Indian'
                                break
                            if 'vj-sp_airoplane'in class_attr:
                                Origin = 'Overseas'
                                break
                        if type == 'retainedplayer':
                            player_data.append({
                            'Player': player_name,
                            'Role': role,
                            'Price': price,
                            'Team': team,
                            'Year': year,
                            'Origin': Origin,
                            "Retained": 'Yes'})
                        else:
                            player_data.append({
                            'Player': player_name,
                            'Role': role,
                            'Price': price,
                            'Team': team,
                            'Year': year,
                            'Origin': Origin,
                        })
    return pd.DataFrame(player_data)

retained_df = scrape_player_data(2022,2026,'retainedplayer')
squad_df = scrape_player_data(2022,2026,'teamsquad')
final_df = pd.merge(
        squad_df,
        retained_df[['Player', 'Team', 'Year','Retained']],
        on=['Player', 'Team', 'Year'],
        how='left'
    )

final_df['Retained'] = final_df['Retained'].fillna('No')
final_df['Price'] = final_df['Price'].astype(float)
final_df.to_csv('final.csv')

df = pd.read_csv('IPL2022.csv')
copy = final_df[final_df['Year']==2022].copy()
df = df.rename(columns={'Name':'Player'})
final22_df = pd.merge(
        copy,
        df[['Player', 'Year','C/U/A']],
        on=['Player', 'Year'],
        how='left'
    )

copy23 = final_df[final_df['Year']==2023].copy()
df23 = pd.read_csv('2023players.csv')
final23_df = pd.merge(
        copy23,
        df23[['Player', 'Year','C/U/A']],
        on=['Player', 'Year'],
        how='left'
    )


copy24 = final_df[final_df['Year']==2024].copy()
copy24['Player'].to_csv('24Players.csv')
df24 = pd.read_csv('2024Players.csv')
final24_df = pd.merge(
        copy24,
        df24[['Player', 'Year','C/U/A']],
        on=['Player', 'Year'],
        how='left'
    )
final24_df.info()
final24_df.loc[(final24_df['Player'] == 'Amit Mishra') & (final24_df['C/U/A'].isna()), 'C/U/A'] = 'Capped'
final24_df = final24_df.fillna('Uncapped')
copy25 = final_df[final_df['Year']==2025]
copy25['Player'].to_csv('25players.csv')
df25 = pd.read_csv('2025Players.csv')
final25_df = pd.merge(
        copy25,
        df25[['Player', 'Year','C/U/A']],
        on=['Player', 'Year'],
        how='left'
    )
final25_df
final_auction = pd.concat([final22_df,final23_df,final24_df,final25_df])
final_auction.to_csv('IPLSquadData.csv')

team_map = {
    "Chennai Super Kings": "CSK",
    "Mumbai Indians": "MI",
    "Royal Challengers Bengaluru": "RCB",
    "Kolkata Knight Riders": "KKR",
    "Rajasthan Royals": "RR",
    "Sunrisers Hyderabad": "SRH",
    "Delhi Capitals": "DC",
    "Punjab Kings": "PBKS",
    "Lucknow Super Giants": "LSG",
    "Gujarat Titans": "GT"
}
team_tables = pd.DataFrame()
for year in range(2022,2026):
    url = f'https://sports.ndtv.com/ipl-{year}/points-table'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    tag = soup.find('h1', class_='scr_pg-ttl')
    table = tag.find_next('table')
    table_df = pd.read_html(StringIO(str(table)))[0]
    table_df.drop('Unnamed: 9',axis=1,inplace=True)
    table_df = table_df[table_df['No'] != table_df['P']].reset_index(drop=True)
    table_df['Teams'] = table_df['Teams'].apply(lambda x: x.split(' ')[-1])
    table_df.rename(columns={'No':'Position'},inplace=True)
    table_df['Year'] = year
    table_df.rename(columns={'Teams':'Team'},inplace=True)
    url2 = f'https://en.wikipedia.org/wiki/{year}_Indian_Premier_League'
    response2 = requests.get(url2)
    soup2 = BeautifulSoup(response2.text, 'html.parser')
    tag2 = soup2.find('h2' if year == 2023 else 'h3', id='Match_summary')
    table2 = tag2.find_next('table')
    table_df2 = pd.read_html(StringIO(str(table2)))[0]
    table_df2.columns = table_df2.columns.get_level_values(1)
    table_df2 = table_df2[['Team','Q1','E','Q2','F']]
    table_df2['Team'] = table_df2['Team'].map(team_map)
    final_df = pd.merge(
    table_df,
    table_df2,
    on=['Team'],
    how='left')
    team_tables = pd.concat([team_tables,final_df],ignore_index=True)

team_tables.to_csv('IPLTablesData.csv')

