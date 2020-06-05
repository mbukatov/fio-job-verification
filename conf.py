# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------

project = 'Data verification of previously written fio data'
copyright = '2020, Martin Bukatovič'
author = 'Martin Bukatovič'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'README.rst']


# -- Hieroglyph Slide Configuration ------------

extensions += [
    'hieroglyph',
]

slide_title = 'Data verification of previously written fio data'
slide_theme = 'single-level'
slide_levels = 3

slide_footer = "OCSQE knowledge sharing session"

# Place custom static assets in the _static directory and uncomment
# the following lines to include them

# slide_theme_options = {
#     'custom_css': 'custom.css',
#     'custom_js': 'custom.js',
# }

# ----------------------------------------------


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'alabaster'
html_sidebars = {'**': ['localtoc.html', 'sourcelink.html', 'searchbox.html']}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
