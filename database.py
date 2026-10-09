import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vulnlab.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(reset=False):
    if reset and os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except Exception as e:
            print(f"Error removing existing database: {e}")

    conn = get_db()
    cursor = conn.cursor()

    # 1. Users table (for Authentication Bypass, IDOR, UNION SQLi)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT,
        role TEXT NOT NULL,
        bio TEXT,
        secret_api_key TEXT,
        account_balance REAL DEFAULT 1000.00
    )
    ''')

    # 2. Products table (for Search SQLi & UNION extraction)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        description TEXT
    )
    ''')

    # 3. Comments table (for Stored XSS)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        author TEXT NOT NULL,
        comment TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 4. Sensitive Financial Records (for advanced SQLi UNION dump)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sensitive_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        credit_card TEXT NOT NULL,
        cvv TEXT NOT NULL,
        exp_date TEXT NOT NULL,
        vault_code TEXT NOT NULL
    )
    ''')

    # Check if data already seeded
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        # Seed Users
        users_data = [
            ('admin', 'SuperSecretAdminPass2026!', 'admin@vulnlab.local', 'administrator', 'Master system administrator with full access.', 'FLAG{admin_super_token_99x82}', 50000.00),
            ('alice', 'alice123', 'alice@cybersec.org', 'user', 'Security enthusiast learning web pentesting.', 'USER_TOKEN_ALICE_4481', 1250.50),
            ('bob', 'password1234', 'bob@builder.net', 'user', 'DevOps engineer tinkering with local servers.', 'USER_TOKEN_BOB_7719', 320.00),
            ('charlie', 'qwerty', 'charlie@underground.io', 'analyst', 'Security researcher and bug bounty hunter.', 'USER_TOKEN_CHARLIE_3391', 8900.25)
        ]
        cursor.executemany('''
        INSERT INTO users (username, password, email, role, bio, secret_api_key, account_balance)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', users_data)

        # Seed Products
        products_data = [
            ('Rubber Ducky USB', 'Hardware', 49.99, 'Keystroke injection hardware tool for covert red-team operations.'),
            ('Wi-Fi Pineapple Mark VII', 'Hardware', 119.99, 'Tactical wireless network auditing and reconnaissance device.'),
            ('HackRF One SDR', 'RF & Wireless', 349.00, 'Software defined radio peripheral capable of transmission and reception of radio signals.'),
            ('Flipper Zero Multi-tool', 'Hardware', 169.00, 'Portable multi-tool for geeks, pen-testers, and hardware tinkerers.'),
            ('Encrypted IronKey Drive 64GB', 'Storage', 89.95, 'Hardware-encrypted flash drive with military-grade tamper resistance.'),
            ('Blue Team Field Manual (BTFM)', 'Books', 24.99, 'Quick reference cybersecurity defensive operations manual.')
        ]
        cursor.executemany('''
        INSERT INTO products (name, category, price, description)
        VALUES (?, ?, ?, ?)
        ''', products_data)

        # Seed initial comments for Stored XSS
        comments_data = [
            ('Alice', 'Welcome to the VulnLab comment wall! Feel free to leave your thoughts.'),
            ('Bob', 'Hey everyone, remember to sanitize user inputs before rendering them!'),
            ('SecurityBot', 'System maintenance complete. All services running normal.')
        ]
        cursor.executemany('''
        INSERT INTO comments (author, comment)
        VALUES (?, ?)
        ''', comments_data)

        # Seed Sensitive Financial Records
        sensitive_data = [
            ('Sarah Connor', '4532-8921-3091-7782', '891', '11/28', 'VAULT-ALPHA-7721'),
            ('John Wick', '3782-8224-6310-0094', '421', '04/27', 'VAULT-CONTINENTAL-001'),
            ('Elliot Alderson', '5105-1051-0510-5105', '137', '09/29', 'FLAG{credit_card_vault_leaked_559}'),
            ('Thomas Anderson', '4000-1234-5678-9010', '707', '01/26', 'VAULT-MATRIX-NEO-33')
        ]
        cursor.executemany('''
        INSERT INTO sensitive_records (full_name, credit_card, cvv, exp_date, vault_code)
        VALUES (?, ?, ?, ?, ?)
        ''', sensitive_data)

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == '__main__':
    init_db(reset=True)
