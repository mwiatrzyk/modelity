# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

this_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.join(this_dir, "..", "..")
sys.path.insert(0, root_dir)

import doctest
import modelity

project = "Modelity"
copyright = "2024, Maciej Wiatrzyk"
author = "Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>"
release = modelity.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
]


templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]


# -- Extension configuration

# sphinx.ext.intersphinx
intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}

# sphinx.ext.doctest
doctest_default_flags = doctest.ELLIPSIS | doctest.DONT_ACCEPT_TRUE_FOR_1
