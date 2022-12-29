import sqlite3 as sql
from pathlib import Path

DB_NAME = "kindle_price_tracker.sqlite"


def create_database() -> None:
    con, cur = load_database()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS book
            (
                ASIN TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                lowest_price FLOAT,
                lowest_price_timestamp DATETIME
            );
    """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user
            (
                name TEXT NOT NULL,
                number INTEGER PRIMARY KEY
            );
    """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_books
            (
                number INTEGER,
                ASIN TEXT,
                FOREIGN KEY(number) REFERENCES user(number),
                FOREIGN KEY(ASIN) REFERENCES book(ASIN),
                UNIQUE(number, ASIN)
            );
    """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS price_data
        (
            ASIN TEXT,
            price FLOAT,
            timestamp DATETIME,
            FOREIGN KEY(ASIN) REFERENCES book(ASIN),
            UNIQUE(ASIN, timestamp)
            ON CONFLICT REPLACE
        );
    """
    )

    close_database(con)


def load_database() -> tuple[sql.Connection, sql.Cursor]:
    con = sql.connect(DB_NAME)
    con.execute("PRAGMA foreign_keys = ON")
    cur = con.cursor()

    return con, cur


def close_database(con: sql.Connection) -> None:
    con.commit()
    con.close()


def insert_book(asin, title):
    con, cur = load_database()

    try:
        cur.execute(
            """
            INSERT INTO book (ASIN, title)
            VALUES (?, ?)
        """,
            (asin, title),
        )
    except Exception as e:
        close_database(con)
        raise e
    else:
        close_database(con)


def update_lowest_price(asin, price, timestamp):
    con, cur = load_database()

    try:
        cur.execute(
            """
            UPDATE book
            SET lowest_price = ?,
                lowest_price_timestamp = ?
            WHERE ASIN = ?
        """,
            (price, timestamp, asin),
        )
    except Exception as e:
        close_database(con)
        raise e
    else:
        close_database(con)


def get_books() -> list[tuple[str, str, str, str]]:
    con, cur = load_database()

    try:
        cur.execute(
            """
            SELECT * FROM book
        """
        )
        books = cur.fetchall()
    except Exception as e:
        close_database(con)
        raise e
    else:
        close_database(con)
        return books


def get_lowest_price(asin) -> float:
    con, cur = load_database()

    try:
        cur.execute(
            """
            SELECT lowest_price FROM book
            WHERE ASIN = ?
        """,
            (asin,),
        )
        price = cur.fetchone()
    except Exception as e:
        close_database(con)
        raise e
    else:
        close_database(con)
        return price[0]


def insert_user(name, number) -> None:
    con, cur = load_database()

    try:
        cur.execute(
            """
            INSERT INTO user
            VALUES (?, ?)
        """,
            (name, number),
        )
    except Exception as e:
        close_database(con)
        raise e
    else:
        close_database(con)


def insert_user_book(number, asin):
    con, cur = load_database()

    try:
        cur.execute(
            """
            INSERT INTO user_books
            VALUES (?, ?)
        """,
            (number, asin),
        )
    except Exception as e:
        close_database(con)
        raise e
    else:
        close_database(con)


def get_users_with_book(asin) -> list[int]:
    con, cur = load_database()

    try:
        cur.execute(
            """
            SELECT number FROM user_books
            WHERE ASIN = ?
        """,
            (asin,),
        )
        users = cur.fetchall()
        users = [user[0] for user in users]
    except Exception as e:
        close_database(con)
        raise e
    else:
        close_database(con)
        return users


def insert_price_data(asin, price, timestamp):
    con, cur = load_database()

    try:
        cur.execute(
            """
            INSERT INTO price_data
            VALUES (?, ?, ?)
        """,
            (asin, price, timestamp),
        )
    except Exception as e:
        close_database(con)
        raise e
    else:
        close_database(con)


def get_price_data() -> list[tuple[str, float, str]]:
    con, cur = load_database()

    try:
        cur.execute(
            """
            SELECT * FROM price_data
        """
        )
        data = cur.fetchall()
    except Exception as e:
        close_database(con)
        raise e
    else:
        close_database(con)
        return data


def get_tables() -> list[str]:
    con, cur = load_database()

    try:
        cur.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table'
        """
        )
        tables = cur.fetchall()
        tables = [table[0] for table in tables]
    except Exception as e:
        close_database(con)
        raise e
    else:
        close_database(con)
        return tables


def get_table_columns(table: str) -> list[str]:
    con, cur = load_database()

    try:
        cur.execute(
            f"""
            SELECT * FROM {table}
        """
        )
        columns = [description[0] for description in cur.description]
    except Exception as e:
        close_database(con)
        raise e
    else:
        close_database(con)
        return columns


def get_table_data(table: str) -> list[tuple]:
    con, cur = load_database()

    try:
        cur.execute(
            f"""
            SELECT * FROM {table}
        """
        )
        data = cur.fetchall()
    except Exception as e:
        close_database(con)
        raise e
    else:
        close_database(con)
        return data


def export_all_tables_to_csv():
    con, _ = load_database()

    if not Path("export").exists():
        Path("export").mkdir()

    try:
        for table in get_tables():
            data = get_table_data(table)
            columns = get_table_columns(table)

            with open(Path("export") / f"{table}.csv", "w") as f:
                f.write(",".join(columns))
                f.write("\n")
                for row in data:
                    f.write(
                        ",".join(f'"{x}"' if "," in str(x) else str(x) for x in row)
                    )
                    f.write("\n")
    except Exception as e:
        close_database(con)
        raise e
