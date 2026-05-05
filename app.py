import os
import sqlite3
from pathlib import Path

import requests
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / 'data.db'
FINDED_TXT_PATH = BASE_DIR / 'finded.txt'


def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS wallets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            btc_address TEXT NOT NULL UNIQUE,
            hash_value TEXT NOT NULL
        )
        '''
    )
    conn.commit()
    conn.close()


def get_btc_balance(address: str) -> str:
    try:
        response = requests.get(
            f'https://blockchain.info/rawaddr/{address}',
            timeout=8,
        )
        response.raise_for_status()
        data = response.json()
        satoshis = int(data.get('final_balance', 0))
        return f'{satoshis / 100_000_000:.8f} BTC'
    except (requests.RequestException, ValueError, TypeError):
        return 'Balance indisponible'


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/wallets')
def list_wallets():
    conn = get_db_connection()
    wallets = conn.execute('SELECT btc_address, hash_value FROM wallets ORDER BY id DESC').fetchall()
    conn.close()

    wallet_items = []
    for wallet in wallets:
        wallet_items.append(
            {
                'btc_address': wallet['btc_address'],
                'hash_value': wallet['hash_value'],
                'balance': get_btc_balance(wallet['btc_address']),
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


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
else:
    init_db()
