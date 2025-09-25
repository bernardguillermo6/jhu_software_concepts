"""
Integration test for running the Flask app entrypoint (src/run.py).
"""

import runpy
from unittest.mock import patch

import pytest


@pytest.mark.integration
def test_main_block_executes():
    """
    Ensure that when run.py is executed as a script, app.run() is called
    with expected arguments.
    """
    # Patch load_data_to_db at its source module, not in src.run
    with patch("src.load_data.load_data_to_db", return_value=None), patch(
        "flask.Flask.run"
    ) as mock_run:
        runpy.run_path("src/run.py", run_name="__main__")

        mock_run.assert_called_once_with(debug=True, host="0.0.0.0", port=8080)
