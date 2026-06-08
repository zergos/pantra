# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import sys
from pathlib import Path
import collections

sys.path.insert(0, str(Path(__file__).parent / '_ext'))

def remove_namedtuple_attrib_docstring(app, what, name, obj, skip, options):
    if type(obj) is collections._tuplegetter:
        return True
    if obj is object:
        return True
    return skip


def setup(app):
    from pantra_lexer import PantraLexer  # noqa
    app.connect('autodoc-skip-member', remove_namedtuple_attrib_docstring)
    app.add_lexer('pantra', PantraLexer)

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'pantra'
copyright = '2026, Andrey Aseev'
author = 'Andrey Aseev'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ['_templates']
exclude_patterns = []

extensions = [
    'sphinx.ext.intersphinx',
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.graphviz',
    'code_include.extension',
    'sphinx_toolbox.collapse',
]
sys.path.insert(0, str(Path('..', '..').resolve()))

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'quazy': ('https://quazydb.readthedocs.io/en/stable', None),
}
autodoc_member_order = 'bysource'
autodoc_typehints = 'both'
graphviz_output_format = 'svg'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'bizstyle'
#html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
