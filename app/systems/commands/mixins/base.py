from systems.commands import args
from utility import text, data
from .meta import MetaBaseMixin


class BaseMixin(object, metaclass = MetaBaseMixin):

    @classmethod
    def generate(cls, command, generator):
        # Override in subclass if needed
        pass


    def parse_flag(self, name, flag, help_text, tags = None):
        with self.option_lock:
            if name not in self.option_map:
                flag_default = self.options.get_default(name)

                if flag_default:
                    option_label = self.success_color("option_{}".format(name))
                    help_text = "{} <{}>".format(help_text, self.value_color('True'))
                else:
                    option_label = self.key_color("option_{}".format(name))

                self.add_schema_field(name,
                    args.parse_bool(
                        self.parser,
                        name,
                        flag,
                        "[@{}] {}".format(option_label, help_text),
                        default = flag_default
                    ),
                    optional = True,
                    tags = tags
                )
                if flag_default is not None:
                    self.option_defaults[name] = flag_default

                self.option_map[name] = True

    def parse_variable(self, name, optional, type, help_text, value_label = None, default = None, choices = None, tags = None):
        with self.option_lock:
            if name not in self.option_map:
                variable_default = None

                if optional:
                    variable_default = self.options.get_default(name)
                    if variable_default is not None:
                        option_label = self.success_color("option_{}".format(name))
                    else:
                        option_label = self.key_color("option_{}".format(name))
                        variable_default = default

                    if variable_default is None:
                        default_label = ''
                    else:
                        default_label = " <{}>".format(self.value_color(variable_default))

                    help_text = "[@{}] {}{}".format(option_label, help_text, default_label)

                if optional and isinstance(optional, (str, list, tuple)):
                    if not value_label:
                        value_label = name

                    self.add_schema_field(name,
                        args.parse_option(self.parser, name, optional, type, help_text,
                            value_label = value_label.upper(),
                            default = variable_default,
                            choices = choices
                        ),
                        optional = True,
                        tags = tags
                    )
                else:
                    self.add_schema_field(name,
                        args.parse_var(self.parser, name, type, help_text,
                            optional = optional,
                            default = variable_default,
                            choices = choices
                        ),
                        optional = optional,
                        tags = tags
                    )
                if variable_default is not None:
                    self.option_defaults[name] = variable_default

                self.option_map[name] = True

    def parse_variables(self, name, optional, type, help_text, value_label = None, default = None, tags = None):
        with self.option_lock:
            if name not in self.option_map:
                variable_default = None

                if optional:
                    variable_default = self.options.get_default(name)
                    if variable_default is not None:
                        option_label = self.success_color("option_{}".format(name))
                    else:
                        option_label = self.key_color("option_{}".format(name))
                        variable_default = default

                    if variable_default is None:
                        default_label = ''
                    else:
                        default_label = " <{}>".format(self.value_color(", ".join(data.ensure_list(variable_default))))

                    help_text = "[@{}] {}{}".format(option_label, help_text, default_label)

                if optional and isinstance(optional, (str, list, tuple)):
                    help_text = "{} (comma separated)".format(help_text)

                    if not value_label:
                        value_label = name

                    self.add_schema_field(name,
                        args.parse_csv_option(self.parser, name, optional, type, help_text,
                            value_label = value_label.upper(),
                            default = variable_default
                        ),
                        optional = True,
                        tags = tags
                    )
                else:
                    self.add_schema_field(name,
                        args.parse_vars(self.parser, name, type, help_text,
                            optional = optional,
                            default = variable_default
                        ),
                        optional = optional,
                        tags = tags
                    )
                if variable_default is not None:
                    self.option_defaults[name] = variable_default

                self.option_map[name] = True

    def parse_fields(self, facade, name, optional = False, help_callback = None, callback_args = None, callback_options = None, exclude_fields = None, tags = None):
        with self.option_lock:
            if not callback_args:
                callback_args = []
            if not callback_options:
                callback_options = {}

            if exclude_fields:
                exclude_fields = data.ensure_list(exclude_fields)
                callback_options['exclude_fields'] = exclude_fields

            if name not in self.option_map:
                if facade:
                    help_text = "\n".join(self.field_help(facade, exclude_fields))
                else:
                    help_text = "\nfields as key value pairs\n"

                if help_callback and callable(help_callback):
                    help_text += "\n".join(help_callback(*callback_args, **callback_options))

                self.add_schema_field(name,
                    args.parse_key_values(self.parser, name, help_text,
                        value_label = 'field=VALUE',
                        optional = optional
                    ),
                    optional = optional,
                    tags = tags
                )
                self.option_map[name] = True


    def parse_test(self):
        self.parse_flag('test', '--test', 'test execution without permanent changes', tags = ['system'])

    @property
    def test(self):
        return self.options.get('test', False)


    def parse_force(self):
        self.parse_flag('force', '--force', 'force execution even with provider errors', tags = ['system'])

    @property
    def force(self):
        return self.options.get('force', False)


    def parse_count(self):
        self.parse_variable('count',
            '--count', int,
            'instance count (default 1)',
            value_label = 'COUNT',
            default = 1,
            tags = ['list', 'limit']
        )

    @property
    def count(self):
        return self.options.get('count', 1)


    def parse_clear(self):
        self.parse_flag('clear', '--clear', 'clear all items', tags = ['system'])

    @property
    def clear(self):
        return self.options.get('clear', False)


    def parse_search(self, optional = True, help_text = 'one or more search queries'):
        self.parse_variables('instance_search_query', optional, str, help_text,
            value_label = 'REFERENCE',
            tags = ['search']
        )
        self.parse_flag('instance_search_or', '--or', 'perform an OR query on input filters', tags = ['search'])

    @property
    def search_queries(self):
        return self.options.get('instance_search_query', [])

    @property
    def search_join(self):
        join_or = self.options.get('instance_search_or', False)
        return 'OR' if join_or else 'AND'


    def field_help(self, facade, exclude_fields = None):
        field_index = facade.field_index
        system_fields = [ x.name for x in facade.system_field_instances ]

        if facade.name == 'user':
            system_fields.extend(['last_login', 'password']) # User abstract model exceptions

        lines = [ "fields as key value pairs", '' ]

        lines.append("-" * 40)
        lines.append('model requirements:')
        for name in facade.required_fields:
            if exclude_fields and name in exclude_fields:
                continue

            if name not in system_fields:
                field = field_index[name]
                field_label = type(field).__name__.replace('Field', '').lower()
                if field_label == 'char':
                    field_label = 'string'

                choices = []
                if field.choices:
                    choices = [ self.value_color(x[0]) for x in field.choices ]

                lines.append("    {} {}{}".format(
                    self.warning_color(field.name),
                    field_label,
                    ':> ' + ", ".join(choices) if choices else ''
                ))
                if field.help_text:
                    lines.extend(('',
                        "       - {}".format(
                            "\n".join(text.wrap(field.help_text, 40,
                                indent = "         "
                            ))
                        ),
                    ))
        lines.append('')

        lines.append('model options:')
        for name in facade.optional_fields:
            if exclude_fields and name in exclude_fields:
                continue

            if name not in system_fields:
                field = field_index[name]
                field_label = type(field).__name__.replace('Field', '').lower()
                if field_label == 'char':
                    field_label = 'string'

                choices = []
                if field.choices:
                    choices = [ self.value_color(x[0]) for x in field.choices ]

                default = facade.get_field_default(field)

                if default is not None:
                    lines.append("    {} {} ({}){}".format(
                        self.warning_color(field.name),
                        field_label,
                        self.value_color(default),
                        ':> ' + ", ".join(choices) if choices else ''
                    ))
                else:
                    lines.append("    {} {} {}".format(
                        self.warning_color(field.name),
                        field_label,
                        ':> ' + ", ".join(choices) if choices else ''
                    ))

                if field.help_text:
                    lines.extend(('',
                        "       - {}".format(
                            "\n".join(text.wrap(field.help_text, 40,
                                indent = "         "
                            ))
                        ),
                    ))
        lines.append('')
        return lines
