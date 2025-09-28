"""
Sphinx configuration file for building the Grad Cafe Application docs.
"""

import os
import sys

sys.path.insert(0, os.path.abspath("../.."))  # parent of src

# Project information
project = "Grad Cafe Application"  # pylint: disable=invalid-name
copyright = "2025, Bernard Guillermo"  # pylint: disable=redefined-builtin,invalid-name
author = "Bernard Guillermo"  # pylint: disable=invalid-name
release = "0.1"  # pylint: disable=invalid-name

# General configuration
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.coverage",
]

templates_path = ["_templates"]
exclude_patterns = []

# HTML theme
html_theme = "alabaster"  # pylint: disable=invalid-name
html_static_path = ["_static"]

# Autodoc configuration
autodoc_member_order = "bysource"  # pylint: disable=invalid-name
autodoc_typehints = "description"  # pylint: disable=invalid-name

# Mock imports so autodoc doesn’t try to actually load heavy deps
autodoc_mock_imports = [
    "flask",
    "psycopg",
    "bs4",
    "urllib3",
]

suppress_warnings = [
    "autodoc.import_object",
    "autodoc.duplicate_object",
]
