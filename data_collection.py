'''import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

url = 'https://en.wikipedia.org/wiki/List_of_2024_Indian_Premier_League_personnel_changes'
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
traded_caption_tag = soup.find('caption', string=re.compile('List of Traded players'))
teams = [
        'Chennai Super Kings', 'Delhi Capitals', 'Mumbai Indians', 
        'Lucknow Super Giants', 'Gujarat Titans', 'Kolkata Knight Riders', 
        'Punjab Kings', 'Rajasthan Royals', 'Royal Challengers Bengaluru', 
        'Sunrisers Hyderabad']

if traded_caption_tag:
    traded_table_element = traded_caption_tag.find_parent('table')
    table_html = str(traded_table_element)
    traded_table = pd.read_html(table_html)[0]
    traded_table['Year'] = 2024
    print(traded_table.head())
else:
    print('Error: Traded players table not found.')

for team in teams:
    ret_cap_tag = None
    ret_cap_tag = soup.find('caption', string= re.compile(f'^{team}'))
    if ret_cap_tag:
        ret_tab_elm = ret_cap_tag.find_parent('table')
        ret_tab_html = str(ret_tab_elm)
        retained_table = pd.read_html(ret_tab_html)[0]
        retained_table['Team'] = team
print(retained_table.head())


'''
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from io import StringIO

url = 'https://en.wikipedia.org/wiki/List_of_2024_Indian_Premier_League_personnel_changes'

try:
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

    print("Scraping tables...")
    # Find ALL tables on the page
    for table in soup.find_all('table', class_='wikitable'):
        # Get the caption of the current table
        caption = table.find('caption')
        
        # Check if a caption exists and if any of our team names are in it
        if caption:
            for team in teams:
                # The most flexible check: does the caption text contain the team name?
                if team in caption.get_text():
                    print(f"-> Found table for {team}")
                    
                    # Read the table into a DataFrame
                    df = pd.read_html(StringIO(str(table)))[0]
                    df['Team'] = team # Add the team name as a new column
                    all_tables.append(df)
                    break # Stop checking other teams for this caption

    if all_tables:
        # Combine all found tables into a single DataFrame
        final_df = pd.concat(all_tables, ignore_index=True)
        print("\n✅ Successfully combined all tables!")
        print(final_df.head())
        print("\nLast 5 rows of the combined table:")
        print(final_df.tail())
    else:
        print("\n❌ No tables were found matching the team names.")

except requests.exceptions.RequestException as e:
    print(f"Error fetching the URL: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
