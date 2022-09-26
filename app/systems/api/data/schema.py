from functools import lru_cache

from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import exceptions
from rest_framework.schemas.openapi import SchemaGenerator, AutoSchema

from .filter.backends import RelatedFilterBackend

import re


def get_csv_response_schema(description):
    return {
        '200': {
            'content': {
                'text/csv': {
                    'schema': {}
                }
            },
            'description': description
        }
    }


class DataSchemaGenerator(SchemaGenerator):

    def has_view_permissions(self, path, method, view):
        if view.request is None:
            return True
        try:
            view.check_permissions(view.request)
        except (exceptions.APIException, Http404, PermissionDenied):
            return False
        return True


class StatusSchema(AutoSchema):

    def get_operation_id_base(self, path, method, action):
        return 'SystemStatus'

    def get_responses(self, path, method):
        return {
            '200': {
                'content': {
                    'application/json': {
                        'schema': {}
                    }
                },
                'description': 'Status information'
            }
        }


class DataSetSchema(AutoSchema):

    def get_operation_id_base(self, path, method, action):
        return 'DataSetCSV'

    def get_responses(self, path, method):
        return get_csv_response_schema('CSV download of dataset data')


class DataSchema(AutoSchema):

    def allows_filters(self, path, method):
        if getattr(self.view, 'filter_backends', None) is None:
            return False

        if hasattr(self.view, 'action'):
            return self.view.action in [
                "list",
                "values",
                "count",
                "csv",
                "json",
                "retrieve",
                "create",
                "update",
                "destroy"
            ]
        return method.lower() in ["get", "put", "delete"]


    def get_component_name(self, serializer):
        if self.component_name is not None:
            return self.component_name

        component_name = serializer.__class__.__name__.replace('_', '')
        pattern = re.compile("serializer", re.IGNORECASE)
        component_name = pattern.sub("", component_name)

        if component_name == "":
            raise Exception(
                '"{}" is an invalid class name for schema generation. '
                'Serializer\'s class name should be unique and explicit. e.g. "ItemSerializer"'
                .format(serializer.__class__.__name__)
            )

        return component_name


    @lru_cache(maxsize = None)
    def get_filter_parameters(self, path, method):
        if not self.allows_filters(path, method):
            return []

        def check_filter_overlap(data_types):
            if len(data_types) <= 2:
                return False
            if len(data_types) != len(set(data_types)):
                return True
            return False

        def load_parameters(view, name_prefix = '', depth = 1, data_types = None):
            relations = view.facade.get_all_relations()
            parameters = []
            id_map = {}

            for filter_backend in view.get_filter_classes():
                if depth == 1 or filter_backend == RelatedFilterBackend:
                    for parameter in filter_backend().get_schema_operation_parameters(view):
                        field_name = parameter['name']

                        if field_name not in id_map:
                            nested_name = "{}__{}".format(name_prefix, field_name) if name_prefix else field_name
                            base_name = parameter['schema']['x-base-field'] if 'x-base-field' in parameter['schema'] else field_name

                            if field_name in relations:
                                related_view = relations[field_name]['model'].facade.get_viewset()(
                                    action = self.view.action
                                )
                                if not check_filter_overlap([ *data_types, related_view.facade.name ]):
                                    parameters.extend(load_parameters(
                                        related_view,
                                        nested_name,
                                        depth = (depth + 1),
                                        data_types = [ *data_types, related_view.facade.name ]
                                    ))
                            elif field_name == base_name or base_name in relations:
                                add_filter = True

                                if base_name in relations:
                                    related_view = relations[base_name]['model'].facade.get_viewset()(
                                        action = self.view.action
                                    )
                                    if check_filter_overlap([ *data_types, related_view.facade.name ]):
                                        add_filter = False

                                if add_filter:
                                    parameter['name'] = nested_name

                                    if 'x-field' in parameter['schema']:
                                        parameter['schema']['x-field'] = "{}{}".format(
                                            "{}__".format(name_prefix) if name_prefix else '',
                                            parameter['schema']['x-field']
                                        )
                                        if name_prefix:
                                            parameter['schema']['x-relation'] = name_prefix

                                    parameters.append(parameter)

                            id_map[field_name] = True
            return parameters

        return load_parameters(self.view, data_types = [ self.view.facade.name ])


    @lru_cache(maxsize = None)
    def get_responses(self, path, method):
        if self.view.action == 'csv':
            return get_csv_response_schema('CSV download of field data')
        else:
            responses = super().get_responses(path, method)

            if self.view.action in ('json',):
                for status_code, response in responses.items():
                    for format, info in response['content'].items():
                        response['content'][format]['schema'] = {
                            'type': 'array',
                            'items': {}
                        }
            return responses
