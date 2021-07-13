from django.db import DEFAULT_DB_ALIAS
from django.db.backends.sqlite3 import base as sqlite3

from utility.environment import Environment


class DatabaseWrapper(sqlite3.DatabaseWrapper):

    def __init__(self, settings_dict, alias = DEFAULT_DB_ALIAS):
        settings_dict['NAME'] = Environment.get_db_path()
        settings_dict['ATOMIC_REQUESTS'] = True
        super().__init__(settings_dict, alias)
