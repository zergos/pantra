from __future__ import annotations

import os
import asyncio
from pathlib import Path
import sys
import typing

try:
    import quazy.migrations as qm
except ImportError:
    pass

from .cli4class import extra_args, run_command
from .settings import config


if typing.TYPE_CHECKING:
    from typing import *
    try:
        from quazy import DBFactory
    except ImportError:
        pass


def _detect_app() -> str | None:
    path = Path.cwd()
    if path == config.APPS_PATH:
        return None
    if path.is_relative_to(config.APPS_PATH):
        return path.relative_to(config.APPS_PATH).parts[0]
    if path.is_relative_to(config.COMPONENTS_PATH):
        return 'Core'
    return None

class AppProvider:
    """Provides `app` argument by current directory

    Parameters:
        app: app name or "Core" for common components
    """

    app: str = lambda: _detect_app()


def _expose_db(app) -> tuple[DBFactory, str] | tuple[None, None]:
    from pantra.models import dbinfo
    import importlib

    try:
        data = importlib.import_module(f'apps.{app}.data')
    except ModuleNotFoundError:
        print('No `data` module in app')
        return None, None

    if not hasattr(data, 'db'):
        print('No `db` attribute in `data` module of app')
        return None, None

    db = data.db
    return db, dbinfo[app]['db'].schema
    #return db, [v['db']['schema'] for v in dbinfo.values()]

class Main(AppProvider):
    """Pantra management CLI"""

    def run(self, host: str = '127.0.0.1', port: int = 8005, cached: bool = False):
        """run pantra application bound to host and port

        Args:
            host: local IP address to bind
            port: number of local port
            cached: whether to use cached app
        """
        from pantra.main import run as run_main

        if cached:
            os.environ['PANTRA_RUN_CACHED'] = 'yes'
            config._late_init()
        run_main(host, port)

    def run_backend(self):
        """run pantra backend workers facility in separate process"""
        import os
        from .watchers import start_observer
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
        """list all apps"""
        for f in config.APPS_PATH.glob('*'):
            if not f.name.startswith('_') and f.is_dir():
                print(f.name)

    def collect_dtd(self):
        """collect html5.dtd schema for editor autocomplete and inspection"""
        from .components.update_dtd import update_dtd
        update_dtd()
        print('Done')

    def get_boilerplate(self, version: str = None):
        """download basic template

        Args:
            version: version to download (default is current)
        """
        import tempfile
        import os
        import shutil
        import zipfile

        import requests
        from .settings import config
        from . import VERSION

        if not version:
            version = VERSION

        REPO_BRANCH = 'pantra-' + version

        with tempfile.NamedTemporaryFile(delete=False) as f:
            res = requests.get(f"https://github.com/zergos/pantra/archive/refs/tags/{version}.zip")
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

    @extra_args('app')
    def build_cache(self):
        """build app cache"""
        from pantra.cached.builder import CacheBuilder

        builder = CacheBuilder(self.app)
        print("Generate templates...")
        builder.make('Main')
        builder.collect_data()
        builder.collect_styles()
        builder.collect_js()
        builder.collect_static()
        builder.collect_locale()
        print('Done')

class Database(AppProvider):
    """Database-related commands"""

    @extra_args('app')
    def check(self):
        """check database connection"""
        from pantra.models import expose_database
        db = expose_database(self.app)
        db.select("select 1")
        print('Done')

    @extra_args('app')
    def stub(self):
        """generate stub file (pyi) for better code completion"""
        db, _ = _expose_db(self.app)
        if not db:
            return

        from quazy.stub import gen_stub
        file_name = sys.modules[f'apps.{self.app}.data'].__file__ + 'i'
        with open(file_name, "wt") as f:
            f.write(gen_stub(db))
            f.write('\ndb: DBFactory')

        print("done")

class Migrations(AppProvider):
    """Work with database changes/migrations"""

    def _check_migrations(self) -> bool:
        from pantra.models import expose_database
        db = expose_database(self.app)

        if not qm.check_migrations(db):
            print('Migrations not activated. Run with `database.migrations.activate` first.')
            return False

        return True

    @extra_args('app')
    def activate(self):
        """activate migrations for current app and scheme"""
        db, _ = _expose_db(self.app)
        if not db:
            return
        qm.activate_migrations(db)
        print("Migrations activated.")

    @extra_args('app')
    def list(self):
        """list all migrations, ones marked with + are applied."""
        if not self._check_migrations():
            return

        db, schema = _expose_db(self.app)
        if not db:
            return

        all_migrations = qm.get_migrations_list(db, schema)

        if all_migrations:
            for mig in all_migrations:
                print(mig)
        else:
            print("No migrations yet. Run `migration.apply` first.")

    @extra_args('app')
    def show(self, rename: str = ""):
        """show current changes

        Args:
            rename: rename list in format `old_name1:new_name1 old_name2:new_name2 ...`
        """
        if not self._check_migrations():
            return

        db, schema = _expose_db(self.app)
        if not db:
            return
        diff = qm.compare_schema(db,
                                 [(line.split(':')[0], line.split(':')[1]) for line in rename.split(" ") if line],
                                 schema=schema)

        print(diff.info())

    @extra_args('app')
    def apply(self, rename: str = "", comments: str = "", debug: bool = False):
        """make migrations and apply changes to database

        Args:
            rename: rename list in format `old_name1:new_name1 old_name2:new_name2 ...`
            comments: comments bound to changes
            debug: show SQL statements
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

        db, schema = _expose_db(self.app)
        if not db:
            return
        diff = qm.compare_schema(db,
                                 [(line.split(':')[0], line.split(':')[1]) for line in rename.split(" ") if line],
                                 schema=schema)
        if not diff.commands:
            print("No changes")
            return

        qm.apply_changes(db, diff, comments)

    @extra_args('app')
    def revert(self, index: str):
        """revert changes to specified migration index

        Args:
            index: migration index (ex. 0005)
        """
        if not self._check_migrations():
            return

        db, schema = _expose_db(self.app)
        if not db:
            return
        diff = qm.compare_schema(db, migration_index=index, schema=schema)
        if not diff.commands:
            print("No changes")
            return

        qm.apply_changes(db, diff)

    @extra_args('app')
    def reset(self):
        """reset all migrations and delete `app` tables"""
        if not self._check_migrations():
            return

        db, schema = _expose_db(self.app)
        if not db:
            return

        qm.clear_migrations(db, schema)

        print('Done')

    @extra_args('app')
    def drop(self):
        """drop all migration tables"""
        if not self._check_migrations():
            return

        db, schema = _expose_db(self.app)
        if not db:
            return

        qm.clear_migrations(db, schema)

        print("Done")

    @extra_args('app')
    def dump(self, directory: str, as_yaml: bool = False):
        """dump all migrations to selected directory

        Args:
            directory:  to save migration dumps
            as_yaml: save as YAML format (JSON by default)
        """
        if not self._check_migrations():
            return

        db, schema = _expose_db(self.app)
        if not db:
            return

        qm.dump_changes(db, schema, directory, as_yaml)

        print("done")

class Schema(AppProvider):
    """Work with database schema"""
    def _check_postgres(self) -> Optional[DBFactory]:
        from pantra.models import expose_database, dbinfo

        db = expose_database(self.app)
        if not db:
            print(f'default `db` is not configured for app `{self.app}`')
            return None
        if dbinfo[self.app]['db'].kwargs['provider'] != 'postgres':
            print(f'schemas available for `postgres` only')
            return None
        return db

    @extra_args('app')
    def list(self):
        """print all schemas"""
        db = self._check_postgres()
        if not db:
            return

        print('Schemas list:')
        with db.select("select nspname from pg_catalog.pg_namespace where left(nspname, 3) != 'pg_'") as res:
            for line in res:
                print('  ' + line[0])

    @extra_args('app')
    def add(self, name: str):
        """add new schema

        Args:
            name: schema name
        """
        db = self._check_postgres()
        if not db:
            return

        with db.execute(f'create schema if not exists "{name}"') as res:
            print(res.statusmessage)


class Locale(AppProvider):
    """Work with L10n and I18n

    Args:
        locale: locale name
    """

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
        return None

    def list(self, filter: str):
        """print all available locales

        Args:
            filter: filter by partial name
        """
        from babel.localedata import locale_identifiers
        for l in locale_identifiers():
            if filter and filter not in l:
                continue
            print(l)

    @extra_args('locale')
    def info(self):
        """print locale information"""
        from babel import Locale
        l = Locale.parse(self.locale)
        print(l.display_name)

    @extra_args('app', 'locale')
    def gen(self, copyright: str = None, email: str = None, version: str = None, no_compile: bool = False, no_clear: bool = False):
        """collect messages for selected app

        Args:
            copyright: copyright holder
            email: email address for bugs information
            version: version number (X.Y)
            no_compile: don't compile after update
            no_clear: don't clear Babel temp files (`babel.ini` and `app.po`)
        """
        from babel.messages.frontend import CommandLineInterface

        if self.app == 'Core':
            path = config.COMPONENTS_PATH
        else:
            path = config.APPS_PATH / self.app
        ini_name = path / 'babel.ini'
        with ini_name.open("wt") as f:
            f.write('[extractors]\n'
                    'python = pantra.trans:extract_python\n'
                    'html = pantra.trans:extract_html\n'
                    'data = pantra.trans:extract_data\n')
            try:
                import quazy
                f.write('[data: **/data/__init__.py]\n')
            except ImportError:
                pass
            f.write('[python: **.py]\n'
                    '[html: **.html]\n')

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
    run_command({
        "main": Main,
        "database": {
            "main": Database,
            "migrations": Migrations,
            "schema": Schema,
        },
        "locale": Locale,
    }, argv)


if __name__ == "__main__":
    execute_from_command_line()
