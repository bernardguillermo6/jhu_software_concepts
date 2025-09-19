========================================
Grad Cafe Application - Project Overview
========================================

Overview & Setup
================
The **Grad Cafe Application** scrapes admissions survey results, cleans the data,
loads it into a PostgreSQL database, and serves queries via a Flask web interface.

**Requirements:**
- Python 3.12+
- PostgreSQL running locally on port 5432
- `psycopg`, `flask`, `bs4`, `urllib3`, `pytest`, `sphinx`

**Environment Variables:**
- ``DATABASE_URL`` or equivalent connection string  
(default: ``dbname=thegradcafe user=postgres host=localhost port=5432``)

**Run the application:**
.. code-block:: bash

   python -m src.run

**Run the tests:**
.. code-block:: bash

   pytest -m "db or web or analysis or integration"

Architecture
============
The application is divided into three main layers:

**Web Layer (Flask):**
- Located in ``src/app/``
- Serves routes for analysis, scraping, refreshing queries, and scraper status.
- Implements a blueprint (`pages.py`) for routing and HTML rendering.

**ETL Layer (Scrape & Clean):**
- ``src/scrape.py``: Scrapes survey entries and detail pages.
- ``src/clean.py``: Cleans raw HTML into normalized records and optionally
runs an LLM-based cleaning pipeline.

**DB Layer (Load & Query):**
- ``src/load_data.py``: Loads JSONL data into PostgreSQL.
- ``src/query_data.py``: Defines and executes SQL queries for analytics.
- ``src/db.py``: Provides database connection helpers.

API Reference
=============
Autodoc pages for core modules:

.. toctree::
   :maxdepth: 1

   api/modules

Testing Guide
=============
We use ``pytest`` with **markers** to organize tests:

- ``@pytest.mark.web`` — page load / HTML structure tests.
- ``@pytest.mark.buttons`` — button endpoints & busy-state behavior.
- ``@pytest.mark.analysis`` — data cleaning and formatting logic.
- ``@pytest.mark.db`` — database schema, inserts, and query execution.
- ``@pytest.mark.integration`` — end-to-end flows across layers.

**Examples:**

Run only database tests:
.. code-block:: bash

   pytest -m db

Run end-to-end tests:
.. code-block:: bash

   pytest -m integration

Run everything with coverage:
.. code-block:: bash

   pytest --cov=src --cov-report=term-missing

``tests/`` also provides test doubles (e.g., fake DB connections) and fixtures
to isolate units while still covering all key branches.
