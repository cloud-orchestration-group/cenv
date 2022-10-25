from .filter.related import RelatedFilterSet, RelatedFilterSetMetaclass
from .filter.filters import (
    BooleanFilter,
    NumberFilter,
    CharFilter,
    DateSearchFilter,
    DateFilter,
    DateTimeSearchFilter,
    DateTimeFilter,
    RelatedFilter,
    BaseInFilter,
    BaseRangeFilter,
    JSONFilter
)


FILTER_TYPES = ('bool', 'number', 'text', 'date', 'time')


class CharInFilter(BaseInFilter, CharFilter):
    pass

class CharRangeFilter(BaseRangeFilter, CharFilter):
    pass

class NumberInFilter(BaseInFilter, NumberFilter):
    pass

class NumberRangeFilter(BaseRangeFilter, NumberFilter):
    pass

class DateInFilter(BaseInFilter, DateFilter):
    pass

class DateRangeFilter(BaseRangeFilter, DateFilter):
    pass

class DateTimeInFilter(BaseInFilter, DateTimeFilter):
    pass

class DateTimeRangeFilter(BaseRangeFilter, DateTimeFilter):
    pass

class DataRelatedFilter(RelatedFilter):

    def get_queryset(self, request):
        return self.filterset._meta.model.objects.all()


class MetaFilterSet(RelatedFilterSetMetaclass):

    def __new__(cls, name, bases, attr):
        facade = attr.get('facade', None)
        related_fields = attr.get('related_fields', None)

        def _generate_filters(id):
            if id in attr and attr[id]:
                for field_name in list(attr[id]):
                    getattr(cls, "{}_filters".format(id))(field_name, attr, facade)

            if id in attr.keys():
                attr.pop(id)

        _generate_filters('_boolean_fields')
        _generate_filters('_text_fields')
        _generate_filters('_number_fields')
        _generate_filters('_date_fields')
        _generate_filters('_time_fields')
        _generate_filters('_list_fields')
        _generate_filters('_dictionary_fields')

        if related_fields:
            cls._generate_aggregator_fields(related_fields, attr, facade)

        return super().__new__(cls, name, bases, attr)


    @classmethod
    def _get_text_lookups(self):
        return ['iexact', 'contains', 'icontains', 'startswith', 'istartswith', 'endswith', 'iendswith', 'regex', 'iregex']

    @classmethod
    def _get_number_lookups(self):
        return ['lt', 'lte', 'gt', 'gte']

    @classmethod
    def _get_date_lookups(self):
        return ['year', 'month', 'day', 'week', 'week_day', 'quarter']

    @classmethod
    def _get_time_lookups(self):
        return self._get_date_lookups() + ['hour', 'minute', 'second']


    @classmethod
    def _boolean_fields_filters(cls, field_name, filters, facade):
        filters[field_name] = BooleanFilter(field_name = field_name, lookup_expr = 'exact', label = 'bool')
        filters["{}__isnull".format(field_name)] = BooleanFilter(field_name = field_name, lookup_expr = 'isnull', label = 'bool')


    @classmethod
    def _text_fields_filters(cls, field_name, filters, facade):
        filters[field_name] = CharFilter(field_name = field_name, lookup_expr = 'exact', label = 'string')
        filters["{}__isnull".format(field_name)] = BooleanFilter(field_name = field_name, lookup_expr = 'isnull', label = 'bool')
        filters["{}__in".format(field_name)] = CharInFilter(field_name = field_name, label = 'csv<string>')

        for lookup in cls._get_text_lookups():
            filters['{}__{}'.format(field_name, lookup)] = CharFilter(field_name = field_name, lookup_expr = lookup, label = 'string')


    @classmethod
    def _number_fields_filters(cls, field_name, filters, facade):
        filters[field_name] = NumberFilter(field_name = field_name, lookup_expr = 'exact', label = 'number')
        filters["{}__isnull".format(field_name)] = BooleanFilter(field_name = field_name, lookup_expr = 'isnull', label = 'bool')
        filters["{}__in".format(field_name)] = NumberInFilter(field_name = field_name, label = 'csv<number>')
        filters["{}__range".format(field_name)] = NumberRangeFilter(field_name = field_name, label = 'low<number>,high<number>')

        for lookup in cls._get_number_lookups():
            filters["{}__{}".format(field_name, lookup)] = NumberFilter(field_name = field_name, lookup_expr = lookup, label = 'number')


    @classmethod
    def _date_fields_filters(cls, field_name, filters, facade):
        filters[field_name] = DateSearchFilter(field_name = field_name, label = 'YYYY-MM-DD')
        filters["{}__isnull".format(field_name)] = BooleanFilter(field_name = field_name, lookup_expr = 'isnull', label = 'bool')
        filters["{}__in".format(field_name)] = DateInFilter(field_name = field_name, label = 'csv<YYYY-MM-DD>')
        filters["{}__range".format(field_name)] = DateRangeFilter(field_name = field_name, label = 'low<YYYY-MM-DD>,high<YYYY-MM-DD>')

        for lookup in cls._get_number_lookups():
            filters["{}__{}".format(field_name, lookup)] = DateFilter(field_name = field_name, lookup_expr = lookup, label = 'YYYY-MM-DD')

        for lookup in cls._get_date_lookups():
            filters["{}__{}".format(field_name, lookup)] = NumberFilter(field_name = field_name, lookup_expr = lookup, label = 'number')
            filters["{}__{}__in".format(field_name, lookup)] = NumberInFilter(field_name = field_name, label = 'csv<number>')
            filters["{}__{}__range".format(field_name, lookup)] = NumberRangeFilter(field_name = field_name, label = 'low<number>,high<number>')

            for sub_lookup in cls._get_number_lookups():
                full_lookup = "{}__{}".format(lookup, sub_lookup)
                filters["{}__{}".format(field_name, full_lookup)] = NumberFilter(field_name = field_name, lookup_expr = full_lookup, label = 'number')


    @classmethod
    def _time_fields_filters(cls, field_name, filters, facade):
        filters[field_name] = DateTimeSearchFilter(field_name = field_name, label = 'YYYY-MM-DDTHH:MM:SS')
        filters["{}__isnull".format(field_name)] = BooleanFilter(field_name = field_name, lookup_expr = 'isnull', label = 'bool')
        filters["{}__range".format(field_name)] = DateTimeRangeFilter(field_name = field_name, label = 'low<YYYY-MM-DDTHH:MM:SS>,high<YYYY-MM-DDTHH:MM:SS>')

        for lookup in cls._get_number_lookups():
            filters["{}__{}".format(field_name, lookup)] = DateTimeFilter(field_name = field_name, lookup_expr = lookup, label = 'YYYY-MM-DDTHH:MM:SS')

        for lookup in cls._get_time_lookups():
            filters["{}__{}".format(field_name, lookup)] = NumberFilter(field_name = field_name, lookup_expr = lookup, label = 'number')
            filters["{}__{}__in".format(field_name, lookup)] = NumberInFilter(field_name = field_name, label = 'csv<number>')
            filters["{}__{}__range".format(field_name, lookup)] = NumberRangeFilter(field_name = field_name, label = 'low<number>,high<number>')

            for sub_lookup in cls._get_number_lookups():
                full_lookup = "{}__{}".format(lookup, sub_lookup)
                filters["{}__{}".format(field_name, full_lookup)] = NumberFilter(field_name = field_name, lookup_expr = full_lookup, label = 'number')


    @classmethod
    def _generate_aggregator_fields(cls, fields, filters, facade):

        def _add_filters(field_name, aggregator_func):
            aggregator_field = "{}:{}".format(field_name, aggregator_func)

            filters[aggregator_field] = NumberFilter(field_name = aggregator_field, lookup_expr = 'exact', label = 'number')
            filters["{}__in".format(aggregator_field)] = NumberInFilter(field_name = aggregator_field, label = 'csv<number>')
            filters["{}__range".format(aggregator_field)] = NumberRangeFilter(field_name = aggregator_field, label = 'low<number>,high<number>')

            for lookup in cls._get_number_lookups():
                filters["{}__{}".format(aggregator_field, lookup)] = NumberFilter(field_name = aggregator_field, lookup_expr = lookup, label = 'number')

        for field, info in fields.items():
            related_facade = info['model'].facade

            for type in FILTER_TYPES:
                type_fields = getattr(related_facade, "{}_fields".format(type))

                if type_fields:
                    aggregators = related_facade.get_aggregators(type)

                    for field_name in type_fields:
                        for aggregator_func in aggregators:
                            _add_filters("{}__{}".format(field, field_name), aggregator_func)


    @classmethod
    def _list_fields_filters(cls, field_name, filters, facade):
        filters[field_name] = JSONFilter(field_name = field_name, label = '__json_lookup=[(]value[)]')


    @classmethod
    def _dictionary_fields_filters(cls, field_name, filters, facade):
        filters[field_name] = JSONFilter(field_name = field_name, label = '__json_lookup=[(]value[)]')


class BaseFilterSet(RelatedFilterSet, metaclass = MetaFilterSet):
    pass


def DataFilterSet(facade):
    class_name = "{}DataFilterSet".format(facade.name.title())

    if class_name in globals():
        return globals()[class_name]

    field_map = {
        'facade': facade,
        '_boolean_fields': facade.bool_fields,
        '_text_fields': facade.text_fields,
        '_number_fields': facade.number_fields,
        '_date_fields': facade.date_fields,
        '_time_fields': facade.time_fields,
        '_list_fields': facade.list_fields,
        '_dictionary_fields': facade.dictionary_fields,
        'Meta': type('Meta', (object,), {
            'model': facade.model,
            'fields': []
        })
    }
    related_fields = {}

    for field_name, info in facade.get_all_relations().items():
        if getattr(info['model'], 'facade', None):
            relation_facade = info['model'].facade

            field_map[field_name] = DataRelatedFilter(
                "systems.api.data.filters.{}DataFilterSet".format(relation_facade.name.title())
            )
            if info['multiple']:
                related_fields[field_name] = info

    field_map['related_fields'] = related_fields

    filterset = type(class_name, (BaseFilterSet,), field_map)
    globals()[class_name] = filterset
    return filterset
