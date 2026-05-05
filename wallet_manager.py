import argparse
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / 'data.db'


def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
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


def add_wallet(address: str, hash_value: str):
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute(
        'INSERT OR REPLACE INTO wallets (btc_address, hash_value) VALUES (?, ?)',
        (address, hash_value),
    )
    conn.commit()
    conn.close()
    print(f'Wallet ajouté/mis à jour: {address}')


def remove_wallet(address: str):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.execute('DELETE FROM wallets WHERE btc_address = ?', (address,))
    conn.commit()
    conn.close()
    if cursor.rowcount:
        print(f'Wallet retiré: {address}')
    else:
        print(f'Aucun wallet trouvé pour: {address}')


def list_wallets():
    conn = sqlite3.connect(DATABASE_PATH)
    rows = conn.execute('SELECT btc_address, hash_value FROM wallets ORDER BY id DESC').fetchall()
    conn.close()
    if not rows:
        print('Aucun wallet en base.')
        return
    for address, hash_value in rows:
        print(f'{address} | {hash_value}')


def main():
    parser = argparse.ArgumentParser(description='Gestion des wallets pour Decrypt Hash')
    subparsers = parser.add_subparsers(dest='command', required=True)

    add_parser = subparsers.add_parser('add', help='Ajouter ou mettre à jour un wallet')
    add_parser.add_argument('--address', required=True, help='Adresse Bitcoin')
    add_parser.add_argument('--hash', required=True, dest='hash_value', help='Hash à associer')

    remove_parser = subparsers.add_parser('remove', help='Retirer un wallet par adresse')
    remove_parser.add_argument('--address', required=True, help='Adresse Bitcoin à retirer')

    subparsers.add_parser('list', help='Lister les wallets')

    args = parser.parse_args()
    init_db()

    if args.command == 'add':
        add_wallet(args.address, args.hash_value)
    elif args.command == 'remove':
        remove_wallet(args.address)
    elif args.command == 'list':
        list_wallets()


if __name__ == '__main__':
    main()
