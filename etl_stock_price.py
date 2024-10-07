# -*- coding: utf-8 -*-
"""ETL_Stock_Price.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1QCabdAZB3TqUTqGYVBKBv5Vb1PRvYItW
"""

from airflow import DAG
from airflow.models import Variable
from airflow.decorators import task
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook

from datetime import timedelta
from datetime import datetime
import snowflake.connector
import requests

def return_snowflake_conn():

    hook = SnowflakeHook(snowflake_conn_id='snowflake_connection_id')

    conn = hook.get_conn()
    return conn.cursor()

@task
def extract(url):
    res = requests.get(url)
    data = res.json()
    results = []
    for d in data["Time Series (Daily)"]:
      results.append(data["Time Series (Daily)"][d])
      daily_info = data["Time Series (Daily)"][d]
      daily_info['6. date'] = d
      results.append(daily_info)
    return results[-90:]

@task
def transform(results):
 for r in results:
        open =   r['1. open'].replace("'", "''")
        high =   r['2. high'].replace("'", "''")
        low =    r['3. low'].replace("'", "''")
        close =  r['4. close'].replace("'", "''")
        volume = r['5. volume'].replace("'", "''")
        date =   r['6. date'].replace("'", "''")
        return results

@task
def load(con, records, target_table):
    try:
      con.execute("BEGIN")
      con.execute(f"""CREATE OR REPLACE TABLE {target_table} (
              open DECIMAL(10, 4) NOT NULL,
              high DECIMAL(10, 4) NOT NULL,
              low DECIMAL(10, 4) NOT NULL,
              close DECIMAL(10, 4) NOT NULL,
              volume BIGINT NOT NULL,
              date DATE NOT NULL,
              PRIMARY KEY (date)
          )""")
      for r in records:
              open =   r['1. open'].replace("'", "''")
              high =   r['2. high'].replace("'", "''")
              low =    r['3. low'].replace("'", "''")
              close =  r['4. close'].replace("'", "''")
              volume = r['5. volume'].replace("'", "''")
              date =   r['6. date'].replace("'", "''")
              sql = f"INSERT INTO {target_table} (open, high, low, close, volume, date) VALUES ('{open}', '{high}', '{low}', '{close}', '{volume}', '{date}')"
              con.execute(sql)
      con.execute("COMMIT")
    except Exception as e:
          con.execute("ROLLBACK")
          raise(e)

with DAG(
    dag_id = 'ETL_Stockprice',
    start_date = datetime(2024,7,10),
    catchup=False,
    tags=['ETL'],
    schedule = '30 12 * * *'
) as dag:
    target_table = "dev.raw_data.stock_price"
    url = Variable.get("url")
    cur = return_snowflake_conn()

    data = extract(url)
    lines = transform(data)
    load(cur, lines, target_table)