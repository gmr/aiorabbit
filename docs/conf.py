import datetime

import pkg_resources

master_doc = 'index'
project = 'aiorabbit'
release = version = pkg_resources.get_distribution(project).version
copyright = '{}, Gavin M. Roy'.format(datetime.date.today().year)

extensions = [
    'sphinx.ext.autodoc',
    'sphinx_autodoc_typehints',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode'
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
intersphinx_mapping = {'python': ('https://docs.python.org/3', None),
                       'pamqp': ('https://pamqp.readthedocs.io/en/latest/', None)}

autodoc_default_options = {'autodoc_typehints': 'description'}
