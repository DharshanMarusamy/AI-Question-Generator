import logging
import sqlite3
import pandas as pd
import requests
import json
import os
import re
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from pandas.errors import ParserError
from dotenv import load_dotenv
from time import sleep

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
if not load_dotenv():
    logger.error(".env file not found or could not be loaded")

app = Flask(__name__)
CORS(app)

# Initialize SQLite database
def get_db_connection():
    conn = sqlite3.connect("questions.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_title TEXT,
            time_limit INTEGER,
            instructions TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paper_id INTEGER,
            question TEXT,
            type TEXT,
            difficulty TEXT,
            blooms_level TEXT,
            topic TEXT,
            options TEXT,
            answer TEXT,
            FOREIGN KEY (paper_id) REFERENCES papers (id)
        )""")
        conn.commit()

init_db()

# AI-based question generation
def generate_questions(text, num_questions=10, question_types=None, difficulty="Medium", topic="General"):
    logger.info(f"Generating {num_questions} questions for topic: {topic}, difficulty: {difficulty}")

    questions = []
    if not question_types:
        question_types = ["Multiple Choice"]

    # Validate input
    if not text or not isinstance(text, str):
        logger.error("Invalid input text")
        return []
    if not isinstance(num_questions, int) or num_questions < 1 or num_questions > 50:
        logger.error("Invalid number of questions")
        return []

    # Sanitize text
    text = re.sub(r'[^\w\s.,!?]', '', text)

    # Single-line prompt
    prompt = f'Generate {num_questions} exam questions as JSON array: question, type ({", ".join(question_types)}), difficulty ({difficulty}), blooms_level (e.g., Remember), topic ({topic}), options (4 for Multiple Choice), answer. Text: "{text}"'

    # Check API key
    api_key = os.getenv("XAI_API_KEY")
    if not api_key or not api_key.startswith("sk-"):
        logger.error("XAI_API_KEY not set or invalid")
        return []

    # Hypothetical xAI API endpoint (replace with actual per xAI documentation)
    api_endpoint = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "grok-3",
        "messages": [
            {"role": "system", "content": "You are an expert question generator. Respond with valid JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 3000
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.info("Making API request...")
            response = requests.post(api_endpoint, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            result = response.json()

            # Flexible response parsing
            content = None
            if "choices" in result and result["choices"]:
                content = result["choices"][0].get("message", {}).get("content", "[]")
            elif "data" in result:
                content = result["data"].get("response", "[]")
            else:
                logger.error("Unexpected API response structure")
                return []

            ai_questions = json.loads(content) if isinstance(content, str) else content

            if not isinstance(ai_questions, list):
                logger.error("API response is not a list")
                return []

            for q in ai_questions[:num_questions]:
                if not isinstance(q, dict) or not all(key in q for key in ["question", "type", "answer"]):
                    logger.warning(f"Skipping invalid question: {q}")
                    continue
                questions.append({
                    "question": q.get("question", ""),
                    "type": q.get("type", question_types[0]),
                    "difficulty": q.get("difficulty", difficulty),
                    "blooms_level": q.get("blooms_level", "Understand"),
                    "topic": q.get("topic", topic),
                    "options": json.dumps(q.get("options", [])),
                    "answer": q.get("answer", "")
                })

            logger.info(f"Generated {len(questions)} questions")
            return questions

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            logger.error("API request timed out or failed to connect")
            if attempt == max_retries - 1:
                return []
            sleep(2 ** attempt)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429 and attempt < max_retries - 1:
                logger.warning("Rate limit exceeded, retrying...")
                sleep(2 ** attempt)
                continue
            logger.error(f"HTTP Error: {str(e)}")
            return []
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error parsing API response: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in API call: {str(e)}")
            return []

# API to generate and store questions
@app.route("/api/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json()
        if not data or not isinstance(data, dict):
            logger.error("Invalid JSON payload")
            return jsonify({"success": False, "message": "Invalid JSON payload"}), 400

        questions = data.get("questions", [])
        topic = data.get("topic", "General")
        num_questions = data.get("num_questions", 10)
        question_types = data.get("question_types", ["Multiple Choice"])
        difficulty = data.get("difficulty", "Medium")
        exam_title = data.get("exam_title", "Question Paper")
        time_limit = data.get("time_limit", 60)
        instructions = data.get("instructions", "")

        # Validate inputs
        if not questions or not isinstance(questions, list) or len(questions) == 0:
            logger.error("Invalid or empty questions")
            return jsonify({"success": False, "message": "Invalid or empty questions"}), 400
        if not isinstance(num_questions, int) or num_questions < 1 or num_questions > 100:
            logger.error("Invalid number of questions")
            return jsonify({"success": False, "message": "Invalid number of questions"}), 400
        if difficulty not in ["Easy", "Medium", "Hard"]:
            logger.error("Invalid difficulty level")
            return jsonify({"success": False, "message": "Invalid difficulty level"}), 400
        valid_question_types = ["Multiple Choice", "True/False", "Short Answer", "Essay", "Long Answer", "Fill in the Blanks", "Problem Solving"]
        if not question_types or not all(qt in valid_question_types for qt in question_types):
            logger.error("Invalid question types")
            return jsonify({"success": False, "message": "Invalid question types"}), 400

        # Generate and store questions
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO papers (exam_title, time_limit, instructions) VALUES (?, ?, ?)",
                (exam_title, time_limit, instructions)
            )
            paper_id = c.lastrowid
            try:
                # Process each question from the input
                for question_text in questions:
                    # Extract question details from the text
                    parts = question_text.split(" (")
                    if len(parts) >= 2:
                        question = parts[0]
                        details = parts[1].rstrip(")").split(", ")
                        q_type = details[0] if len(details) > 0 else question_types[0]
                        q_difficulty = details[1] if len(details) > 1 else difficulty
                        q_blooms = details[2] if len(details) > 2 else "Understand"
                        q_topic = details[3] if len(details) > 3 else topic
                        
                        c.execute(
                            "INSERT INTO questions (paper_id, question, type, difficulty, blooms_level, topic, options, answer) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            (paper_id, question, q_type, q_difficulty, q_blooms, q_topic, "[]", "")
                        )
                conn.commit()
                logger.info(f"Inserted {len(questions)} questions for paper_id: {paper_id}")
            except sqlite3.Error as e:
                conn.rollback()
                logger.error(f"Database error: {str(e)}")
                return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

        return jsonify({"success": True, "paper_id": paper_id})
    except Exception as e:
        logger.error(f"Unexpected error in generate endpoint: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": "Server error: Please try again later."}), 500

# API to upload and process Excel file
@app.route("/api/upload_excel", methods=["POST"])
def upload_excel():
    if "excel_file" not in request.files:
        logger.error("No file uploaded")
        return jsonify({"success": False, "message": "No file uploaded"}), 400

    file = request.files["excel_file"]
    if file.filename == "":
        logger.error("No file selected")
        return jsonify({"success": False, "message": "No file selected"}), 400

    if not file.filename.endswith((".xlsx", ".xls")):
        logger.error("Invalid file format")
        return jsonify({"success": False, "message": "Only Excel files are allowed"}), 400

    try:
        question_types = json.loads(request.form.get('question_types', '[]'))
        topic = request.form.get('topic', '')
        difficulty = request.form.get('difficulty', 'Medium')
        exam_title = request.form.get('exam_title', 'Excel Generated Paper')
        time_limit = int(request.form.get('time_limit', 60))
        instructions = request.form.get('instructions', 'Generated from Excel file')
        total_questions = int(request.form.get('total_questions', 0))

        logger.info(f"Processing Excel upload: topic={topic}, difficulty={difficulty}, total_questions={total_questions}")

        if not question_types:
            logger.error("No question types specified")
            return jsonify({"success": False, "message": "No question types specified"}), 400

        if total_questions < 1 or total_questions > 50:
            logger.error("Invalid total questions count")
            return jsonify({"success": False, "message": "Invalid total questions count"}), 400

        df = pd.read_excel(file)
        logger.info(f"Excel file loaded with {len(df)} rows")

        required_columns = ['Description', 'Type', 'Course Outcome', "Bloom's Level"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"Missing required columns: {', '.join(missing_columns)}")
            return jsonify({"success": False, "message": f"Missing required columns: {', '.join(missing_columns)}"}), 400

        filtered_df = df.copy()
        if topic:
            filtered_df = filtered_df[filtered_df['Unit'].str.contains(topic, case=False, na=False)]
        if 'Difficulty' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Difficulty'] == difficulty]

        questions_by_type = {}
        total_selected = 0
        for q_type in question_types:
            type_df = filtered_df[filtered_df['Type'] == q_type['type']]
            if not type_df.empty:
                count = min(len(type_df), q_type['count'])
                questions_by_type[q_type['type']] = type_df.sample(count)
                total_selected += count

        if total_selected == 0:
            logger.error("No questions found matching criteria")
            return jsonify({"success": False, "message": "No questions found matching your criteria."}), 400

        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO papers (exam_title, time_limit, instructions) VALUES (?, ?, ?)",
                (exam_title, time_limit, instructions)
            )
            paper_id = c.lastrowid

            questions_inserted = 0
            for q_type, type_df in questions_by_type.items():
                for _, row in type_df.iterrows():
                    if pd.isna(row['Description']) or not str(row['Description']).strip():
                        continue
                    c.execute(
                        """INSERT INTO questions 
                        (paper_id, question, type, difficulty, blooms_level, topic, options, answer) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            paper_id,
                            str(row['Description']),
                            str(row['Type']),
                            difficulty,
                            str(row["Bloom's Level"]),
                            str(row.get('Unit', 'General')),
                            "[]",
                            ""
                        )
                    )
                    questions_inserted += 1
            conn.commit()
            logger.info(f"Inserted {questions_inserted} questions for paper_id: {paper_id}")

        return jsonify({
            "success": True,
            "paper_id": paper_id,
            "message": f"Successfully selected {questions_inserted} questions from the Excel file"
        })
    except Exception as e:
        logger.error(f"Error processing Excel file: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": "Server error: Please try again later."}), 500

# API to fetch all questions
@app.route("/api/questions")
def get_questions():
    paper_id = request.args.get("paper_id")
    if not paper_id or not paper_id.isdigit():
        logger.error("Invalid paper_id")
        return jsonify({"success": False, "message": "Invalid paper_id"}), 400

    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT id, question, type, difficulty, blooms_level, topic, options, answer FROM questions WHERE paper_id = ?", (paper_id,))
            questions = [
                {
                    "id": row["id"],
                    "question": row["question"],
                    "type": row["type"],
                    "difficulty": row["difficulty"],
                    "blooms_level": row["blooms_level"],
                    "topic": row["topic"],
                    "options": json.loads(row["options"]),
                    "answer": row["answer"]
                }
                for row in c.fetchall()
            ]
        logger.info(f"Fetched {len(questions)} questions for paper_id: {paper_id}")
        return jsonify(questions)
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

# API to export questions as PDF
@app.route("/api/export", methods=["POST"])
def export_pdf():
    data = request.get_json()
    paper_id = data.get("paper_id")
    question_ids = data.get("question_ids", [])

    if not paper_id or not question_ids or not all(isinstance(qid, int) for qid in question_ids):
        logger.error("Invalid paper_id or question_ids")
        return jsonify({"success": False, "message": "Invalid paper_id or question_ids"}), 400

    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT exam_title, time_limit, instructions FROM papers WHERE id = ?", (paper_id,))
            paper = c.fetchone()
            if not paper:
                logger.error("Paper not found")
                return jsonify({"success": False, "message": "Paper not found"}), 404

            placeholders = ",".join("?" * len(question_ids))
            c.execute(
                f"SELECT question, type, difficulty, blooms_level, topic, options, answer FROM questions WHERE id IN ({placeholders}) AND paper_id = ?",
                question_ids + [paper_id]
            )
            questions = c.fetchall()

        if not questions:
            logger.error("No questions found")
            return jsonify({"success": False, "message": "No questions found"}), 400

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph(paper["exam_title"] or "Question Paper", styles['Title']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Time Limit: {paper['time_limit'] or 60} minutes", styles['Normal']))
        if paper["instructions"]:
            story.append(Paragraph("Instructions:", styles['Normal']))
            story.append(Paragraph(paper["instructions"], styles['BodyText']))
        story.append(Spacer(1, 12))

        for i, row in enumerate(questions, 1):
            try:
                story.append(Paragraph(f"Q{i}. {row['question']}", styles['BodyText']))
                opts = json.loads(row['options'])
                if row['type'] == "Multiple Choice" and opts:
                    for j, opt in enumerate(opts, 1):
                        story.append(Paragraph(f"   {chr(96+j)}. {opt}", styles['BodyText']))
                story.append(Paragraph(f"({row['type']}, {row['difficulty']}, {row['blooms_level']}, {row['topic']})", styles['Normal']))
                story.append(Spacer(1, 12))
            except json.JSONDecodeError:
                story.append(Paragraph("Error: Invalid options format", styles['Normal']))

        doc.build(story)
        buffer.seek(0)
        logger.info(f"Generated PDF for paper_id: {paper_id}")
        return send_file(
            buffer,
            as_attachment=True,
            download_name="question_paper.pdf",
            mimetype="application/pdf"
        )
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": "Server error: Please try again later."}), 500

@app.route("/")
def index():
    logger.info("Serving index.html")
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)