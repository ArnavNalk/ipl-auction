import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from io import StringIO
import numpy as np
import json
import os
from rapidfuzz import process, fuzz

def convert_price(price_str):
    if not isinstance(price_str, str):
        return np.nan

    crore_match = re.search(r'([\d.]+)\s*crore', price_str, re.IGNORECASE)
    lakh_match = re.search(r'([\d.]+)\s*lakh', price_str, re.IGNORECASE)

    if crore_match:
        value = float(crore_match.group(1))
        return value
    elif lakh_match:
        value = float(lakh_match.group(1))
        return value/100
    else:
        return np.nan

def scrape_player_data(st_year, end_year, type):
    player_data = []
    for year in range(st_year, end_year):
        if type == 'replacement':
                team_map = {
                        "Chennai Super Kings": "CSK",
                        "Mumbai Indians": "MI",
                        "Royal Challengers Bangalore": "RCB",
                        "Kolkata Knight Riders": "KKR",
                        "Rajasthan Royals": "RR",
                        "Sunrisers Hyderabad": "SRH",
                        "Delhi Capitals": "DC",
                        "Punjab Kings": "PBKS",
                        "Lucknow Super Giants": "LSG",
                        "Gujarat Titans": "GT",
                        "Royal Challengers Bengaluru":"RCB"}
                if year == 2022 or year == 2025:
                    url3  = f'https://en.wikipedia.org/wiki/List_of_{year}_Indian_Premier_League_personnel_changes'
                    response3 = requests.get(url3)
                    soup3 = BeautifulSoup(response3.text, 'html.parser')
                    head_tag3  = soup3.find('h2', id="Withdrawn_players")
                    table3 = head_tag3.find_next('table')
                    table_df3 = pd.read_html(StringIO(str(table3)))[0]
                    table_df3.rename(columns={table_df3.columns[5]: 'Player Name',table_df3.columns[6]: 'Price'}, inplace=True)
                    table_df3['Team'] = table_df3['Team'].map(team_map)
                    table_df3['Price'] = table_df3['Price'].apply(convert_price)
                    table_df3 = table_df3[['Team','Player Name','Price']]
                    table_df3['Year'] = year
                    table_df3['Replacement'] = 'Yes'
                    table_df3 = table_df3[table_df3['Price'].notna()].reset_index(drop=True)
                    player_data.append(table_df3)
                else:
                    url3  = f'https://en.wikipedia.org/wiki/List_of_{year}_Indian_Premier_League_personnel_changes'
                    response3 = requests.get(url3)
                    soup3 = BeautifulSoup(response3.text, 'html.parser')
                    head_tag3  = soup3.find('h2', id="Withdrawn_players")
                    table3 = head_tag3.find_next('table')
                    table_df3 = pd.read_html(StringIO(str(table3)))[0]
                    table_df3.rename(columns={table_df3.columns[6]: 'Player Name',table_df3.columns[8]: 'Price'}, inplace=True)
                    table_df3['Team'] = table_df3['Team'].map(team_map)
                    table_df3['Price'] = table_df3['Price'].apply(convert_price)
                    table_df3 = table_df3[['Team','Player Name','Price']]
                    table_df3['Year'] = year
                    table_df3['Replacement'] = 'Yes'
                    table_df3 = table_df3[table_df3['Price'].notna()].reset_index(drop=True)
                    player_data.append(table_df3)
        else:
            url = f'https://sports.ndtv.com/ipl-{year}/auction/{type}'
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            teams = ['CSK', 'DC', 'MI',
                    'LSG', 'GT', 'KKR',
                    'PBKS', 'RR', 'RCB',
                    'SRH']

            for team in teams:
                table = soup.find('table', id=re.compile(team))
                table_df = pd.read_html(StringIO(str(table)))[0]
                table_df['Player Name'] = table_df.apply(lambda row: row['Player Name'].replace(row['Type'], '').strip(), axis=1)
                table_df['Team'] = team
                table_df['Year'] = year
                if type == 'retainedplayer':
                    table_df['Retained'] = 'Yes'
                    table_df['Price'] = table_df['Salary (₹ Cr.)']
                    table_df = table_df[['Player Name','Team','Year','Price','Retained']]
                else:
                    table_df['Price'] = table_df['Price (₹ Cr.)']
                    table_df['Replacement'] = 'No'
                    table_df = table_df[['Player Name','Team','Year','Price','Replacement']]
                player_data.append(table_df)
            
    return pd.concat(player_data,ignore_index=True)

retained_df = scrape_player_data(2022,2026,'retainedplayer')
squad_df = scrape_player_data(2022,2026,'teamsquad')
replacement_df = scrape_player_data(2022,2026,'replacement')
squad_df = pd.concat([squad_df,replacement_df])
squad_df['Player Name'] = squad_df['Player Name'].str.replace(r'[^a-zA-Z\s]$', '', regex=True)
final_df = pd.merge(
        squad_df,
        retained_df[['Player Name', 'Team', 'Year','Retained']],
        on=['Player Name', 'Team', 'Year'],
        how='left'
    )

final_df['Retained'] = final_df['Retained'].fillna('No')
final_df['Price'] = final_df['Price'].astype(float)
final_df['Player Name'] = final_df['Player Name'].apply(
    lambda x: 'Sai Kishore' if x == 'Ravisrinivasan Sai Kishore'
    else 'Vijaykumar Vyshak' if x == 'Vyshak Vijay Kumar'
    else 'Kumar Kartikeya' if x == 'Kumar Kartikeya Singh'
    else "Will O'Rourke" if x == "Will O’Rourke"
    else 'KS Bharat' if x == 'Srikar Bharat'
    else 'Yudhvir Singh' if x == 'Yudhvir Charak'
    else 'Harpreet Singh' if x == 'Harpreet Singh Bhatia'
    else x
)
missing_player = {'Player Name':'Saurav Chuahan','Team':'RCB','Year':2024,'Price':0.20,'Replacement':'No','Retained':'No'}
missing_player_df = pd.DataFrame([missing_player])
final_df = pd.concat([final_df,missing_player_df],ignore_index=True)
final_df.to_csv('data_files/final.csv')

merged_tables = []
for year in range(2022,2026):
    df = pd.read_csv(f'Player_data/IPL{year}PlayerAuction.csv')
    copy = final_df[final_df['Year']==year].copy()
    merged_df = pd.merge(
            copy,
            df,
            on=['Player Name'],
            how='left'
        )
    merged_tables.append(merged_df)
squad_df = pd.concat(merged_tables,ignore_index=True)
squad_df['Base Price'] = squad_df['Base Price']/100


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

team_tables.to_csv('data_files/IPLTablesData.csv')

tables = []
for filename in os.listdir('matches'):
    with open(f'matches/{filename}') as f:
        data = json.load(f)
        date = data['info']['dates'][0]
        team1, team2 = data['info']['players'].items()
        d1 = {'Player Name':team1[1],'Team':team_map.get(team1[0]),'Year':date[0:4]}
        d2 = {'Player Name':team2[1],'Team':team_map.get(team2[0]),'Year':date[0:4]}
        df1= pd.DataFrame(d1)
        df2= pd.DataFrame(d2)
        tables.append(df1)
        tables.append(df2)
json_df = pd.concat(tables,ignore_index=True)
json_df = json_df.drop_duplicates().reset_index(drop=True)
json_df['Year'] = json_df['Year'].astype(int)

dict={}
for filename in os.listdir('matches'):
    with open(f'matches/{filename}') as f:
        data = json.load(f)
    reg = data['info']['registry']['people']
    dict.update(reg)

player_names = set(json_df['Player Name'].str.strip().str.lower())
player_dict = { key:value for key, value in dict.items() if key.strip().lower() in player_names}
player_df = pd.DataFrame(list(player_dict.items()), columns=['Player Name', 'Player ID'])
json_df = pd.merge(json_df,player_df,on=['Player Name'],how='left')

def norm_names(name):
    parts = name.strip().split()
    if len(parts) < 2:
        return name
    first_initial = parts[0][0].upper() + parts[0][-1].upper()
    last_name = parts[-1].title()
    return f"{first_initial} {last_name}"

squad_df['Role'] = squad_df['Role'].str.title()
squad_df['Role'] = squad_df['Role'].replace('Batter', 'Batsman')
squad_df['Bowling Style']= squad_df['Bowling Style'].str.title()
squad_df['Norm_names'] = squad_df['Player Name'].apply(norm_names)
player_map = {'CV Varun':'Varun Chakravarthy','PWH de Silva':'Wanindu Hasaranga','PHKD Mendis':'Kamindu Mendis',
              'PVSN Raju':'Satyanarayana Raju','DS Rathi':'Digvesh Singh','Rasikh Salam':'Rasikh Dar',
              'PWA Mulder':'Wiaan Mulder','M Shahrukh Khan':'Shahrukh Khan','BKG Mendis': 'Kusal Mendis'}
json_df['Player Name']= json_df['Player Name'].replace(player_map)
json_df['Norm_names'] = json_df['Player Name'].apply(norm_names)

def fuzzy_match_with_team_year(player_name, team, year, squad_df, threshold=80):
    filtered_squad = squad_df[(squad_df['Team'] == team) & (squad_df['Year'] == year)]
    if filtered_squad.empty:
        return None  
    choices = filtered_squad['Norm_names'].tolist()
    match, score, _ = process.extractOne(player_name, choices, scorer=fuzz.token_sort_ratio)

    return match if score >= threshold else None
json_df['Matched_Name'] = json_df.apply(lambda row: fuzzy_match_with_team_year(player_name=row['Norm_names'],team=row['Team'],year=row['Year'],squad_df=squad_df),axis=1)

merged_df = pd.merge(
    json_df,
    squad_df,
    left_on=['Matched_Name', 'Team', 'Year'],
    right_on=['Norm_names', 'Team', 'Year'],
    how='left',
    suffixes=('_json', '_squad')
)

squad_final_df = merged_df.drop(['Player Name_json','Norm_names_json','Matched_Name','Norm_names_squad'],axis=1)
squad_final_df.to_csv('data_files/IPLSquadData.csv')