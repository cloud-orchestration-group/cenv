from settings.roles import Roles
from .router import RouterCommand
from .action import ActionCommand


class StateRouterCommand(RouterCommand):

    def get_priority(self):
        return 95


class StateActionCommand(ActionCommand):

    def groups_allowed(self):
        return [
            Roles.admin,
            Roles.config_admin
        ]

    def server_enabled(self):
        return True

    def get_priority(self):
        return 95
