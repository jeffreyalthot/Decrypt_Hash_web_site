import os
import sqlite3
import threading
import time
from pathlib import Path

import requests
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / 'data.db'
FINDED_TXT_PATH = BASE_DIR / 'finded.txt'


def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout = 30000')
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS wallets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            btc_address TEXT NOT NULL UNIQUE,
            hash_value TEXT NOT NULL,
            balance_satoshis INTEGER DEFAULT 0,
            balance_updated_at TEXT
        )
        '''
    )
    columns = {
        row['name'] for row in conn.execute('PRAGMA table_info(wallets)').fetchall()
    }
    if 'balance_satoshis' not in columns:
        conn.execute('ALTER TABLE wallets ADD COLUMN balance_satoshis INTEGER DEFAULT 0')
    if 'balance_updated_at' not in columns:
        conn.execute('ALTER TABLE wallets ADD COLUMN balance_updated_at TEXT')
    conn.commit()
    conn.close()


def fetch_btc_balance_satoshis(address: str) -> int:
    response = requests.get(
        f'https://bitcoin.atomicwallet.io/api/v2/address/{address}',
        timeout=8,
    )
    response.raise_for_status()
    data = response.json()

    for key in ('balance', 'confirmedBalance', 'finalBalance'):
        value = data.get(key)
        if value is not None:
            return int(str(value))

    raise ValueError('Balance non trouvée dans la réponse API')


def format_balance(satoshis: int | None) -> str:
    try:
        satoshis = int(satoshis or 0)
        return f'{satoshis / 100_000_000:.8f} BTC'
    except (ValueError, TypeError):
        return 'Balance indisponible'


def refresh_all_wallet_balances():
    conn = get_db_connection()
    wallets = conn.execute('SELECT id, btc_address FROM wallets').fetchall()

    for wallet in wallets:
        try:
            satoshis = fetch_btc_balance_satoshis(wallet['btc_address'])
            conn.execute(
                'UPDATE wallets SET balance_satoshis = ?, balance_updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (satoshis, wallet['id']),
            )
        except (requests.RequestException, ValueError, TypeError):
            continue

    conn.commit()
    conn.close()


def start_balance_refresh_scheduler():
    def _run():
        while True:
            refresh_all_wallet_balances()
            time.sleep(3600)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/wallets')
def list_wallets():
    conn = get_db_connection()
    wallets = conn.execute(
        'SELECT btc_address, hash_value, balance_satoshis FROM wallets ORDER BY id DESC'
    ).fetchall()
    conn.close()

    wallet_items = []
    for wallet in wallets:
        wallet_items.append(
            {
                'btc_address': wallet['btc_address'],
                'hash_value': wallet['hash_value'],
                'balance': format_balance(wallet['balance_satoshis']),
            }
        )

    return render_template('list_wallet.html', wallets=wallet_items)


@app.route('/submit-earn', methods=['GET', 'POST'])
def submit_earn():
    if request.method == 'POST':
        receiver_address = request.form.get('receiver_address', '').strip()
        hash_value = request.form.get('hash_value', '').strip()
        password_finded = request.form.get('password_finded', '').strip()

        if receiver_address and hash_value and password_finded:
            with open(FINDED_TXT_PATH, 'a', encoding='utf-8') as file:
                file.write(f'{receiver_address} {hash_value} {password_finded}\n')

        return redirect(url_for('submit_earn'))

    return render_template('submit_earn.html')


_background_jobs_started = False


def start_background_jobs_once():
    global _background_jobs_started
    if _background_jobs_started:
        return

    init_db()
    refresh_all_wallet_balances()
    start_balance_refresh_scheduler()
    _background_jobs_started = True


if __name__ == '__main__':
    # In debug mode, Flask's reloader runs this module twice.
    # Only start background jobs in the serving process.
    debug_mode = True
    if (not debug_mode) or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        start_background_jobs_once()
    app.run(debug=debug_mode)
else:
    start_background_jobs_once()
