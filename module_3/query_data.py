from db import get_db_connection

def get_questions_and_queries():
    return [
        ("How many entries do you have in your database who applied for Fall 2025?",
         "SELECT 'Applicant count: ' || COUNT(*) FROM applicants WHERE term in ('Fall 2025','F25')"),
        ("What percentage of entries are from international students (not American or Other) (to two decimal places)?",
         "SELECT 'Percent International: ' || ROUND((SUM(CASE WHEN us_or_international = 'International' THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100), 2) || '%' AS percent_international FROM applicants;"),
        ("What is the average GPA, GRE, GRE V, GRE AW of applicants who provide these metrics?",
         "SELECT 'Average GPA: ' || ROUND(AVG(NULLIF(gpa,0))::numeric,2) || ', Average GRE: ' || ROUND(AVG(NULLIF(gre,0))::numeric,2) || ', Average GRE V: ' || ROUND(AVG(NULLIF(gre_v,0))::numeric,2) || ', Average GRE AW: ' || ROUND(AVG(NULLIF(gre_aw,0))::numeric,2) FROM applicants;"),
        ("What is their average GPA of American students in Fall 2025?",
         "SELECT 'Average GPA American: ' || ROUND(AVG(NULLIF(gpa,0))::numeric,2) FROM applicants WHERE term IN ('Fall 2025','F25') AND us_or_international = 'American'"),
        ("What percent of entries for Fall 2025 are Acceptances (to two decimal places)?",
         "SELECT 'Acceptance percent: ' || ROUND(SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100,2) || '%' FROM applicants WHERE term IN ('Fall 2025','F25')"),
        ("What is the average GPA of applicants who applied for Fall 2025 who are Acceptances?",
         "SELECT 'Average GPA Acceptance: ' || ROUND(AVG(NULLIF(gpa,0))::numeric,2) FROM applicants WHERE term in ('Fall 2025','F25') AND status = 'Accepted'"),
        ("How many entries are from applicants who applied to JHU for a masters degrees in Computer Science?",
         "SELECT 'JHU Computer Science Masters Applications: ' || COUNT(*) FROM applicants WHERE llm_generated_university = 'Johns Hopkins University' AND llm_generated_program = 'Computer Science' AND degree = 'Masters'"),
        ("How many entries from 2025 are acceptances from applicants who applied to Georgetown University for a PhD in Computer Science?",
         "SELECT 'Georgetown University Computer Science PhD Acceptances: ' || COUNT(*) FROM applicants WHERE llm_generated_university = 'Georgetown University' AND llm_generated_program = 'Computer Science' AND term LIKE '%2025%' AND status = 'Accepted' AND degree = 'PhD'"),
        ("What universities with at least 10 applications for master's programs in computer science have the lowest and highest acceptance rates?",
         "SELECT 'Lowest acceptance rate: ' || (SELECT university || ' - ' || ROUND(acceptance_rate * 100, 2)::text || '%' FROM (SELECT llm_generated_university AS university, SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END)::numeric / COUNT(*) AS acceptance_rate, COUNT(*) AS total_apps FROM applicants WHERE degree = 'Masters' AND llm_generated_program = 'Computer Science' GROUP BY 1 HAVING COUNT(*) >= 10) a ORDER BY acceptance_rate ASC LIMIT 1) || ' | Highest acceptance rate: ' || (SELECT university || ' - ' || ROUND(acceptance_rate * 100, 2)::text || '%' FROM (SELECT llm_generated_university AS university, SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END)::numeric / COUNT(*) AS acceptance_rate, COUNT(*) AS total_apps FROM applicants WHERE degree = 'Masters' AND llm_generated_program = 'Computer Science' GROUP BY 1 HAVING COUNT(*) >= 10) b ORDER BY acceptance_rate DESC LIMIT 1)"),
        ("What are the most popular PhD programs in 2024 and 2025 by applications?",
         "SELECT 'Most popular PhD program in 2024: ' || (SELECT llm_generated_program || ' at ' || llm_generated_university || ' - ' || COUNT(*) FROM applicants WHERE degree = 'PhD' AND term LIKE '%2024%' GROUP BY llm_generated_program, llm_generated_university ORDER BY COUNT(*) DESC LIMIT 1) || ' | Most popular PhD program in 2025: ' || (SELECT llm_generated_program || ' at ' || llm_generated_university || ' - ' || COUNT(*) FROM applicants WHERE degree = 'PhD' AND term LIKE '%2025%' GROUP BY llm_generated_program, llm_generated_university ORDER BY COUNT(*) DESC LIMIT 1)")
    ]


def run_queries():
    """Fetch all Q&A pairs by running queries against the DB."""
    conn = get_db_connection()
    cur = conn.cursor()

    data = []
    for question, query in get_questions_and_queries():
        cur.execute(query)
        answer = cur.fetchone()[0]
        data.append({"question": question, "answer": answer})

    cur.close()
    conn.close()
    return data


def get_max_id():
    """Fetch the current maximum ID from the applicants table."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT MAX(CAST(split_part(url, '/result/', 2) AS INTEGER)) AS max_id
        FROM applicants
    """)
    result = cur.fetchone()[0]
    cur.close()
    conn.close()
    return result if result else 0

if __name__ == "__main__":
    for item in run_queries():
        print(f"Q: {item['question']}")
        print(f"A: {item['answer']}")
        print("-" * 80)