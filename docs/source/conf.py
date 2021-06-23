# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('../../python/src'))


# -- Project information -----------------------------------------------------

project = 'Model Balancing'
copyright = '2021, Elad Noor, Wolfram Liebermeister'
author = 'Elad Noor, Wolfram Liebermeister'

# The full version, including alpha/beta/rc tags
release = '0.1'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx_rtd_theme",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autodoc",
    "sphinx.ext.inheritance_diagram",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinxcontrib.bibtex",
    "autoapi.extension",
    "nbsphinx",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", ".ipynb_checkpoints"]

# Napoleon settings
napoleon_numpy_docstring = True

# The master toctree document.
master_doc = "index"

# Bibtex options.
suppress_warnings = ["autosectionlabel.*"]
bibtex_bibfiles = ["bibliography.bib"]

# -- Sphinx AutoAPI ----------------------------------------------------------
autoapi_type = "python"
autoapi_add_toctree_entry = False
autoapi_dirs = ["../../python/src/model_balancing"]
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
]

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {
    "http://docs.python.org/": None,
    "http://docs.scipy.org/doc/numpy/": None,
    "http://docs.scipy.org/doc/scipy/reference": None,
}
intersphinx_cache_limit = 10  # days to keep the cached inventories


def skip_member_handler(app, what, name, obj, skip, options):
    return skip or name.endswith(".logger")


def setup(app):
    app.connect("autoapi-skip-member", skip_member_handler)


# For debugging purposes only.
# autoapi_keep_files = True

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
