from django.core.management.base import CommandError

from systems.command import SimpleCommand
from data.environment import models


class GetCommand(SimpleCommand):

    def get_description(self, overview):
        if overview:
            return """get current cluster environment (for all operations)

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """get current cluster environment (for all operations)
                      
Etiam mattis iaculis felis eu pharetra. Nulla facilisi. 
Duis placerat pulvinar urna et elementum. Mauris enim risus, 
mattis vel risus quis, imperdiet convallis felis. Donec iaculis 
tristique diam eget rutrum.

Etiam sit amet mollis lacus. Nulla pretium, neque id porta feugiat, 
erat sapien sollicitudin tellus, vel fermentum quam purus non sem. 
Mauris venenatis eleifend nulla, ac facilisis nulla efficitur sed. 
Etiam a ipsum odio. Curabitur magna mi, ornare sit amet nulla at, 
scelerisque tristique leo. Curabitur ut faucibus leo, non tincidunt 
velit. Aenean sit amet consequat mauris.
"""

    def add_arguments(self, parser):
        pass


    def handle(self, *args, **options):
        state = models.State.objects.get(name = 'environment')
        
        if state:
            print(" > Current environment: {}".format(self.style.SUCCESS(state.value)))
            print(" > Last updated: {}".format(state.timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")))
        else:
            raise CommandError(self.style.WARNING("Environment state has not been set"))
