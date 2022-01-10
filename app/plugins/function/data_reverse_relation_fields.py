from systems.plugins.index import BaseProvider


class Provider(BaseProvider('function', 'data_reverse_relation_fields')):

    def exec(self, data_type):
        facade = self.command.facade(data_type)
        return list(facade.get_reverse_relations().keys())
