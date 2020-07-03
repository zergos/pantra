from __future__ import annotations

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
    """
    Manage fruits
    :param app: app name
    """

    app: str = lambda: _detect_app()

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

    @context_args('app')
    def pony(self, x: bool = False):
        """
        generate pony code for type checker
        :param x: exclude default db initial block
        """

        from core.models import expose_to_pony
        expose_to_pony(self.app, not x)
        print('Done')

    @context_args('app')
    def django(self):
        """
        generate django code for debugging
        """

        from core.models import expose_to_django
        expose_to_django(self.app)
        print('Done')

    @context_args('app')
    def check(self):
        """
        load and check models definition runtime
        """

        from core.models import expose_databases
        expose_databases(self.app)
        print('Check OK')


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
        from core.models import expose_databases, dbinfo

        db = expose_databases(self.app)
        if not db:
            print(f'default db does not configured for app {self.app}')
            return None
        if dbinfo[self.app]['db'].factory.kwargs['provider'] != 'postgres':
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


class Locale:
    """
    Work with L10n and I18n
    :param app: app name (auto-detection by current directory)
    :param locale: set locale name
    """

    app: str = lambda: _detect_app()
    locale: str = lambda: Locale._detect_locale()

    @staticmethod
    def _detect_locale():
        path = os.getcwd()
        if path.startswith(BASE_PATH):
            path = os.path.relpath(path, BASE_PATH)
            while os.path.dirname(path):
                path, tail = os.path.split(path)
                if os.path.basename(path) == 'locale':
                    return tail
        return Empty

    def list(self, filter: str = None):
        """
        print all available locales
        :param filter: filter by partial name
        """
        from babel.localedata import locale_identifiers
        for l in locale_identifiers():
            if filter and filter not in l:
                continue
            print(l)

    @context_args('locale')
    def info(self):
        """
        print locale information
        """
        from babel import Locale
        l = Locale.parse(self.locale)
        print(l.display_name)

    @context_args('app', 'locale')
    def gen(self, copyright: str = None, email: str = None, version: str = None, no_compile: bool = False, no_clear: bool = False):
        """
        collect messages for selected app
        :param copyright: copyright holder
        :param email: email address for bugs information
        :param version: version number (X.Y)
        :param no_compile: don't compile after update
        :param no_clear: don't clear Babel temp files (`babel.ini` and `app.po`)
        """
        from babel.messages.frontend import CommandLineInterface

        if self.app == 'C':
            self.app = 'Components'
            path = COMPONENTS_PATH
        else:
            path = os.path.join(APPS_PATH, self.app)
        ini_name = os.path.join(path, 'babel.ini')
        with open(ini_name, 'wt') as f:
            f.write('[extractors]\npython = core.trans:extract_python\nhtml = core.trans:extract_html\nxml = core.trans:extract_xml\n')
            f.write('[python: **.py]\n[html: **.html]\n[xml: **.xml]\n')

        pot_name = os.path.join(path, 'app.po')

        args = ['', 'extract']
        args.extend(['-F', ini_name])
        args.extend(['-o', pot_name])
        args.append('--sort-by-file')
        args.append(f'--project=Fruits App "{self.app}"')
        args.extend(['-c', 'NOTE'])
        if copyright:
            args.append(f'--copyright-holder={copyright}')
        if email:
            args.append(f'--msgid-bugs-address={email}')
        if version:
            args.append(f'--version={version}')
        args.append(path)
        CommandLineInterface().run(args)

        dest_name = os.path.join(path, 'locale', self.locale, 'LC_MESSAGES', 'messages.po')
        if not os.path.exists(dest_name):
            args = ['', 'init']
        else:
            args = ['', 'update']
        args.extend(['-i', pot_name])
        args.extend(['-l', self.locale])
        # args.extend(['-D', self.app])
        args.extend(['-d', os.path.join(path, 'locale')])
        CommandLineInterface().run(args)

        if not no_clear:
            os.remove(ini_name)
            os.remove(pot_name)

        if no_compile:
            return

        args = ['', 'compile']
        args.extend(['-i', dest_name])
        args.extend(['-l', self.locale])
        # args.extend(['-D', self.app])
        args.extend(['-d', os.path.join(path, 'locale')])
        args.append('--statistics')
        CommandLineInterface().run(args)


def execute_from_command_line(argv):
    main = ExposeToArgs(Main())
    main.add_commands(Migrate())
    main.add_commands(Schema())
    main.add_commands(Locale())
    main.execute(argv)
