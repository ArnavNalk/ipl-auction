import json
import pandas as pd
import os

'''players = set()
for filename in os .listdir('matches'):
    with open(f'matches/{filename}') as f:
        data = json.load(f)
        team1, team2 = data['info']['players'].items()
        players.update(team1[1])
        players.update(team2[1])
print(players)'''

with open('matches/1473481.json') as f:
    data = json.load(f)
