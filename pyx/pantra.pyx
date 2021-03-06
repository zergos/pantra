import os
import sys

# detect env
venv = os.environ.get('VIRTUAL_ENV', '')
if not venv:
    print('activate your virtual environment first')
    sys.exit(0)

# setup env project root
sys.path.append(os.path.dirname(venv))

# setup env site-packages
if sys.platform == "win32":
    venv = os.path.join(venv, 'Scripts')
else:
    venv = os.path.join(venv, 'bin')
activator = os.path.join(venv, 'activate_this.py')
exec(open(activator).read(), {'__file__': activator})

# reset module name from this file to package
del sys.modules['pantra']

# run management command
from pantra.management import execute_from_command_line
execute_from_command_line(None)
