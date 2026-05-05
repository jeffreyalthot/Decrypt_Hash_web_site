# Decrypt Hash Website

## Lancer le site
```bash
python app.py
```

## Gérer les wallets via terminal
```bash
python wallet_manager.py add --address "BTC_ADDRESS" --hash "HASH_VALUE"
python wallet_manager.py remove --address "BTC_ADDRESS"
python wallet_manager.py list
```

Le fichier `data.db` est créé automatiquement s'il n'existe pas.
