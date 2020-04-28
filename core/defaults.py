import os

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPONENTS_PATH = os.path.join(BASE_PATH, 'components')
PAGES_PATH = os.path.join(BASE_PATH, 'pages')
CSS_PATH = os.path.join(BASE_PATH, 'css')

'''
DB_PARAMS = dict(
    provider='sqlite',
    filename=os.path.join(BASE_PATH, 'local.sqlite'),
    create_db=True
)
'''
DB_PARAMS = dict(
    provider='postgres',
    database='bwf',
    user='bwf',
    password='bwf',
    host='',
)
MIGRATION_PATH = os.path.join(BASE_PATH, 'migrations')

TASK_THREADS = 2
