from flask import Blueprint, render_template
import psycopg

# Initializing the blueprint for the page routes
bp = Blueprint("pages", __name__)

def get_db_connection():
    return psycopg.connect(dbname="thegradcafe", user="postgres", host="localhost", port=5432)

# Route for the About tab
@bp.route("/")
def index():
    conn = get_db_connection()
    cur = conn.cursor()

    questions_and_queries = [
        ("How many entries do you have in your database who applied for Fall 2024?",
         "SELECT 'Applicant count: ' || COUNT(*) FROM applicants WHERE term in ('Fall 2024','F24')"),

        ("What percentage of entries are from international students (not American or Other) (to two decimal places)?",
         "SELECT 'Percent International: ' || ROUND((SUM(CASE WHEN us_or_international = 'International' THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100), 2) || '%' AS percent_international FROM applicants;"),

        ("What is the average GPA, GRE, GRE V, GRE AW of applicants who provide these metrics?",
         "SELECT 'Average GPA: ' || ROUND(AVG(NULLIF(gpa,0))::numeric,2) || ', Average GRE: ' || ROUND(AVG(NULLIF(gre,0))::numeric,2) || ', Average GRE V: ' || ROUND(AVG(NULLIF(gre_v,0))::numeric,2) || ', Average GRE AW: ' || ROUND(AVG(NULLIF(gre_aw,0))::numeric,2) FROM applicants;"),

        ("What is their average GPA of American students in Fall 2025?",
         "SELECT 'Average GPA American: ' || ROUND(AVG(NULLIF(gpa,0))::numeric,2)  FROM applicants WHERE term = 'Fall 2025' AND us_or_international = 'American' "),

        ("What percent of entries for Fall 2025 are Acceptances (to two decimal places)?",
         "SELECT 'Acceptance percent: ' || ROUND(SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100,2) || '%' FROM applicants WHERE term = 'Fall 2025'"),

        ("What is the average GPA of applicants who applied for Fall 2025 who are Acceptances?",
         "SELECT 'Average GPA Acceptance: ' || ROUND(AVG(NULLIF(gpa,0))::numeric,2) FROM applicants WHERE term = 'Fall 2025' AND status = 'Accepted'"),

        ("How many entries are from applicants who applied to JHU for a masters degrees in Computer Science?",
         "SELECT 'JHU Computer Science Masters Applications: ' || COUNT(*) FROM applicants WHERE llm_generated_university = 'Johns Hopkins University' AND llm_generated_program = 'Computer Science' AND degree = 'Masters' "),

        ("How many entries from 2025 are acceptances from applicants who applied to Georgetown University for a PhD in Computer Science?",
         "SELECT 'Georgetown University Computer Science PhD Acceptances: ' || COUNT(*) FROM applicants WHERE llm_generated_university = 'Georgetown University' AND llm_generated_program = 'Computer Science' AND term LIKE '%2025%' AND status = 'Accepted' AND degree = 'PhD' ")    
    ]

    data = []
    for question, query in questions_and_queries:
        cur.execute(query)
        answer = cur.fetchone()[0]
        data.append({"question": question, "answer": answer})

    cur.close()
    conn.close()
    return render_template("pages/index.html", data=data)