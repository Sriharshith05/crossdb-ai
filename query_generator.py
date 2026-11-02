# query_generator.py  ← UPDATED (conversation memory aware)

import json
from google import genai
from config import GEMINI_API_KEY
from schema_extractor import get_sqlite_schema, get_mongodb_schema

client = genai.Client(api_key=GEMINI_API_KEY)


def generate_database_queries(user_question: str, conversation_history: str = ""):
    print("Extracting live schemas from databases...")
    sql_schema   = get_sqlite_schema()
    nosql_schema = get_mongodb_schema()

    # Inject conversation history so AI resolves follow-up references
    # e.g. "what about Bob?" after asking about Alice
    history_block = ""
    if conversation_history:
        history_block = f"""
Previous conversation (for context only — use it to resolve pronouns or references):
{conversation_history}
"""

    system_prompt = f"""
You are CrossDB AI, an intelligent cross-database query router.
Your job is to take a user's natural language question and generate
the appropriate queries for SQLite and MongoDB.

SQL Schema (SQLite):
{json.dumps(sql_schema, indent=2)}

NoSQL Schema (MongoDB - Collection: interview_feedbacks):
{json.dumps(nosql_schema, indent=2)}
{history_block}
    Rules:
    1. Generate a valid SQLite SELECT query. Always include the student name column.
    2. Generate the MongoDB filter document ONLY — no wrapper keys.
    3. CRITICAL: If the MongoDB filter needs a value from SQL results,
       use placeholder format: "SQL_RESULT_columnname"
       Example: {{"student_id": "SQL_RESULT_student_id"}}
    4. NEVER filter inside nested arrays (no $elemMatch, no $in on arrays).
       Always fetch the full document using only top-level fields like student_id.
    5. When filtering by a person's name, always use SQL LIKE with wildcards
       (e.g., WHERE name LIKE '%Alice%') instead of exact equality (=), since
       users often refer to people by first name only.
    6. Return ONLY valid JSON with exactly two keys:
       "sql_query" and "mongodb_query". No markdown, no explanation.
"""

    prompt = f"{system_prompt}\n\nUser Question: {user_question}"
    print("Sending question to AI...")

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        clean = response.text.replace("```json", "").replace("```", "").strip()
        queries = json.loads(clean)
        return queries

    except json.JSONDecodeError as e:
        print(f"[ERROR] AI returned invalid JSON: {e}")
        print(f"Raw AI Output: {response.text}")
        return None

    except Exception as e:
        print(f"[ERROR] Query generation failed: {e}")
        return None