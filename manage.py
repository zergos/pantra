import os

from core.args import *
from core.models import expose_datebases, dbinfo
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
    Work with database migrations
    :param app: app name
    """
    app: str

    def _migrations_path(self):
        return os.path.join(APPS_PATH, self.app, 'data', 'migrations')

    def _get_db_and_path(self):
        db = expose_datebases(self.app, False)
        path = self._migrations_path()
        if not os.path.exists(path):
            print('migration path not found')
            return None, None, None
        return db, path, dbinfo[self.app]['db'].kwargs

    @context_args('app')
    def list(self):
        """
        list all migrations, ones marked with + are applied.
        """
        db, path, kwargs = self._get_db_and_path()
        if not db: return
        db.migrate(command='list', migration_dir=path, **kwargs)

    @context_args('app')
    def make(self, empty: bool = False, v: bool = False):
        """
        make new migration related to app model changes
        :param empty: produce file with empty content
        :param v: verbose
        """

        db = expose_datebases(self.app, False)
        path = self._migrations_path()
        if not os.path.exists(path):
            os.mkdir(path, 0o755)
        args = ['make']
        if v:
            args.append('-v')
        if empty:
            args.append('--empty')
        db.migrate(command=' '.join(args), migration_dir=path, **dbinfo[self.app]['db'].kwargs)

    @context_args('app')
    def apply(self, from_idx: str = None, to_idx: str = None, keep: bool = False, v: bool = False):
        """
        apply migrations to database
        :param from_idx: start from selected migration
        :param to_idx: to select migration
        :param keep: keep data on initial migration
        :param v: verbose
        """

        db, path, kwargs = self._get_db_and_path()
        if not db: return
        args = ['apply']
        if from_idx:
            args.append(from_idx)
        if to_idx:
            args.append(to_idx)
        if keep:
            args.append('--fake-initial')
        if v:
            args.append('-v')
        db.migrate(command=' '.join(args), migration_dir=path, **kwargs)

    @context_args('app')
    def sql(self, from_idx: str, to_idx: str = None):
        """
        show the sql for the migrations, it should not be applied yet.
        :param from_idx: start from selected migration
        :param to_idx: to select migration
        """
        db, path, kwargs = self._get_db_and_path()
        if not db: return
        args = ['sql']
        if from_idx:
            args.append(from_idx)
        if to_idx:
            args.append(to_idx)
        db.migrate(command=' '.join(args), migration_dir=path, **kwargs)


if __name__ == '__main__':
    main = ExposeToArgs(Main())
    main['migrate'] = ExposeToArgs(Migrate())
    main.execute()


