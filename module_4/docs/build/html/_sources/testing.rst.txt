================
Testing Guide
================

We use ``pytest`` with markers to organize tests.  

Markers
-------
- ``@pytest.mark.web`` — page load / HTML structure.
- ``@pytest.mark.buttons`` — button endpoints & busy-state behavior.
- ``@pytest.mark.analysis`` — data cleaning and formatting logic.
- ``@pytest.mark.db`` — database schema, inserts, and query execution.
- ``@pytest.mark.integration`` — end-to-end flows across layers.

Examples
--------
Run only **database** tests:
.. code-block:: bash

   pytest -m db

Run only **web** tests:
.. code-block:: bash

   pytest -m web

Run end-to-end **integration** tests:
.. code-block:: bash

   pytest -m integration

Run all tests with coverage:
.. code-block:: bash

   pytest --cov=src --cov-report=term-missing

Fixtures and Test Doubles
-------------------------
- Fake database connections (see ``test_load_data.py`` and ``test_query_data.py``).
- Monkeypatched HTTP requests (see ``test_scrape.py``).
- Temporary JSONL files for isolated ETL testing.

These ensure unit tests remain deterministic while integration tests cover full workflows.
