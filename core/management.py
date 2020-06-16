from __future__ import annotations

import os
import typing

from core.args import *
from core.defaults import *

if typing.TYPE_CHECKING:
    from typing import *
    from pony.orm import Database

def _detect_app():
    path = os.getcwd()
    if path.startswith(APPS_PATH):
        path = os.path.relpath(path, APPS_PATH)
        while os.path.dirname(path):
            path = os.path.dirname(path)
        return path
    return Empty


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

    def pony(self, app: str = None):
        '''
        generate pony code for type checker
        :param app: app name
        '''

        app = app or _detect_app()

        from core.models import expose_to_pony
        expose_to_pony(app)

    def django(self, app: str = None):
        '''
        generate django code for debugging
        :param app: app name
        '''

        app = app or _detect_app()
        from core.models import expose_to_django
        expose_to_django(app)


class Migrate:
    """
    Work with database migrations via Django
    :param app: app name (auto-detection by current directory)
    :param noinput: tells Django to NOT prompt the user for input of any kind
    :param debug: leave files 'model.py' and 'app.py' in app data path after call
    """
    app: str = lambda: _detect_app()
    noinput: bool = False
    debug: bool = False

    def _call_django(self, *args):
        from core.models import expose_to_django

        data_settings = expose_to_django(self.app)

        import django
        from django.conf import settings
        from django.core.management import execute_from_command_line

        args = [*args]
        args.insert(0, 'manage.py')
        # os.environ.setdefault("DJANGO_SETTINGS_MODULE", '.'.join(['apps', self.app, 'data')
        settings.configure(**data_settings)
        django.setup()
        execute_from_command_line(args)
        if not self.debug:
            os.remove(os.path.join(APPS_PATH, self.app, 'data', 'models.py'))
            os.remove(os.path.join(APPS_PATH, self.app, 'data', 'app.py'))

    @context_args('app', 'debug')
    def list(self):
        """
        list all migrations, ones marked with + are applied.
        """
        self._call_django('showmigrations', self.app)

    @context_args('app', 'noinput', 'debug')
    def make(self, dry: bool = False, merge: bool = False, empty: bool = False, name: str = None):
        """
        make new migration related to app model changes
        :param dry: show what migrations would be made; don't actually write them
        :param merge: enable fixing of migration conflicts
        :param empty: create empty migration
        :param name: use this name for migration file
        """
        args = ['makemigrations', self.app]
        if dry: args.append('--dry-run')
        if merge: args.append('--merge')
        if empty: args.append('--empty')
        if self.noinput: args.append('--noinput')
        if name: args.extend(['-n', name])
        self._call_django(*args)

    @context_args('app', 'noinput', 'debug')
    def apply(self, name: str = None, fake: bool = False, fake_init: bool = False, plan: bool = False):
        """
        apply migrations to database
        :param name: migration name ('zero' to rollback all)
        :param fake: mark migrations as run without actually running them
        :param fake_init: detect if tables already exist and fake-apply initial migrations if so
        :param plan: shows a list of the migration actions that will be performed
        """
        args = ['migrate', self.app]
        if name:
            args.append(name)
        if self.noinput: args.append('--noinput')
        if fake: args.append('--fake')
        if fake_init: args.append('--fake-initial')
        if plan: args.append('--plan')
        self._call_django(*args)

    @context_args('app', 'debug')
    def sql(self, migration: str, back: bool = False):
        """
        prints the SQL statements for the named migration
        :param migration: migration name
        :param back: creates SQL to unapply the migration, rather than to apply it
        """
        args = ['sqlmigrate', self.app, migration]
        if back: args.append('--backwards')
        self._call_django(*args)

    @context_args('app', 'noinput', 'debug')
    def squash(self, start_migration: str, end_migration: str, no_optimize: bool = False, name: str = None):
        """
        squashes an existing set of migrations into a single new one (including start and end)
        :param start_migration: start migration name
        :param end_migration: end migration name
        :param no_optimize: do not add a header comment to the new squashed
        :param name: name of the new squashed migration
        """
        args = ['squashmigrations', self.app, start_migration, end_migration]
        if no_optimize: args.append('--no-optimize')
        if self.noinput: args.append('--noinput')
        if name: args.extend(['--squashed-name', name])
        self._call_django(args)


class Schema:
    """
    Work with database schema
    :param app: app name (auto-detection by current directory)
    """

    app: str = lambda: _detect_app()

    def _check_postgres(self) -> Optional[Database]:
        from core.models import expose_datebases, dbinfo

        db = expose_datebases(self.app)
        if not db:
            print(f'default db does not configured for app {self.app}')
            return None
        if dbinfo[self.app]['db'].kwargs['provider'] != 'postgres':
            print(f'schemas available for postgres only')
            return None
        return db

    @context_args('app')
    def list(self):
        """
        print all schemas
        """
        from pony.orm import db_session

        db = self._check_postgres()
        if not db:
            return

        print('Schemas list:')
        with db_session():
            res = db.select("select nspname from pg_catalog.pg_namespace where left(nspname, 3) != 'pg_'")
            for line in res:
                print('  ' + line)

    @context_args('app')
    def add(self, name: str):
        """
        add new schema
        :param name: schema name
        """
        from pony.orm import db_session

        db = self._check_postgres()
        if not db:
            return

        with db_session():
            with db.get_connection().cursor() as cur:
                cur.execute(f'create schema if not exists "{name}"')
                print(cur.statusmessage)


def execute_from_command_line(argv):
    main = ExposeToArgs(Main())
    main.add_commands(Migrate())
    main.add_commands(Schema())
    main.execute(argv)