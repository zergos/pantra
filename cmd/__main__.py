try:
    import pantra

except ModuleNotFoundError:
    import os
    import sys

    # detect env
    venv = os.environ.get('VIRTUAL_ENV', '')
    if not venv:
        print('activate your virtual environment first')
        sys.exit(0)

    # setup env project root
    sys.path.append(os.path.dirname(venv))

# run management command
from pantra.management import execute_from_command_line
execute_from_command_line(None)
