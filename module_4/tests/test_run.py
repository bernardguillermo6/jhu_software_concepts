import runpy
import pytest
from unittest.mock import patch


@pytest.mark.run
def test_main_block_executes():
    """
    Ensure that when run.py is executed as a script, app.run() is called
    with expected arguments.
    """
    # Patch Flask.run so it doesn't actually start a server
    with patch("flask.Flask.run") as mock_run:
        runpy.run_path("src/run.py", run_name="__main__")

        mock_run.assert_called_once_with(debug=True, host="0.0.0.0", port=8080)