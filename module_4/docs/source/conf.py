# Configuration file for the Sphinx documentation builder.

import os
import sys
sys.path.insert(0, os.path.abspath("../.."))  # parent of src

project = "Grad Cafe Application"
copyright = "2025, Bernard Guillermo"
author = "Bernard Guillermo"
release = "0.1"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.coverage",
]

templates_path = ["_templates"]
exclude_patterns = []

html_theme = "alabaster"
html_static_path = ["_static"]

# Autodoc configuration
autodoc_member_order = "bysource"
autodoc_typehints = "description"

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
