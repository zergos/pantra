import os

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPONENTS_PATH = os.path.join(BASE_PATH, 'components')
PAGES_PATH = os.path.join(BASE_PATH, 'pages')
CSS_PATH = os.path.join(BASE_PATH, 'css')

'''
db_params = dict(
    provider='sqlite',
    filename=os.path.join(BASE_PATH, 'local.sqlite'),
    create_db=True
)
'''
db_params = dict(
    provider='postgres',
    database='bwf',
    user='bwf',
    password='bwf',
    host='',
)
migration_dir = os.path.join(BASE_PATH, 'migrations')
