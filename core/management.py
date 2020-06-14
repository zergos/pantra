import os

from core.args import *
from core.models import *
from core.defaults import *


class Main:
    """Manage fruits"""

    def run(self, host: str = '127.0.0.1', port: int = 8005):
        """
        run core application on host and port
        :param host: local IP address to bind
        :param port: number of local port
        """
        from core.main import run as run_main

        run_main(host, port)

    def apps(self):
        """
        list all apps
        """
        for f in os.listdir(APPS_PATH):
            print(f)


class Migrate:
    """
    Work with database migrations via Django
    :param app: app name (auto-detection by current directory)
    :param noinput: tells Django to NOT prompt the user for input of any kind
    """
    app: str = lambda: Migrate._detect_app()
    noinput: bool = False

    @staticmethod
    def _detect_app():
        path = os.getcwd()
        if path.startswith(APPS_PATH):
            path = os.path.relpath(path, APPS_PATH)
            while os.path.dirname(path):
                path = os.path.dirname(path)
            return path
        return Empty

    def _call_django(self, *args):
        data_settings = expose_to_django(self.app)

        import django
        from django.conf import settings
        from django.core.management import execute_from_command_line

        args = list(*args)
        args.insert(0, 'manage.py')
        # os.environ.setdefault("DJANGO_SETTINGS_MODULE", '.'.join(['apps', self.app, 'data')
        settings.configure(**data_settings)
        django.setup()
        execute_from_command_line(args)

    @context_args('app')
    def init(self):
        """
        initialize migrations on database
        """
        self._call_django('migrate')

    @context_args('app')
    def list(self):
        """
        list all migrations, ones marked with + are applied.
        """
        self._call_django('showmigrations', 'data', '-v', '3')

    @context_args('app', 'noinput')
    def make(self, dry: bool = False, merge: bool = False, empty: bool = False, name: str = None):
        """
        make new migration related to app model changes
        :param dry: show what migrations would be made; don't actually write them
        :param merge: enable fixing of migration conflicts
        :param empty: create empty migration
        :param name: use this name for migration file
        """
        args = ['makemigrations', 'data', '-v', '3']
        if dry: args.append('--dry-run')
        if merge: args.append('--merge')
        if empty: args.append('--empty')
        if self.noinput: args.append('--noinput')
        if name: args.extend(['-n', name])
        self._call_django(*args)

    @context_args('app', 'noinput')
    def apply(self, name: str = None, fake: bool = False, fake_init: bool = False, plan: bool = False):
        """
        apply migrations to database
        :param name: migration name
        :param fake: mark migrations as run without actually running them
        :param fake_init: detect if tables already exist and fake-apply initial migrations if so
        :param plan: shows a list of the migration actions that will be performed
        """
        args = ['migrate', 'data']
        if name:
            args.append(name)
        args.extend(['-v', '3'])
        if self.noinput: args.append('--noinput')
        if fake: args.append('--fake')
        if fake_init: args.append('--fake-initial')
        if plan: args.append('--plan')
        self._call_django(*args)

    @context_args('app')
    def sql(self, migration: str, back: bool = False):
        """
        prints the SQL statements for the named migration
        :param migration: migration name
        :param back: creates SQL to unapply the migration, rather than to apply it
        """
        args = ['sqlmigrate', 'data', migration]
        if back: args.append('--backwards')
        self._call_django(*args)

    @context_args('app', 'noinput')
    def squash(self, start_migration: str, end_migration: str, no_optimize: bool = False, name: str = None):
        """
        squashes an existing set of migrations into a single new one (including start and end)
        :param start_migration: start migration name
        :param end_migration: end migration name
        :param no_optimize: do not add a header comment to the new squashed
        :param name: name of the new squashed migration
        """
        args = ['squashmigrations', 'data', start_migration, end_migration, '-v', '3']
        if no_optimize: args.append('--no-optimize')
        if self.noinput: args.append('--noinput')
        if name: args.extend(['--squashed-name', name])
        self._call_django(args)


def execute_from_command_line(argv):
    main = ExposeToArgs(Main())
    main.add_commands(Migrate())
    main.execute(argv)
