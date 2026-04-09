import os, psycopg2
from dotenv import load_dotenv
load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'suppliers' ORDER BY ordinal_position")
for row in cur.fetchall():
    print(f"{row[0]:40s} {row[1]}")
cur.close()
conn.close()

# anything
