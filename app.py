# app.py  ← UPDATED (Flask Web API + conversation memory)

import uuid
from flask import Flask, request, jsonify, render_template, session
from google import genai

from config import GEMINI_API_KEY
from query_generator import generate_database_queries
from executor import execute_pipeline
from memory import get_history, add_message, clear_history, format_history_for_prompt

app = Flask(__name__)
app.secret_key = "crossdb-secret-key-change-in-prod"  # needed for Flask sessions

client = genai.Client(api_key=GEMINI_API_KEY)


# ── Answer Synthesis ─────────────────────────────────────────────────
def synthesize_answer(question, raw_data, conversation_history=""):
    sql_data   = raw_data.get("sql_data", [])
    mongo_data = raw_data.get("mongo_data", [])

    if not sql_data and not mongo_data:
        return "I couldn't find any data for that question. Please try rephrasing."

    # Build plain-English summary (keeps name linked to all fields)
    summaries = []
    for i, row in enumerate(sql_data):
        parts = []
        for key, value in row.items():
            parts.append(f"{key} is {value}")

        if i < len(mongo_data):
            doc = mongo_data[i]
            job = doc.get("job_details")
            if job:
                parts.append(f"applying to company {job.get('company', 'N/A')}")
                parts.append(f"for the role of {job.get('role', 'N/A')}")
                parts.append(f"with a package of {job.get('package', 'N/A')}")
            for r in doc.get("rounds", []):
                rtype  = r.get("type", "Unknown")
                score  = r.get("score")
                status = r.get("status")
                notes  = r.get("notes")
                if score  is not None: parts.append(f"{rtype} round score is {score}")
                if status is not None: parts.append(f"{rtype} round status is {status}")
                if notes  is not None: parts.append(f"{rtype} round notes: {notes}")

        summaries.append(". ".join(parts) + ".")

    data_summary = "\n".join(summaries)

    history_block = ""
    if conversation_history:
        history_block = f"""
Previous conversation (for context):
{conversation_history}
"""

    prompt = f"""You are CrossDB AI, a helpful data assistant.
{history_block}
The following facts were retrieved from a database:

{data_summary}

Question: {question}

Answer in 2-3 clear sentences using only the facts above.
Do not say data is missing. Do not mention databases, SQL, or MongoDB.
Answer:"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"Error generating answer: {e}"


# ── Routes ────────────────────────────────────────────────────────────

@app.route("/")
def index():
    # Assign a unique session ID to each browser tab
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
def ask():
    data     = request.get_json()
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "Question cannot be empty."}), 400

    # Get or create session ID
    session_id = session.get("session_id", str(uuid.uuid4()))
    session["session_id"] = session_id

    # Fetch conversation history for context
    history = format_history_for_prompt(session_id)

    # Step 1: Generate queries (with memory context)
    queries = generate_database_queries(question, conversation_history=history)
    if not queries:
        return jsonify({"error": "Could not generate queries. Please rephrase."}), 500

    # Step 2: Execute pipeline
    raw_data = execute_pipeline(queries)
    if "error" in raw_data:
        return jsonify({"error": raw_data["error"]}), 500

    # Step 3: Synthesize answer (with memory context)
    answer = synthesize_answer(question, raw_data, conversation_history=history)

    # Step 4: Save to memory
    add_message(session_id, "user",      question)
    add_message(session_id, "assistant", answer)

    # Step 5: Return everything to the frontend
    return jsonify({
        "answer":       answer,
        "sql_query":    queries.get("sql_query", ""),
        "mongo_query":  str(queries.get("mongodb_query", {})),
        "sql_results":  raw_data.get("sql_data", []),
        "mongo_results": raw_data.get("mongo_data", []),
        "history":      get_history(session_id)
    })


@app.route("/clear", methods=["POST"])
def clear():
    session_id = session.get("session_id")
    if session_id:
        clear_history(session_id)
    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)