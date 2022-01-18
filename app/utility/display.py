from contextlib import contextmanager
from terminaltables import AsciiTable

from django.conf import settings

from .runtime import Runtime
from .text import wrap
from .terminal import colorize_data

import os
import sys
import traceback
import re
import logging


logger = logging.getLogger(__name__)


def format_table(data, prefix = None):
    data = colorize_data(data)
    table_rows = AsciiTable(data).table.splitlines()
    prefixed_rows = []

    if prefix:
        for row in table_rows:
            prefixed_rows.append("{}{}".format(prefix, row))
    else:
        prefixed_rows = table_rows

    return ("\n".join(prefixed_rows), len(table_rows[0]))


def format_list(data, prefix = None, row_labels = False, width = None):
    if width is None:
        width = Runtime.width()

    data = colorize_data(data)
    prefixed_text = [
        "=" * width
    ]

    if not row_labels:
        labels = list(data[0])
        values = data[1:]
    else:
        values = data

    def format_item(item):
        text = []

        if row_labels:
            values = item[1:]
            if len(values) > 0 and "\n" in values[0]:
                values[0] = "\n{}".format(values[0])

            text.append(" * {}: {}".format(
                item[0].replace("\n", ' '),
                "\n".join(values)
            ))
        else:
            text.append("-" * width)
            for index, label in enumerate(labels):
                value = str(item[index]).strip()
                if "\n" in value:
                    value = "\n{}".format(value)

                text.append(" * {}: {}".format(
                    label.replace("\n", ' '),
                    value
                ))
        return text

    for item in values:
        text = format_item(item)
        if text:
            prefixed_text.extend(text)

    return "\n".join(prefixed_text)


def format_data(data, prefix = None, row_labels = False, width = None):
    if width is None:
        width = Runtime.width()

    data = colorize_data(data)
    table_text, table_width = format_table(data, prefix)
    if table_width <= width:
        return "\n" + table_text
    else:
        return "\n" + format_list(data, prefix, row_labels = row_labels, width = width)


def format_exception_info():
    exc_type, exc_value, exc_tb = sys.exc_info()
    return traceback.format_exception(exc_type, exc_value, exc_tb)

def print_exception_info(debug = False):
    if Runtime.debug() or debug:
        sys.stderr.write('\n'.join([ item.strip() for item in format_exception_info() ]) + '\n')

def format_traceback():
    return traceback.format_stack()[:-2]

def print_traceback(debug = False):
    if Runtime.debug() or debug:
        sys.stderr.write('\n'.join([ item.strip() for item in format_traceback() ]) + '\n')


@contextmanager
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout


def display_class_info(klass, prefix = '', display_function = logger.info):
    display_function("{}{}".format(prefix, klass.__name__))
    for parent in klass.__bases__:
        display_class_info(parent, "{}  << ".format(prefix), display_function)

    display_function("{} properties:".format(prefix))
    for attribute in dir(klass):
        if not attribute.startswith('__') and not callable(getattr(klass, attribute)):
            display_function("{}  ->  {}".format(prefix, attribute))

    display_function("{} methods:".format(prefix))
    for attribute in dir(klass):
        if not attribute.startswith('__') and callable(getattr(klass, attribute)):
            display_function("{}  **  {}".format(prefix, attribute))
