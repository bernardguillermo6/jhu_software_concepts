"""
Query predefined analytics from the PostgreSQL applicants table.

This module defines common analysis queries over the applicant data and
provides functions to execute them:

- `_get_questions_and_queries`: Returns the static list of (question, SQL).
- `run_queries`: Executes queries and returns results as dicts.
- `get_max_id`: Fetch the maximum applicant result ID from the DB.
- `main`: CLI entry point that prints results to stdout.
"""

#!/usr/bin/env python3
# pylint: disable=no-member

from typing import List, Dict, Tuple
from psycopg import Connection
from src.db import get_db_connection


def _get_questions_and_queries() -> List[Tuple[str, str]]:
    """
    Return a static list of questions and their associated SQL queries.
    """
    return [
        (
            "How many entries do you have in your database who applied for Fall 2025?",
            (
                "SELECT 'Applicant count: ' || COUNT(*) "
                "FROM applicants "
                "WHERE term IN ('Fall 2025','F25')"
            ),
        ),
        (
            "What percentage of entries are from international students (not American or Other)?",
            (
                "SELECT 'Percent International: ' || ROUND(("
                "SUM(CASE WHEN us_or_international = 'International' "
                "THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100), 2) || '%' "
                "FROM applicants"
            ),
        ),
        (
            "What is the average GPA, GRE, GRE V, GRE AW of applicants who provide these metrics?",
            (
                "SELECT 'Average GPA: ' || ROUND(AVG(NULLIF(gpa,0))::numeric,2) "
                "|| ', Average GRE: ' || ROUND(AVG(NULLIF(gre,0))::numeric,2) "
                "|| ', Average GRE V: ' || ROUND(AVG(NULLIF(gre_v,0))::numeric,2) "
                "|| ', Average GRE AW: ' || ROUND(AVG(NULLIF(gre_aw,0))::numeric,2) "
                "FROM applicants"
            ),
        ),
        (
            "What is their average GPA of American students in Fall 2025?",
            (
                "SELECT 'Average GPA American: ' || "
                "ROUND(AVG(NULLIF(gpa,0))::numeric,2) "
                "FROM applicants "
                "WHERE term IN ('Fall 2025','F25') "
                "AND us_or_international = 'American'"
            ),
        ),
        (
            "What percent of entries for Fall 2025 are Acceptances?",
            (
                "SELECT 'Acceptance percent: ' || ROUND("
                "SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END)::numeric "
                "/ COUNT(*) * 100, 2) || '%' "
                "FROM applicants "
                "WHERE term IN ('Fall 2025','F25')"
            ),
        ),
        (
            "What is the average GPA of applicants in Fall 2025 who are Acceptances?",
            (
                "SELECT 'Average GPA Acceptance: ' || "
                "ROUND(AVG(NULLIF(gpa,0))::numeric,2) "
                "FROM applicants "
                "WHERE term IN ('Fall 2025','F25') "
                "AND status = 'Accepted'"
            ),
        ),
        (
            "How many JHU masters in Computer Science applications are there?",
            (
                "SELECT 'JHU Computer Science Masters Applications: ' || COUNT(*) "
                "FROM applicants "
                "WHERE llm_generated_university = 'Johns Hopkins University' "
                "AND llm_generated_program = 'Computer Science' "
                "AND degree = 'Masters'"
            ),
        ),
        (
            "How many 2025 Georgetown PhD CS acceptances?",
            (
                "SELECT 'Georgetown CS PhD Acceptances: ' || COUNT(*) "
                "FROM applicants "
                "WHERE llm_generated_university = 'Georgetown University' "
                "AND llm_generated_program = 'Computer Science' "
                "AND term LIKE '%2025%' "
                "AND status = 'Accepted' "
                "AND degree = 'PhD'"
            ),
        ),
        (
            "What universities (≥10 apps) for CS Masters have lowest/highest acceptance rates?",
            (
                "SELECT 'Lowest acceptance rate: ' || ("
                "SELECT university || ' - ' "
                "|| ROUND(acceptance_rate * 100, 2)::text || '%' "
                "FROM (SELECT llm_generated_university AS university, "
                "SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END)::numeric "
                "/ COUNT(*) AS acceptance_rate, COUNT(*) AS total_apps "
                "FROM applicants "
                "WHERE degree = 'Masters' "
                "AND llm_generated_program = 'Computer Science' "
                "GROUP BY 1 HAVING COUNT(*) >= 10) a "
                "ORDER BY acceptance_rate ASC LIMIT 1) "
                "|| ' | Highest acceptance rate: ' || ("
                "SELECT university || ' - ' "
                "|| ROUND(acceptance_rate * 100, 2)::text || '%' "
                "FROM (SELECT llm_generated_university AS university, "
                "SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END)::numeric "
                "/ COUNT(*) AS acceptance_rate, COUNT(*) AS total_apps "
                "FROM applicants "
                "WHERE degree = 'Masters' "
                "AND llm_generated_program = 'Computer Science' "
                "GROUP BY 1 HAVING COUNT(*) >= 10) b "
                "ORDER BY acceptance_rate DESC LIMIT 1)"
            ),
        ),
        (
            "Most popular PhD programs in 2024 and 2025?",
            (
                "SELECT 'Most popular PhD program in 2024: ' || ("
                "SELECT llm_generated_program || ' at ' "
                "|| llm_generated_university || ' - ' || COUNT(*) "
                "FROM applicants "
                "WHERE degree = 'PhD' AND term LIKE '%2024%' "
                "GROUP BY llm_generated_program, llm_generated_university "
                "ORDER BY COUNT(*) DESC LIMIT 1) "
                "|| ' | Most popular PhD program in 2025: ' || ("
                "SELECT llm_generated_program || ' at ' "
                "|| llm_generated_university || ' - ' || COUNT(*) "
                "FROM applicants "
                "WHERE degree = 'PhD' AND term LIKE '%2025%' "
                "GROUP BY llm_generated_program, llm_generated_university "
                "ORDER BY COUNT(*) DESC LIMIT 1)"
            ),
        ),
    ]


def run_queries() -> List[Dict[str, str]]:
    """Run predefined SQL queries and return their results."""
    data: List[Dict[str, str]] = []
    conn: Connection = get_db_connection()  # type: ignore
    try:
        with conn.cursor() as cur:
            for question, query in _get_questions_and_queries():
                cur.execute(query)
                answer = cur.fetchone()[0]
                data.append({"question": question, "answer": answer})
    finally:
        conn.close()
    return data


def get_max_id() -> int:
    """Get the maximum applicant result ID from the database."""
    conn: Connection = get_db_connection()  # type: ignore
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT MAX(
                    CAST(split_part(url, '/result/', 2) AS INTEGER)
                ) AS max_id
                FROM applicants
                """
            )
            result = cur.fetchone()[0]
            return result if result else 0
    finally:
        conn.close()


def main() -> None:
    """Run queries and print them to stdout."""
    for item in run_queries():
        print(f"Q: {item['question']}")
        print(f"A: {item['answer']}")
        print("-" * 80)


if __name__ == "__main__":
    main()
