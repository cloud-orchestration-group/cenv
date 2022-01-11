from ctypes import c_bool
from django.conf import settings
from django.core.management.base import CommandError

from systems.commands.index import CommandMixin
from systems.commands.mixins import exec
from systems.commands import base, messages
from utility import display

import multiprocessing
import re
import logging
import copy
import yaml
import getpass
import zimagi


logger = logging.getLogger(__name__)


class ActionCommand(
    exec.ExecMixin,
    CommandMixin('log'),
    CommandMixin('schedule'),
    CommandMixin('notification'),
    base.BaseCommand
):
    @classmethod
    def generate(cls, command, generator):
        # Override in subclass if needed
        pass


    def __init__(self, name, parent = None):
        super().__init__(name, parent)

        self.disconnected = multiprocessing.Value(c_bool, False)
        self.log_result = True
        self.notification_messages = []

        self.action_result = self.get_action_result()


    def queue(self, msg):
        data = super().queue(msg)
        if self.log_result:
            self.log_message(data)

        self.notification_messages.append(
            self.raw_text(msg.format(disable_color = True))
        )
        self.action_result.add(msg)
        return data


    def get_action_result(self):
        return zimagi.command.CommandResponse()

    def display_header(self):
        return True


    def parse_base(self, addons = None):

        def action_addons():
            # Operations
            self.parse_push_queue()

            if not settings.API_EXEC:
                # Operations
                self.parse_local()
                self.parse_reverse_status()

            # Locking
            self.parse_lock_id()
            self.parse_lock_error()
            self.parse_lock_timeout()
            self.parse_lock_interval()

            if self.server_enabled():
                # Scheduling
                self.parse_schedule()
                self.parse_schedule_begin()
                self.parse_schedule_end()

                # Notifications
                self.parse_command_notify()
                self.parse_command_notify_failure()

            if addons and callable(addons):
                addons()

        super().parse_base(action_addons)

    def parse_push_queue(self):
        self.parse_flag('push_queue', '--queue', "run command in the background instead of executing immediately", tags = ['system'])

    @property
    def push_queue(self):
        return self.options.get('push_queue', False)


    def parse_local(self):
        self.parse_flag('local', '--local', "force command to run in local environment", tags = ['system'])

    @property
    def local(self):
        return self.options.get('local', False)

    def parse_reverse_status(self):
        self.parse_flag('reverse_status', '--reverse-status', "reverse exit status of command (error on success)", tags = ['system'])

    @property
    def reverse_status(self):
        return self.options.get('reverse_status', False)


    def parse_lock_id(self):
        self.parse_variable('lock_id', '--lock', str,
            'command lock id to prevent simultanious duplicate execution',
            value_label = 'UNIQUE_NAME',
            tags = ['lock']
        )

    @property
    def lock_id(self):
        return self.options.get('lock_id', None)

    def parse_lock_error(self):
        self.parse_flag('lock_error', '--lock-error', 'raise an error and abort if commmand lock can not be established', tags = ['lock'])

    @property
    def lock_error(self):
        return self.options.get('lock_error', False)

    def parse_lock_timeout(self):
        self.parse_variable('lock_timeout', '--lock-timeout', int,
            'command lock wait timeout in seconds',
            value_label = 'SECONDS',
            default = 600,
            tags = ['lock']
        )

    @property
    def lock_timeout(self):
        return self.options.get('lock_timeout', 600)

    def parse_lock_interval(self):
        self.parse_variable('lock_interval', '--lock-interval', int,
            'command lock check interval in seconds',
            value_label = 'SECONDS',
            default = 2,
            tags = ['lock']
        )

    @property
    def lock_interval(self):
        return self.options.get('lock_interval', 2)


    def confirm(self):
        # Override in subclass
        pass

    def prompt(self):

        def _standard_prompt(parent, split = False):
            try:
                self.info('-' * self.display_width)
                value = input("Enter {}{}: ".format(parent, " (csv)" if split else ""))
                if split:
                    value = re.split('\s*,\s*', value)
            except Exception as error:
                self.error("User aborted", 'abort')

            return value

        def _hidden_verify_prompt(parent, split = False):
            try:
                self.info('-' * self.display_width)
                value1 = getpass.getpass(prompt = "Enter {}{}: ".format(parent, " (csv)" if split else ""))
                value2 = getpass.getpass(prompt = "Re-enter {}{}: ".format(parent, " (csv)" if split else ""))
            except Exception as error:
                self.error("User aborted", 'abort')

            if value1 != value2:
                self.error("Prompted {} values do not match".format(parent))

            if split:
                value1 = re.split('\s*,\s*', value1)

            return value1


        def _option_prompt(parent, option, top_level = False):
            any_override = False

            if isinstance(option, dict):
                for name, value in option.items():
                    override, value = _option_prompt(parent + [ str(name) ], value)
                    if override:
                        option[name] = value
                        any_override = True

            elif isinstance(option, (list, tuple)):
                process_list = True

                if len(option) == 1:
                    override, value = _option_prompt(parent, option[0])
                    if isinstance(option[0],  str) and option[0] != value:
                        option.extend(re.split('\s*,\s*', value))
                        option.pop(0)
                        process_list = False
                        any_override = True

                if process_list:
                    for index, value in enumerate(option):
                        override, value = _option_prompt(parent + [ str(index) ], value)
                        if override:
                            option[index] = value
                            any_override = True

            elif isinstance(option, str):
                parent = " ".join(parent).replace("_", " ")

                if option == '+prompt+':
                    option = _standard_prompt(parent)
                    any_override = True
                elif option == '++prompt++':
                    option = _standard_prompt(parent, True)
                    any_override = True
                elif option == '+private+':
                    option = _hidden_verify_prompt(parent)
                    any_override = True
                elif option == '++private++':
                    option = _hidden_verify_prompt(parent, True)
                    any_override = True

            return any_override, option


        for name, value in self.options.export().items():
            override, value = _option_prompt([ name ], value, True)
            if override:
                self.options.add(name, value)


    def exec(self):
        # Override in subclass
        pass

    def exec_local(self, name, options = None, task = None):
        if not options:
            options = {}

        command = self.manager.index.find_command(name, self)
        command.mute = self.mute

        options = command.format_fields(
            copy.deepcopy(options)
        )
        options.setdefault('debug', self.debug)
        options.setdefault('no_parallel', self.no_parallel)
        options.setdefault('no_color', self.no_color)
        options.setdefault('display_width', self.display_width)
        options['local'] = not self.server_enabled() or self.local

        log_key = options.pop('_log_key', None)

        command.set_options(options)
        command.handle(options,
            task = task,
            log_key = log_key
        )

    def exec_remote(self, host, name, options = None, display = True):
        if not options:
            options = {}

        command = self.manager.index.find_command(name, self)
        command.mute = self.mute
        success = True

        options = {
            key: options[key] for key in options if key not in (
                'no_color',
                'environment_host',
                'local',
                'version',
                'reverse_status'
            )
        }
        options['environment_host'] = self.environment_host
        options.setdefault('debug', self.debug)
        options.setdefault('no_parallel', self.no_parallel)
        options.setdefault('display_width', self.display_width)

        command.set_options(options)
        command.log_init(options)

        def message_callback(message):
            message = self.create_message(message.render(), decrypt = False)

            if (display and self.verbosity > 0) or isinstance(message, messages.ErrorMessage):
                message.display(
                    debug = self.debug,
                    disable_color = self.no_color,
                    width = self.display_width
                )
            command.queue(message)

        try:
            api = host.api(
                options_callback = command.preprocess_handler,
                message_callback = message_callback
            )
            response = api.execute(name, **options)
            command.postprocess_handler(response)

            if response.aborted:
                success = False
                raise CommandError()
        finally:
            if command.log_result:
                command.log_status(success)

        return response


    def preprocess(self, options):
        # Override in subclass
        pass

    def preprocess_handler(self, options, primary = False):
        self.start_profiler('preprocess', primary)
        self.preprocess(options)
        self.stop_profiler('preprocess', primary)

    def postprocess(self, response):
        # Override in subclass
        pass

    def postprocess_handler(self, response, primary = False):
        if not response.aborted:
            self.start_profiler('postprocess', primary)
            self.postprocess(response)
            self.stop_profiler('postprocess', primary)


    def handle(self, options, primary = False, task = None, log_key = None):

        def _process(_options, _primary, _task, _log_key):
            width = self.display_width
            env = self.get_env()
            host = self.get_host()
            success = True

            if _primary and settings.CLI_EXEC:
                self.info("-" * width)

            _log_key = self.log_init(self.options.export(),
                task = _task,
                log_key = _log_key
            )
            try:
                if not self.local and host and \
                    (settings.CLI_EXEC or host.name != settings.DEFAULT_HOST_NAME) and \
                    self.server_enabled() and self.remote_exec():

                    if _primary and self.display_header() and self.verbosity > 1:
                        self.data("> env ({})".format(
                                self.key_color(host.host)
                            ),
                            env.name,
                            'environment'
                        )

                    if _primary:
                        self.prompt()
                        self.confirm()

                    self.exec_remote(host, self.get_full_name(), _options, display = True)
                else:
                    if not self.check_execute():
                        self.error("User {} does not have permission to execute command: {}".format(self.active_user.name, self.get_full_name()))

                    if _primary and self.display_header() and self.verbosity > 1:
                        self.data('> env',
                            env.name,
                            'environment'
                        )

                    if _primary and settings.CLI_EXEC:
                        self.prompt()
                        self.confirm()

                        self.info("=" * width)
                        self.data("> {}".format(self.key_color(self.get_full_name())), _log_key, 'log_key')
                        self.info("-" * width)
                    try:
                        self.preprocess_handler(self.options, _primary)
                        if not self.set_periodic_task() and not self.set_queue_task(_log_key):
                            self.start_profiler('exec', _primary)
                            self.run_exclusive(self.lock_id, self.exec,
                                error_on_locked = self.lock_error,
                                timeout = self.lock_timeout,
                                interval = self.lock_interval
                            )
                            self.stop_profiler('exec', _primary)

                    except Exception as e:
                        success = False
                        raise e
                    finally:
                        self.postprocess_handler(self.action_result, _primary)

                        if self.log_result:
                            self.log_status(success)

                            if _primary:
                                self.send_notifications(success)

            except Exception as e:
                if not self.reverse_status:
                    raise e
                self.flush()
                return

            if self.reverse_status:
                self.error('Reverse status error')

        if primary or self.no_parallel:
            _process(options, primary, task, log_key)
        else:
            process = multiprocessing.Process(target = _process, args = (options, primary, task, log_key))
            process.start()
            process.join()


    def _exec_wrapper(self, options):
        try:
            width = self.display_width
            log_key = self.log_init(options)
            success = True

            if self.display_header() and self.verbosity > 1:
                self.info("=" * width)
                self.data("> {}".format(self.get_full_name()), log_key, 'log_key')
                self.data("> active user", self.active_user.name, 'active_user')
                self.info("-" * width)

            if not self.set_periodic_task() and not self.set_queue_task(log_key):
                self.run_exclusive(self.lock_id, self.exec,
                    error_on_locked = self.lock_error,
                    timeout = self.lock_timeout,
                    interval = self.lock_interval
                )

        except Exception as e:
            success = False

            if not isinstance(e, CommandError):
                self.error(e,
                    terminate = False,
                    traceback = display.format_exception_info()
                )
        finally:
            try:
                if self.log_result:
                    self.log_status(success)
                    self.send_notifications(success)

            except Exception as e:
                self.error(e,
                    terminate = False,
                    traceback = display.format_exception_info()
                )

            finally:
                self.flush()


    def handle_api(self, options):
        logger.debug("Running API command: {}\n\n{}".format(self.get_full_name(), yaml.dump(options)))

        action = multiprocessing.Process(target = self._exec_wrapper, args = (options,))
        action.start()

        logger.debug("Command thread started: {}".format(self.get_full_name()))

        try:
            while True:
                self.sleep(0.25)
                logger.debug("Checking messages")

                for data in iter(self.messages.get, None):
                    logger.debug("Receiving data: {}".format(data))

                    msg = self.create_message(data, decrypt = False)
                    package = msg.to_package()
                    yield package

                if not action.is_alive():
                    logger.debug("Command thread is no longer active")
                    break
        except Exception as e:
            logger.warning("Command transport exception: {}".format(e))
            raise e
        finally:
            logger.debug("User disconnected")
            self.disconnected = True
