import psycopg2
from psycopg2.extras import RealDictCursor, DictCursor

class Database:
    def __init__(self):
        self.conn = None
    
    def connect(self):
        if self.conn is None:
            try:
                self.conn = psycopg2.connect(
                    database="d192h6q6nuqtvm", 
                    user="qgxitkvldvufuq", 
                    password="09a67a8ba28ae881bd1d2dbeb019ec4ea690f249601eafa1d0d5e63d1fb61013", 
                    host="ec2-52-205-45-219.compute-1.amazonaws.com", 
                    port="5432"
                )
                # self.conn = psycopg2.connect(
                #     database="musicbot_test", 
                #     user="postgres", 
                #     password="123", 
                #     host="127.0.0.1", 
                #     port="5432"
                # )
            except psycopg2.DatabaseError as e:
                raise e

    def create_table(self):
        self.connect()
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            #cur.execute("DROP TABLE IF EXISTS USERS" )
            cur.execute(
                '''CREATE TABLE IF NOT EXISTS USERS
                (USERKEY     SERIAL PRIMARY KEY     NOT NULL,
                USERID             TEXT             NOT NULL,
                PLAYLISTS         JSONB               );''')

            self.conn.commit()

    def select_rows_dict_cursor(self, query, fetchall):
        self.connect()
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(query)

            if fetchall:
                records = cur.fetchall()
            else:
                records = cur.fetchone()
        cur.close()
        return records
    
    def commit_query(self, query):
        self.connect()   
        with self.conn.cursor() as cur:
            cur.execute(query)
            self.conn.commit()
            cur.close()

def start_database():
    database = Database()
    database.connect()
    database.create_table()

    return database