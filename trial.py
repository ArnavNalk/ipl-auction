import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from io import StringIO

url = 'https://en.wikipedia.org/wiki/List_of_2024_Indian_Premier_League_personnel_changes'
response = requests.get(url)
response.raise_for_status()
soup = BeautifulSoup(response.text, 'html.parser')

    # We will use the main city/region names which are unique
teams = [
        'Chennai Super Kings', 'Delhi Capitals', 'Mumbai Indians',
        'Lucknow Super Giants', 'Gujarat Titans', 'Kolkata Knight Riders',
        'Punjab Kings', 'Rajasthan Royals', 'Royal Challengers Bengaluru',
        'Sunrisers Hyderabad'
    ]
    
all_tables = []

te = soup.find('div', string=re.compile('List of Retained'))

fe = te.find_parent('div')

tables = fe.find_all('table' , class_='wikitable')

for table in tables:
    caption = table.find('caption')
    for team in teams:
        if team in caption.get_text():
            df= pd.read_html(StringIO(str(table)))[0]
            df['Team'] = team
            all_tables.append(df)
ret_tab = pd.concat(all_tables)
print(ret_tab.tail())



