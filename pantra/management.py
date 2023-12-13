from __future__ import annotations

import asyncio
from pathlib import Path
import sys
import typing

from .args import *
from .settings import config

if typing.TYPE_CHECKING:
    from typing import *
    from quazy import *


def _detect_app():
    path = Path.cwd()
    if path == config.APPS_PATH:
        return Empty
    if path.is_relative_to(config.APPS_PATH):
        return path.relative_to(config.APPS_PATH).parts[0]
    if path.is_relative_to(config.COMPONENTS_PATH):
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

    def run_backend(self):
        """
        run pantra backend workers facility in separate process
        """
        import os
        from .watchers import start_observer, stop_observer
        from .session import Session

        if config.WORKER_SERVER.run_with_web:
            print(f"This backend `{config.WORKER_SERVER.__name__}` should run with WEB only")
            return

        if not config.PRODUCTIVE:
            start_observer()

        if os.name == 'nt':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        asyncio.run(Session.run_server_worker())

    def apps(self):
        """
        list all apps
        """
        for f in config.APPS_PATH.glob('*'):
            if not f.name.startswith('_') and f.is_dir():
                print(f.name)

    def collect_dtd(self):
        """
        collect html5.dtd schema for editor autocomplete and inspection
        """
        from .components.update_dtd import update_dtd
        update_dtd()
        print('Done')

    def get_boilerplate(self):
        """
        download basic template
        """
        import tempfile
        import os
        import shutil
        import zipfile

        import requests
        from .settings import config

        REPO_BRANCH = 'pantra-master'

        with tempfile.NamedTemporaryFile(delete=False) as f:
            res = requests.get("https://github.com/zergos/pantra/archive/master.zip")
            if res.status_code != 200:
                print(f'{res.status_code} {res.reason}')
                return

            f.write(res.content)
            temp_name = f.name

        cwd = config.BASE_PATH
        with zipfile.ZipFile(temp_name, "r") as zip:
            for member in ['components', 'css', 'apps/demo']:
                for file in zip.namelist():
                    if file.startswith(f'{REPO_BRANCH}/{member}/'):
                        zip.extract(file, cwd)


        for file_name in (cwd / REPO_BRANCH).glob('*'):
            if (cwd / file_name.name).exists():
                print(f"directory `{file_name.name}` exists, skipped")
                continue
            print(f'move {file_name} to {cwd}')
            shutil.move(file_name, cwd)

        shutil.rmtree(cwd / REPO_BRANCH)

        #config.APPS_PATH.mkdir(exist_ok=True)
        config_file = (config.APPS_PATH / 'config.py')
        if not config_file.exists():
            config_file.write_text('# apps configs')

        os.remove(temp_name)
        print('Done')


class Migrate:
    """
    Work with database changes/migrations
    :param app: app name (auto-detection by current directory)
    """
    app: str = lambda: _detect_app()
    noinput: bool = False

    def _check_migrations(self) -> bool:
        from pantra.models import expose_database
        from quazy.migrations import check_migrations
        db = expose_database(self.app)

        if not check_migrations(db):
            print('Migrations not activated. Run with `migrate.activate` first.')
            return False

        return True

    def _expose_db(self) -> tuple[DBFactory, str] | tuple[None, None]:
        from pantra.models import dbinfo
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

        db, schema = self._expose_db()
        if not db:
            return
        commands, new_tables = get_changes(db, schema, [(line.strip(':')[0], line.strip(':')[1]) for line in rename.split(" ") if line])
        if not commands:
            print("No changes")
            return

        apply_changes(db, schema, commands, new_tables, comments)

    @context_args('app')
    def reset(self):
        """
        reset all migrations and delete `app` tables
        """
        if not self._check_migrations():
            return

        db, schema = self._expose_db()
        if not db:
            return

        from quazy.migrations import clear_migrations
        clear_migrations(db, schema)

        print('Done')

    @context_args('app')
    def drop(self):
        """
        drop all migration tables
        """
        if not self._check_migrations():
            return

        db, schema = self._expose_db()
        if not db:
            return

        from quazy.migrations import clear_migrations
        clear_migrations(db)

        print("Done")

    @context_args('app')
    def dump(self, directory: str):
        """
        dump all migrations to selected directory
        :param directory:  to save migration dumps
        """
        from quazy.migrations import dump_changes

        if not self._check_migrations():
            return

        db, schema = self._expose_db()
        if not db:
            return

        dump_changes(db, schema, directory)

        print("done")

    @context_args('app')
    def stub(self):
        """
        generate stub file (pyi) for better code completion
        """
        from quazy.stub import gen_stub

        db, schema = self._expose_db()
        if not db:
            return

        file_name = sys.modules[f'apps.{self.app}.data'].__file__ + 'i'
        with open(file_name, "wt") as f:
            f.write(gen_stub(db, schema))
            f.write('\ndb: DBFactory')

        print("done")


class Schema:
    """
    Work with database schema
    :param app: app name (auto-detection by current directory)
    """

    app: str = lambda: _detect_app()

    def _check_postgres(self) -> Optional[DBFactory]:
        from pantra.models import expose_database, dbinfo

        db = expose_database(self.app)
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
        path = Path.cwd()
        if path.is_relative_to(config.BASE_PATH):
            path = path.relative_to(config.BASE_PATH)
            while path.parent.name:
                if path.parent.name == 'locale':
                    return path.name
                path = path.parent
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
            path = config.COMPONENTS_PATH
        else:
            path = config.APPS_PATH / self.app
        ini_name = path / 'babel.ini'
        with ini_name.open("wt") as f:
            f.write('[extractors]\npython = pantra.trans:extract_python\nhtml = pantra.trans:extract_html\ndata = pantra.trans:extract_data\n')
            f.write('[data: **/data/__init__.py]\n[python: **.py]\n[html: **.html]\n')

        pot_name = path / 'app.po'

        args = ['', '-q', 'extract']
        args.extend(['-F', str(ini_name)])
        args.extend(['-o', str(pot_name)])
        args.append('--sort-by-file')
        args.append(f'--project=Pantra App "{self.app}"')
        args.extend(['-c', 'NOTE'])
        if copyright:
            args.append(f'--copyright-holder={copyright}')
        if email:
            args.append(f'--msgid-bugs-address={email}')
        if version:
            args.append(f'--version={version}')
        args.append(str(path))
        CommandLineInterface().run(args)

        dest_name = path / 'locale' / self.locale / 'LC_MESSAGES' / 'messages.po'
        if not dest_name.exists():
            args = ['', 'init']
        else:
            args = ['', 'update']
        args.extend(['-i', str(pot_name)])
        args.extend(['-l', self.locale])
        # args.extend(['-D', self.app])
        args.extend(['-d', str(path / 'locale')])
        CommandLineInterface().run(args)

        if not no_clear:
            ini_name.unlink()
            pot_name.unlink()

        if no_compile:
            return

        args = ['', 'compile']
        args.extend(['-i', str(dest_name)])
        args.extend(['-l', self.locale])
        # args.extend(['-D', self.app])
        args.extend(['-d', str(path / 'locale')])
        args.append('--statistics')
        CommandLineInterface().run(args)


def execute_from_command_line(argv=None):
    main = ExposeToArgs(Main)
    main.add_commands(Migrate)
    main.add_commands(Schema)
    main.add_commands(Locale)
    main.execute(argv)


if __name__ == "__main__":
    execute_from_command_line()
