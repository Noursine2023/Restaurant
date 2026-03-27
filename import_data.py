"""
import_data.py
-------------
Importe le fichier restaurants.json dans MongoDB (restaurantDB > restaurants).
Les dates au format {"$date": timestamp_ms} sont converties en datetime Python.

Usage :
    python import_data.py
    python import_data.py --file /chemin/vers/restaurants.json
    python import_data.py --clear   # vide la collection avant d'importer
"""

import json
import sys
import argparse
from datetime import datetime, timezone
from pymongo import MongoClient, errors

# ── CONFIG ──────────────────────────────────────────────────────────────────
MONGO_URI   = "mongodb://localhost:27017/"
DB_NAME     = "restaurantDB"
COLLECTION  = "restaurants"
DEFAULT_FILE = "restaurants.json"
BATCH_SIZE  = 500          # documents insérés par lot
# ────────────────────────────────────────────────────────────────────────────


def parse_value(v):
    """Convertit récursivement les valeurs MongoDB Extended JSON."""
    if isinstance(v, dict):
        # Date MongoDB : {"$date": 1393804800000}
        if "$date" in v and len(v) == 1:
            ts = v["$date"]
            return datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
        return {k: parse_value(val) for k, val in v.items()}
    if isinstance(v, list):
        return [parse_value(i) for i in v]
    return v


def load_and_import(filepath: str, clear: bool = False):
    # Connexion
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        client.server_info()
    except errors.ServerSelectionTimeoutError:
        print("❌ Impossible de se connecter à MongoDB.")
        print("   Vérifiez que le container Docker tourne : docker start mongo-resto")
        sys.exit(1)

    db  = client[DB_NAME]
    col = db[COLLECTION]

    if clear:
        deleted = col.delete_many({}).deleted_count
        print(f"🗑  Collection vidée ({deleted} documents supprimés)")

    # Lecture du fichier
    print(f"📂 Lecture de {filepath}...")
    docs = []
    errors_count = 0

    with open(filepath, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
                doc = parse_value(raw)
                docs.append(doc)
            except json.JSONDecodeError as e:
                errors_count += 1
                if errors_count <= 5:
                    print(f"   ⚠ Ligne {line_num} ignorée : {e}")

    print(f"✅ {len(docs)} documents chargés ({errors_count} lignes ignorées)")

    # Insertion par lots
    print(f"⬆  Insertion dans {DB_NAME}.{COLLECTION}...")
    inserted_total = 0

    for i in range(0, len(docs), BATCH_SIZE):
        batch = docs[i : i + BATCH_SIZE]
        result = col.insert_many(batch, ordered=False)
        inserted_total += len(result.inserted_ids)
        pct = inserted_total / len(docs) * 100
        print(f"   {inserted_total}/{len(docs)} ({pct:.0f}%)", end="\r")

    print(f"\n🎉 Import terminé — {inserted_total} documents insérés dans '{COLLECTION}'")
    print(f"   Total dans la collection : {col.count_documents({})}")
    client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Importe restaurants.json dans MongoDB")
    parser.add_argument("--file",  default=DEFAULT_FILE, help="Chemin vers le fichier JSON")
    parser.add_argument("--clear", action="store_true",  help="Vider la collection avant import")
    args = parser.parse_args()

    load_and_import(args.file, args.clear)
