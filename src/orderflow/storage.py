import sqlite3


def connect_database(path=":memory:"):
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, email TEXT, total INT)")
    return connection


def find_orders_by_email(connection, email):
    query = "SELECT id, email, total FROM orders WHERE email = ?"
    return connection.execute(query, (email,)).fetchall()


def save_order(connection, email, total):
    connection.execute("INSERT INTO orders(email, total) VALUES (?, ?)", (email, total))
    connection.commit()
