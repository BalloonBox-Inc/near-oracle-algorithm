from dotenv import load_dotenv
from icecream import ic
from os import getenv
import psycopg2
load_dotenv()


DB_URI = getenv('DATABASE_URL').replace(
    '@', ':').replace('/', ':').split(':')[3:]

USER, PASSWORD, HOST, PORT, DATABASE = [DB_URI[i] for i in tuple(range(5))]


def add_row_to_table(tablename, obj):
    '''
    tablename [string]: table name
    obj [object]: object of column-value pair

    '''
    try:
        metadata = ' VARCHAR(255), '.join(list(obj.keys())) + ' VARCHAR(255)'
        columns = ', '.join(list(obj.keys()))
        values = "'" + "', '".join(str(e) for e in list(obj.values())) + "'"

        with psycopg2.connect(user=USER, password=PASSWORD, host=HOST, port=PORT, database=DATABASE) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f'CREATE TABLE IF NOT EXISTS {tablename} ({metadata})')
                conn.commit()
                cursor.execute(
                    f'INSERT INTO {tablename} ({columns}) VALUES ({values})')
                conn.commit()

    except (Exception, psycopg2.Error) as e:
        ic(str(e))
    return
