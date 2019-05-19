from collections import OrderedDict

from django.conf import settings

from systems.command.parsers import config, reference, token
from utility.data import ensure_list


class AppOptions(object):

    def __init__(self, command):
        self.command = command
        self._options = {}

        self.parsers = OrderedDict()
        self.parsers['token'] = token.TokenParser(command)
        self.parsers['config'] = config.ConfigParser(command)
        self.parsers['reference'] = reference.ReferenceParser(command)

    def initialize(self, reset = False):
        for name, parser in self.parsers.items():
            parser.initialize(reset)

    def interpolate(self, value, parsers = []):
        parsers = ensure_list(parsers)
        for name, parser in self.parsers.items():
            if not parsers or name in parsers:
                value = parser.interpolate(value)
        return value


    def get(self, name, default = None):
        return self._options.get(name, default)

    def add(self, name, value):
        env = self.command.get_env()

        if self.command.interpolate_options() and (not env.host or (self.command.remote_exec() and settings.API_EXEC)):
            self.initialize()
            self._options[name] = self.interpolate(value)
        else:
            self._options[name] = value

        return self._options[name]

    def rm(self, name):
        return self._options.pop(name)

    def clear(self):
        self._options.clear()

    def export(self):
        return self._options
