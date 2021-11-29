from systems.plugins.index import BaseProvider

import datetime


class Provider(BaseProvider('validator', 'date_time')):

    def validate(self, value, record):
        if isinstance(value, float):
            value = int(value)
        try:
            datetime.datetime.strptime(str(value), self.field_format)
        except ValueError as e:
            self.warning("Value {} is not a valid date time according to pattern: {}".format(value, self.field_format))
            return False
        return True
