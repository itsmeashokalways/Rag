import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "rag_agent")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")


def run_init_db():
    try:
        # =========================
        # 1. CONNECT TO DEFAULT DB
        # =========================
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database="postgres",  # 🔥 IMPORTANT
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # =========================
        # 2. CHECK IF DB EXISTS
        # =========================
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (POSTGRES_DB,)
        )
        exists = cursor.fetchone()

        # =========================
        # 3. CREATE DB IF NOT EXISTS
        # =========================
        if not exists:
            cursor.execute(f'CREATE DATABASE "{POSTGRES_DB}"')
            print(f"Database '{POSTGRES_DB}' created")
        else:
            print(f"Database '{POSTGRES_DB}' already exists")

        cursor.close()
        conn.close()

        # =========================
        # 4. CONNECT TO TARGET DB
        # =========================
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        conn.autocommit = True
        cursor = conn.cursor()

        print("Connected to target database")

        # =========================
        # 5. RUN SQL FILE
        # =========================
        with open("Scripts/db_init.sql", "r") as file:
            sql_script = file.read()

        cursor.execute(sql_script)

        print("Database initialized successfully")

        cursor.close()
        conn.close()

    except Exception as e:
        print("Error:", e)


if __name__ == "__main__":
    run_init_db()