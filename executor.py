import sqlite3
import json
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from config import SQLITE_DB_PATH, MONGO_URI, MONGO_DB_NAME, MONGO_COLLECTION
 

def _is_safe_sql(query: str) -> bool:
    stripped = query.strip().upper()
    dangerous = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "TRUNCATE", "CREATE"]
    if not stripped.startswith("SELECT"):
        return False
    for keyword in dangerous:
        if keyword in stripped:
            return False
    return True
 
 
def _run_sql(query: str):
    """Runs any safe SQL query and returns list of dicts."""
    if not _is_safe_sql(query):
        print(f"[BLOCKED] Unsafe SQL rejected: {query}")
        return []
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    except Exception as e:
        print(f"[ERROR] SQL execution failed: {e}")
        return []
 
 
def execute_pipeline(queries):
    sql_query            = queries.get("sql_query", "").strip()
    mongo_query_template = queries.get("mongodb_query", {})
 
    # Parse Mongo query if returned as string
    if isinstance(mongo_query_template, str):
        try:
            mongo_query_template = json.loads(mongo_query_template)
        except Exception as e:
            print(f"[ERROR] Could not parse Mongo query: {e}")
            return {"error": "Failed to parse MongoDB query"}
 
    # ── Step 1: Run SQL ──────────────────────────────────
    print("\n--- 1. Executing SQL Query ---")
    print(f"Query: {sql_query}")
    sql_results = _run_sql(sql_query)
    print(f"SQL Results: {sql_results}")
 
    if not sql_results:
        return {"sql_data": [], "mongo_data": []}
 
    # ── Step 2: Run MongoDB ──────────────────────────────
    print("\n--- 2. Executing MongoDB Query ---")
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        client.admin.command('ping')
        db         = client[MONGO_DB_NAME]
        collection = db[MONGO_COLLECTION]
    except ConnectionFailure:
        print("[ERROR] MongoDB is not reachable.")
        return {"sql_data": sql_results, "mongo_data": [], "error": "MongoDB connection failed"}
    except Exception as e:
        print(f"[ERROR] MongoDB setup failed: {e}")
        return {"sql_data": sql_results, "mongo_data": [], "error": str(e)}
 
    mongo_results = []
    for row in sql_results:
        final_mongo_query = {}
        for key, value in mongo_query_template.items():
            if isinstance(value, str) and value.startswith("SQL_RESULT_"):
                col = value.replace("SQL_RESULT_", "")
                final_mongo_query[key] = row.get(col, value)
            else:
                final_mongo_query[key] = value
 
        print(f"Final Mongo Query: {final_mongo_query}")
        docs = list(collection.find(final_mongo_query, {'_id': 0}))
        mongo_results.extend(docs)
 
    client.close()
    print(f"MongoDB Results: {mongo_results}")
 
    # ── Step 3: 3-way join — resolve job_id → jobs table ─
    # If MongoDB returned job_id fields, look them up in the jobs table
    enriched_mongo = []
    for doc in mongo_results:
        enriched = dict(doc)
        job_id = doc.get("job_id")
        if job_id is not None:
            print(f"\n--- 2b. Resolving job_id {job_id} from jobs table ---")
            job_rows = _run_sql(f"SELECT * FROM jobs WHERE job_id = {int(job_id)}")
            if job_rows:
                enriched["job_details"] = job_rows[0]
                print(f"Job Details: {job_rows[0]}")
        enriched_mongo.append(enriched)
 
    return {
        "sql_data":   sql_results,
        "mongo_data": enriched_mongo
    }
 
 
if __name__ == "__main__":
    from query_generator import generate_database_queries
    question = "What role is Alice Smith applying for and what did she score in technical round?"
    print(f"Testing: '{question}'")
    queries = generate_database_queries(question)
    if queries:
        result = execute_pipeline(queries)
        print("\n--- Final Data ---")
        print(json.dumps(result, indent=2))