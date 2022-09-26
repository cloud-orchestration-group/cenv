from ..errors import RestrictedError, UpdateError
from utility.data import ensure_list, normalize_dict
from utility.query import get_queryset

import re
import logging


logger = logging.getLogger(__name__)


class ModelFacadeUpdateMixin(object):

    def create(self, key, values = None):
        if values is None:
            values = {}

        values[self.key()] = key
        self._check_scope(values)
        return self.model(**values)

    def get_or_create(self, key):
        instance = self.retrieve(key)
        if not instance:
            instance = self.create(key)
        return instance


    def split_field_values(self, values):
        relation_index = self.get_extra_relations()
        fields = {}
        relations = {}

        for field, value in values.items():
            if field in relation_index:
                relations[field] = value
            else:
                fields[field] = value

        return fields, relations


    def store(self, key, values = None, command = None, relation_key = False):
        if values is None:
            values = {}

        filters = { self.key(): key }
        values = normalize_dict(values)
        instance = self.retrieve(key, **filters)
        created = False

        if not instance:
            instance = self.create(key, filters)
            created = True

        fields, relations = self.split_field_values(values)

        for field, value in fields.items():
            setattr(instance, field, value)

        instance.save()
        self.save_relations(
            instance,
            relations,
            command = command,
            relation_key = relation_key
        )
        return (instance, created)


    def save_relations(self, instance, relations, relation_key = False, command = None):
        relation_index = self.get_extra_relations()
        resave = False

        for field, value in relations.items():
            # value = [[+-][provider:]id,...]
            if command:
                facade = command.facade(
                    relation_index[field]['model'].facade.name
                )
            else:
                facade = relation_index[field]['model'].facade

            if relation_index[field]['multiple']:
                self._update_related(facade, instance, field, value, relation_key, command)
            else:
                self._set_related(facade, instance, field, value, relation_key, command)
                resave = True

        if resave:
            instance.save()


    def _update_related(self, facade, instance, relation, ids, use_key, command):
        queryset = get_queryset(instance, relation)

        if ids is None:
            if queryset:
                queryset.clear()
            else:
                raise UpdateError("Instance {} relation {} is not a valid queryset".format(getattr(instance, instance.facade.key()), relation))
        else:
            all_ids = []
            input_ids = []
            add_ids = []
            remove_ids = []

            if queryset:
                id_field = facade.key() if use_key else facade.pk
                for sub_instance in queryset.all():
                    all_ids.append(getattr(sub_instance, id_field))

            for id in ids:
                if id.startswith('+'):
                    add_ids.append(id[1:])
                elif id.startswith('-'):
                    remove_ids.append(id[1:])
                else:
                    input_ids.append(id)

            if input_ids:
                if use_key:
                    input_values = [ id.split(':')[-1] for id in input_ids ]
                    remove_ids = []

                    for id in all_ids:
                        if id not in input_values:
                            remove_ids.append(id)
                else:
                    remove_ids = list(set(all_ids) - set(input_ids))

                add_ids = input_ids

            if add_ids:
                self._add_related(
                    facade,
                    instance, relation,
                    add_ids,
                    use_key,
                    command
                )
            if remove_ids:
                self._remove_related(
                    facade,
                    instance, relation,
                    remove_ids,
                    use_key,
                    command
                )

    def _add_related(self, facade, instance, relation, ids, use_key, command):
        queryset = get_queryset(instance, relation)
        instance_name = type(instance).__name__.lower()
        auto_create = facade.check_auto_create()

        if queryset:
            for id in ids:
                if use_key:
                    # [provider:]id
                    id_components = id.split(':')
                    provider_type = id_components[0] if len(id_components) > 1 else 'base'
                    id = id_components[1] if len(id_components) > 1 else id_components[0]

                    sub_instance = facade.retrieve(id)

                    if command and auto_create and not sub_instance:
                        if getattr(facade, 'provider_name', None):
                            provider = command.get_provider(facade.provider_name, provider_type)
                            sub_instance = provider.create(id)
                        else:
                            sub_instance, created = facade.store(id)
                else:
                    sub_instance = facade.retrieve_by_id(id)

                if sub_instance:
                    try:
                        queryset.add(sub_instance)
                    except Exception as e:
                        raise UpdateError("{} add failed: {}".format(facade.name.title(), str(e)))
                elif command and auto_create:
                    raise UpdateError("{} '{}' creation failed for attachment to {} '{}'".format(facade.name.title(), id, instance.facade.name, str(instance)))
                else:
                    raise UpdateError("{} '{}' does not exist for attachment to {} '{}'".format(facade.name.title(), id, instance.facade.name, str(instance)))
        else:
            raise UpdateError("There is no relation {} on {} class".format(relation, instance_name))

    def _remove_related(self, facade, instance, relation, ids, use_key, command):
        queryset = get_queryset(instance, relation)
        instance_name = type(instance).__name__.lower()

        if use_key:
            key = getattr(instance, instance.facade.key())
            keep_index = instance.facade.keep_relations().get(relation, {})
            keep = ensure_list(keep_index.get(key, []))

        if queryset:
            for id in ids:
                if not use_key or id not in keep:
                    if use_key:
                        # [provider:]id
                        id_components = id.split(':')
                        id = id_components[1] if len(id_components) > 1 else id_components[0]
                        sub_instance = facade.retrieve(id)
                    else:
                        sub_instance = facade.retrieve_by_id(id)

                    if sub_instance:
                        try:
                            queryset.remove(sub_instance)
                        except Exception as e:
                            raise UpdateError("{} remove failed: {}".format(facade.name.title(), str(e)))
                elif use_key:
                    raise UpdateError("{} '{}' removal from {} is restricted".format(facade.name.title(), id, key))
        else:
            raise UpdateError("There is no relation {} on {} class".format(relation, instance_name))

    def _set_related(self, facade, instance, relation, id, use_key, command):
        if id is None:
            setattr(instance, relation, None)
        else:
            if isinstance(id, str):
                auto_create = facade.check_auto_create()

                if re.match(r'(none|null)', id, re.IGNORECASE):
                    setattr(instance, relation, None)
                else:
                    if use_key:
                        # [provider:]id
                        id_components = id.split(':')
                        provider_type = id_components[0] if len(id_components) > 1 else 'base'
                        id = id_components[1] if len(id_components) > 1 else id_components[0]

                        sub_instance = facade.retrieve(id)

                        if command and auto_create and not sub_instance:
                            if getattr(facade, 'provider_name', None):
                                provider = command.get_provider(facade.provider_name, provider_type)
                                sub_instance = provider.create(id)
                            else:
                                sub_instance, created = facade.store(id)
                    else:
                        sub_instance = facade.retrieve_by_id(id)

                    if sub_instance:
                        setattr(instance, relation, sub_instance)
                    elif command and auto_create:
                        raise UpdateError("{} '{}' creation failed for attachment to {} '{}'".format(facade.name.title(), id, instance.facade.name, str(instance)))
                    else:
                        raise UpdateError("{} '{}' does not exist for attachment to {} '{}'".format(facade.name.title(), id, instance.facade.name, str(instance)))
            else:
                setattr(instance, relation, id)


    def delete(self, key, **filters):
        if key not in ensure_list(self.keep(key)):
            filters[self.key()] = key
            return self.clear(**filters)
        else:
            raise RestrictedError("Removal of {} {} is restricted".format(self.model.__name__.lower(), key))

    def clear(self, **filters):
        queryset  = self.filter(**filters)
        keep_list = self.keep()
        if keep_list:
            queryset = queryset.exclude(**{
                "{}__in".format(self.key()): ensure_list(keep_list)
            })

        deleted, del_per_type = queryset.delete()
        if deleted:
            return True
        return False
