import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL')
conn = psycopg2.connect(db_url)
cur = conn.cursor()

cur.execute('SELECT id, company_name, contact_email FROM suppliers')
rows = cur.fetchall()
for r in rows:
    print(f'ID: {r[0]}, Name: {r[1]}, Email: {r[2]}')

cur.execute("UPDATE suppliers SET contact_email = 'kartikakhade46@gmail.com'")
conn.commit()
print('Successfully updated contact emails to kartikakhade46@gmail.com')

cur.close()
conn.close()
