import sqlite3
import pandas as pd

DB_PATH = "ipl_auction.db"

conn = sqlite3.connect(DB_PATH)

query = """SELECT
  'Mohammed Shami' AS player_name,
  SUM(CASE WHEN T1.bowler = 'Mohammed Shami' AND T1.is_wicket = 1 AND T1.kind != 'run out' AND T1.is_super_over = 0 THEN 1 ELSE 0 END) AS bowler_wickets,
  SUM(CASE WHEN T1.bowler = 'Mohammed Shami' AND T1.is_super_over = 0 THEN T1.total_runs ELSE 0 END) AS bowler_runs_conceded,
  COUNT(CASE WHEN T1.bowler = 'Mohammed Shami' AND T1.is_super_over = 0 AND T1.extras_type NOT IN ('wides', 'noballs') THEN 1 ELSE NULL END) AS bowler_balls_bowled,
  SUM(CASE WHEN T1.batter = 'Mohammed Shami' AND T1.is_super_over = 0 THEN T1.runs_off_bat ELSE 0 END) AS batter_runs_scored,
  COUNT(CASE WHEN T1.batter = 'Mohammed Shami' AND T1.is_super_over = 0 AND T1.extras_type NOT IN ('wides', 'noballs') THEN 1 ELSE NULL END) AS batter_balls_faced
FROM
  ball_by_ball AS T1
WHERE
  T1.bowler = 'Mohammed Shami' OR T1.batter = 'Mohammed Shami';"""

df = pd.read_sql_query(query, conn)
print(df)
conn.close()