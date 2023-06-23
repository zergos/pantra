from __future__ import annotations

import sys
import typing

from pantra.args import *
from pantra.defaults import *

if typing.TYPE_CHECKING:
    from typing import *
    from quazy import *

def _detect_app():
    path = os.getcwd()
    if path.startswith(APPS_PATH):
        path = os.path.relpath(path, APPS_PATH)
        while os.path.dirname(path):
            path = os.path.dirname(path)
        return path
    if path.startswith(COMPONENTS_PATH):
        return 'Core'
    return Empty


class Main:
    """
    Manage Pantra
    :param app: app name
    """

    app: str = lambda: _detect_app()

    def run(self, host: str = '127.0.0.1', port: int = 8005):
        """
        run pantra application on host and port
        :param host: local IP address to bind
        :param port: number of local port
        """
        from pantra.main import run as run_main

        run_main(host, port)

    def apps(self):
        """
        list all apps
        """
        for f in os.listdir(APPS_PATH):
            print(f)

    def collect_dtd(self):
        '''
        collect html5.dtd schema for editor autocomplete and inspection
        '''
        from .components.update_dtd import update_dtd
        update_dtd()
        print('Done')


class Migrate:
    """
    Work with database changes/migrations
    :param app: app name (auto-detection by current directory)
    """
    app: str = lambda: _detect_app()
    noinput: bool = False

    def _check_migrations(self) -> bool:
        from pantra.models import expose_databases, dbinfo
        from quazy.migrations import check_migrations
        db = expose_databases(self.app)

        if not check_migrations(db):
            print('Migrations not activated. Run with `migrate.activate` first.')
            return False

        return True

    def _expose_db(self) -> tuple[DBFactory, str] | tuple[None, None]:
        from pantra.models import expose_databases, dbinfo
        import importlib

        try:
            data = importlib.import_module(f'apps.{self.app}.data')
        except ModuleNotFoundError:
            print('No `data` module in app')
            return None, None

        if not hasattr(data, 'db'):
            print('No `db` attribute in `data` module of app')
            return None, None

        db = data.db
        return db, dbinfo[self.app]['db'].schema


    @context_args('app')
    def activate(self):
        """
        activate migrations for current app and scheme
        """
        from quazy.migrations import activate_migrations

        db, schema = self._expose_db()
        if not db:
            return
        activate_migrations(db)
        print("Migrations activated.")

    @context_args('app')
    def list(self):
        """
        list all migrations, ones marked with + are applied.
        """
        if not self._check_migrations():
            return

        from quazy.migrations import get_migrations

        db, schema = self._expose_db()
        if not db:
            return

        all_migrations = get_migrations(db, schema)

        if all_migrations:
            for m in all_migrations:
                print('{}{} {:%x %X} {}'.format("*" if m[0] else " ", m[1], m[2], m[3]))
        else:
            print("No migrations yet. Run `migrate.apply` first.")

    @context_args('app')
    def show(self, rename: str = ""):
        """
        show current changes
        :param rename: rename list in format `old_name1:new_name1 old_name2:new_name2 ...`
        """
        if not self._check_migrations():
            return

        from quazy.migrations import get_changes

        db, schema = self._expose_db()
        if not db:
            return
        commands, _ = get_changes(db, schema, [(line.strip(':')[0], line.strip(':')[1]) for line in rename.split(" ") if line])

        if not commands:
            print("No changes")
            return

        for i, command in enumerate(commands):
            print(f'{i+1}. {command}')

    @context_args('app')
    def apply(self, rename: str = "", comments: str = "", debug: bool = False):
        """
        make migrations and apply changes to database
        :param rename: rename list in format `old_name1:new_name1 old_name2:new_name2 ...`
        :param comments: comments bound to changes
        :param debug: show SQL statements
        """
        if not self._check_migrations():
            return

        if debug:
            import logging

            logger = logging.getLogger('psycopg')
            logger.setLevel(logging.DEBUG)

            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)

            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)

            logger.addHandler(console_handler)

        from quazy.migrations import get_changes, apply_changes
        import importlib

        db, schema = self._expose_db()
        if not db:
            return
        commands, new_tables = get_changes(db, schema, [(line.strip(':')[0], line.strip(':')[1]) for line in rename.split(" ") if line])
        if not commands:
            print("No changes")
            return

        apply_changes(db, schema, commands, new_tables, comments)


class Schema:
    """
    Work with database schema
    :param app: app name (auto-detection by current directory)
    """

    app: str = lambda: _detect_app()

    def _check_postgres(self) -> Optional[DBFactory]:
        from pantra.models import expose_databases, dbinfo

        db = expose_databases(self.app)
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
        db = self._check_postgres()
        if not db:
            return

        print('Schemas list:')
        with db.select("select nspname from pg_catalog.pg_namespace where left(nspname, 3) != 'pg_'") as res:
            for line in res:
                print('  ' + line[0])

    @context_args('app')
    def add(self, name: str):
        """
        add new schema
        :param name: schema name
        """
        db = self._check_postgres()
        if not db:
            return

        with db.select(f'create schema if not exists "{name}"') as res:
            print(res)


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

        if self.app == 'Core':
            path = COMPONENTS_PATH
        else:
            path = os.path.join(APPS_PATH, self.app)
        ini_name = os.path.join(path, 'babel.ini')
        with open(ini_name, 'wt') as f:
            f.write('[extractors]\npython = pantra.trans:extract_python\nhtml = pantra.trans:extract_html\nxml = pantra.trans:extract_xml\n')
            f.write('[python: **.py]\n[html: **.html]\n[xml: **.xml]\n')

        pot_name = os.path.join(path, 'app.po')

        args = ['', '-q', 'extract']
        args.extend(['-F', ini_name])
        args.extend(['-o', pot_name])
        args.append('--sort-by-file')
        args.append(f'--project=Pantra App "{self.app}"')
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
