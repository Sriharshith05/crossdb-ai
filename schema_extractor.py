
import sqlite3
import json
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# ✅ FIX 1: Import from config instead of hardcoding
from config import SQLITE_DB_PATH, MONGO_URI, MONGO_DB_NAME, MONGO_COLLECTION

def get_sqlite_schema(db_path=None):
    db_path = db_path or SQLITE_DB_PATH
    # ✅ FIX 2: Wrap in try/except — gives a clear error instead of crashing
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        schema = {}
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            schema[table_name] = [f"{col[1]} ({col[2]})" for col in columns]

        conn.close()
        return schema
    except Exception as e:
        print(f"[ERROR] Failed to read SQLite schema: {e}")
        return {}
    

# ── MongoDB Schema ──────────────────────────────────────
def get_mongodb_schema(db_name=None, collection_name=None, sample_size=10):
    db_name = db_name or MONGO_DB_NAME
    collection_name = collection_name or MONGO_COLLECTION

    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        # ✅ FIX 3: Ping first — fails fast with a clear message if Mongo is down
        client.admin.command('ping')
        db = client[db_name]
        collection = db[collection_name]

        # ✅ FIX 4: Sample 10 docs instead of 1 — captures all possible fields
        sample_docs = list(collection.find().limit(sample_size))
        if not sample_docs:
            return {"error": "Collection is empty"}
        
        def extract_keys(doc):
            inferred = {}
            for key, value in doc.items():
                if key == '_id':
                    continue
                if isinstance(value, dict):
                    inferred[key] = extract_keys(value)
                elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                    inferred[key] = [extract_keys(value[0])]
                else:
                    inferred[key] = type(value).__name__
            return inferred
        

        
        # ✅ FIX 5: Merge keys from ALL sampled docs (not just first one)
        merged_schema = {}
        for doc in sample_docs:
            merged_schema.update(extract_keys(doc))

        client.close()
        return merged_schema

    except ConnectionFailure:
        print("[ERROR] Could not connect to MongoDB. Is it running?")
        return {"error": "MongoDB connection failed"}
    except Exception as e:
        print(f"[ERROR] Failed to read MongoDB schema: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    print("--- SQL Schema ---")
    print(json.dumps(get_sqlite_schema(), indent=2))
    print("\n--- MongoDB Schema ---")
    print(json.dumps(get_mongodb_schema(), indent=2))