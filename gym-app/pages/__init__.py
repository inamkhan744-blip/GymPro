import sqlite3

def init_db():
    conn = sqlite3.connect("gym_saas.db")
    c = conn.cursor()

    # gyms
    c.execute("""
    CREATE TABLE IF NOT EXISTS gyms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        owner TEXT
    )
    """)

    # users
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gym_id INTEGER,
        username TEXT,
        password TEXT,
        role TEXT
    )
    """)

    # members
    c.execute("""
    CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gym_id INTEGER,
        name TEXT,
        phone TEXT,
        status TEXT,
        fee_due INTEGER
    )
    """)

    # chat history
    c.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gym_id INTEGER,
        user TEXT,
        message TEXT,
        response TEXT,
        time TEXT
    )
    """)

    conn.commit()
    conn.close()
