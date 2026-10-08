import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).with_name("database.sqlite")


def create_database() -> None:
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.executescript(
        """
        DROP TABLE IF EXISTS sales;
        DROP TABLE IF EXISTS customers;
        DROP TABLE IF EXISTS employees;

        CREATE TABLE sales (
            id INTEGER PRIMARY KEY,
            region TEXT NOT NULL,
            product TEXT NOT NULL,
            revenue REAL NOT NULL,
            date TEXT NOT NULL,
            units_sold INTEGER NOT NULL
        );

        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            industry TEXT NOT NULL,
            churn_date TEXT,
            satisfaction_score REAL NOT NULL
        );

        CREATE TABLE employees (
            id INTEGER PRIMARY KEY,
            department TEXT NOT NULL,
            satisfaction_score REAL NOT NULL,
            tenure_years REAL NOT NULL
        );
        """
    )

    cursor.executemany(
        """
        INSERT INTO sales (region, product, revenue, date, units_sold)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("East", "Platform", 125000, "2025-01-15", 25),
            ("West", "Platform", 98000, "2025-01-20", 20),
            ("North", "Analytics", 87000, "2025-01-22", 18),
            ("South", "Security", 112000, "2025-02-10", 22),
            ("East", "Analytics", 131000, "2025-02-14", 27),
            ("West", "Security", 104000, "2025-02-19", 21),
            ("North", "Platform", 119000, "2025-03-05", 24),
            ("South", "Analytics", 93000, "2025-03-11", 19),
            ("East", "Security", 145000, "2025-03-18", 29),
            ("West", "Platform", 108000, "2025-04-08", 22),
            ("North", "Security", 101000, "2025-04-16", 20),
            ("South", "Platform", 116000, "2025-04-23", 23),
        ],
    )

    cursor.executemany(
        """
        INSERT INTO customers
            (name, industry, churn_date, satisfaction_score)
        VALUES (?, ?, ?, ?)
        """,
        [
            ("Customer A", "Healthcare", None, 4.7),
            ("Customer B", "Financial Services", None, 4.3),
            ("Customer C", "Retail", "2025-02-28", 2.8),
            ("Customer D", "Technology", None, 4.5),
            ("Customer E", "Manufacturing", "2025-03-31", 3.1),
            ("Customer F", "Public Sector", None, 4.1),
        ],
    )

    cursor.executemany(
        """
        INSERT INTO employees
            (department, satisfaction_score, tenure_years)
        VALUES (?, ?, ?)
        """,
        [
            ("Engineering", 4.2, 3.5),
            ("Engineering", 4.5, 5.0),
            ("Sales", 3.8, 2.0),
            ("Sales", 4.1, 4.5),
            ("Customer Success", 4.6, 6.0),
            ("Customer Success", 4.0, 1.5),
            ("Operations", 3.9, 7.0),
            ("Operations", 4.4, 3.0),
        ],
    )

    connection.commit()
    connection.close()
    print(f"Created SQLite database at {DATABASE_PATH}")


if __name__ == "__main__":
    create_database()
