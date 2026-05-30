import sqlite3
import pandas as pd
from pathlib import Path

CSV_FOLDER = "data_files"
DB_PATH = "ipl_auction.db"
conn = sqlite3.connect(DB_PATH)
csv_files = Path(CSV_FOLDER).glob("*.csv")

for file in csv_files:
    print(f"\nProcessing {file.name}")
    df = pd.read_csv(file)
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    for col in df.columns:
        # Try numeric conversion
        try:
            converted = pd.to_numeric(df[col])
            # Only replace if successful enough
            if converted.notna().sum() > 0:
                df[col] = converted
        except:
            pass
        # Try datetime conversion
        if "date" in col or "time" in col:
            try:
                df[col] = pd.to_datetime(df[col])
            except:
                pass
    table_name = file.stem.lower()
    df.to_sql(
        table_name,
        conn,
        if_exists="replace",
        index=False
    )
    print(f"✅ Created table: {table_name}")
conn.close()
print("\n🎉 Database ready")