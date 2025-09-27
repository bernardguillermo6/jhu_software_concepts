"""
Query predefined analytics from the PostgreSQL applicants table.

All queries are written using psycopg.sql composition to prevent injection.
Each includes an explicit LIMIT to avoid unbounded results.

Functions
---------
- _get_questions_and_queries: returns list of (question, composed SQL)
- run_queries: executes queries and returns results as dicts
- get_max_id: fetch the maximum applicant result ID from the DB
- main: CLI entry point that prints results to stdout
"""

#!/usr/bin/env python3
# pylint: disable=no-member

from typing import List, Dict, Tuple
from psycopg import Connection, sql
from src.db import get_db_connection


def _get_questions_and_queries() -> List[Tuple[str, sql.Composed]]:
    """Return a static list of questions and their associated composed SQL."""
    tbl = sql.Identifier("applicants")
    limit_one = sql.SQL(" LIMIT 1")

    queries: List[Tuple[str, sql.Composed]] = [
        (
            "How many entries do you have in your database who applied for Fall 2025?",
            sql.SQL(
                "SELECT 'Applicant count: ' || COUNT(*) "
                "FROM {tbl} WHERE term IN ({t1}, {t2})"
            ).format(tbl=tbl, t1=sql.Literal("Fall 2025"), t2=sql.Literal("F25"))
            + limit_one,
        ),
        (
            "What percentage of entries are from international students?",
            sql.SQL(
                "SELECT 'Percent International: ' || ROUND(("
                "SUM(CASE WHEN us_or_international = {intl} THEN 1 ELSE 0 END)::numeric "
                "/ COUNT(*) * 100), 2) || '%' FROM {tbl}"
            ).format(tbl=tbl, intl=sql.Literal("International"))
            + limit_one,
        ),
        (
            "What is the average GPA, GRE, GRE V, GRE AW of applicants?",
            sql.SQL(
                "SELECT 'Average GPA: ' || ROUND(AVG(NULLIF(gpa,0))::numeric,2) "
                "|| ', Average GRE: ' || ROUND(AVG(NULLIF(gre,0))::numeric,2) "
                "|| ', Average GRE V: ' || ROUND(AVG(NULLIF(gre_v,0))::numeric,2) "
                "|| ', Average GRE AW: ' || ROUND(AVG(NULLIF(gre_aw,0))::numeric,2) "
                "FROM {tbl}"
            ).format(tbl=tbl)
            + limit_one,
        ),
        (
            "What is their average GPA of American students in Fall 2025?",
            sql.SQL(
                "SELECT 'Average GPA American: ' || ROUND(AVG(NULLIF(gpa,0))::numeric,2) "
                "FROM {tbl} WHERE term IN ({t1}, {t2}) AND us_or_international = {amer}"
            ).format(
                tbl=tbl,
                t1=sql.Literal("Fall 2025"),
                t2=sql.Literal("F25"),
                amer=sql.Literal("American"),
            )
            + limit_one,
        ),
        (
            "What percent of entries for Fall 2025 are Acceptances?",
            sql.SQL(
                "SELECT 'Acceptance percent: ' || ROUND("
                "SUM(CASE WHEN status = {accepted} THEN 1 ELSE 0 END)::numeric "
                "/ COUNT(*) * 100, 2) || '%' FROM {tbl} "
                "WHERE term IN ({t1}, {t2})"
            ).format(
                tbl=tbl,
                accepted=sql.Literal("Accepted"),
                t1=sql.Literal("Fall 2025"),
                t2=sql.Literal("F25"),
            )
            + limit_one,
        ),
        (
            "What is the average GPA of applicants in Fall 2025 who are Acceptances?",
            sql.SQL(
                "SELECT 'Average GPA Acceptance: ' || ROUND(AVG(NULLIF(gpa,0))::numeric,2) "
                "FROM {tbl} WHERE term IN ({t1}, {t2}) AND status = {accepted}"
            ).format(
                tbl=tbl,
                t1=sql.Literal("Fall 2025"),
                t2=sql.Literal("F25"),
                accepted=sql.Literal("Accepted"),
            )
            + limit_one,
        ),
        (
            "How many JHU masters in Computer Science applications are there?",
            sql.SQL(
                "SELECT 'JHU Computer Science Masters Applications: ' || COUNT(*) "
                "FROM {tbl} WHERE llm_generated_university = {uni} "
                "AND llm_generated_program = {prog} AND degree = {deg}"
            ).format(
                tbl=tbl,
                uni=sql.Literal("Johns Hopkins University"),
                prog=sql.Literal("Computer Science"),
                deg=sql.Literal("Masters"),
            )
            + limit_one,
        ),
        (
            "How many 2025 Georgetown PhD CS acceptances?",
            sql.SQL(
                "SELECT 'Georgetown CS PhD Acceptances: ' || COUNT(*) "
                "FROM {tbl} WHERE llm_generated_university = {uni} "
                "AND llm_generated_program = {prog} "
                "AND term LIKE {t2025} AND status = {accepted} AND degree = {phd}"
            ).format(
                tbl=tbl,
                uni=sql.Literal("Georgetown University"),
                prog=sql.Literal("Computer Science"),
                t2025=sql.Literal("%2025%"),
                accepted=sql.Literal("Accepted"),
                phd=sql.Literal("PhD"),
            )
            + limit_one,
        ),
    ]

    return queries


def run_queries() -> List[Dict[str, str]]:
    """Run predefined SQL queries and return their results."""
    data: List[Dict[str, str]] = []
    conn: Connection = get_db_connection()  # type: ignore
    try:
        with conn.cursor() as cur:
            for question, query in _get_questions_and_queries():
                cur.execute(query)
                row = cur.fetchone()
                answer = row[0] if row else ""
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
                sql.SQL(
                    "SELECT MAX(CAST(split_part(url, '/result/', 2) AS INTEGER)) "
                    "FROM {tbl} LIMIT 1"
                ).format(tbl=sql.Identifier("applicants"))
            )
            result = cur.fetchone()
            return int(result[0]) if result and result[0] is not None else 0
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
