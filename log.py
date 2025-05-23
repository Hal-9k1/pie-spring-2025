from abc import ABC
from abc import abstractmethod
from inspect import currentframe
from datetime import datetime
from ioutil import write_flexible_string
from sys import stderr
from sys import stdout

class Log:
    def __init__(self, severity, label, location, msg):
        self._severity = severity
        self._label = label
        self._location = location
        self._msg = msg

    def get_message(self):
        return self._msg

    def write_to(self, buffer):
        write_flexible_string(buffer, self._severity)
        write_flexible_string(buffer, self._label)
        write_flexible_string(buffer, self._location)
        write_flexible_string(buffer, self._msg)


class Logger:
    ERROR_SEVERITY = "ERROR"
    WARN_SEVERITY = "WARN"
    INFO_SEVERITY = "INFO"
    TRACE_SEVERITY = "TRACE"

    def __init__(self, label, backend, default_severity, default_severity_only, report_locations_filter,
        report_timestamps_filter):
        self._label = label
        self._backend = backend
        self._default_severity = default_severity
        self._default_severity_only = default_severity_only
        self._report_locations_filter = report_locations_filter
        self._report_timestamps_filter = report_timestamps_filter

    def error(self, *args):
        self._do_log(True, Logger.ERROR_SEVERITY, args)

    def warn(self, *args):
        self._do_log(True, Logger.WARN_SEVERITY, args)

    def info(self, *args):
        self._do_log(True, Logger.INFO_SEVERITY, args)

    def trace(self, *args):
        self._do_log(True, Logger.TRACE_SEVERITY, args)

    def log_severity(self, severity, *args):
        self._do_log(True, severity, args)

    def log(self, *args):
        self._do_log(False, self._default_severity, args)

    def position(self, item_label, position):
        self._backend.process_position(label, item_label, position)

    def vector(self, item_label, attach_label, vector):
        self._backend.process_vector(label, item_label, attach_label, vector)

    def transform(self, item_label, attach_label, transform):
        self._backend.process_transform(label, item_label, attach_label, transform)

    def update(self, item_label, value):
        self._backend.process_updatable_object(label, item_label, value)

    def _do_log(self, is_explicit_severity, severity, args):
        if is_explicit_severity and self._default_severity_only:
            raise RuntimeError("Attempt to log with explicit severity on logger configured to allow"
                + " default severity only")
        location = ""
        if self._report_locations_filter.permit(severity):
            frame = currentframe().f_back.f_back
            file = frame.f_code.co_filename
            num = frame.f_lineno
            try:
                file, num = _HELPER_translate_line_no(frame.f_lineno)
            except NameError:
                pass
            location = f" {file}:{num}"
        timestamp = ""
        if self._report_timestamps_filter.permit(timestamp):
            timestamp = datetime.now().strftime("%H:%M:%S.%f")
        msg = f"[{timestamp + ' ' if timestamp else ''}{severity} {self._label}{location}] {''.join(str(arg) for arg in args)}"
        self._backend.process_log(Log(severity, self._label, location, msg))


class LoggerBackend(ABC):
    @abstractmethod
    def process_position(self, logger_label, item_label, position):
        pass

    @abstractmethod
    def process_vector(self, logger_label, item_label, attach_label, vector):
        pass

    @abstractmethod
    def process_transform(self, logger_label, item_label, attach_label, transform):
        pass

    @abstractmethod
    def process_updatable_object(self, logger_label, item_label, value):
        pass

    @abstractmethod
    def process_log(self, log):
        pass


class StdioBackend(LoggerBackend):
    def process_position(self, logger_label, item_label, position):
        pass

    def process_vector(self, logger_label, item_label, attach_label, vector):
        pass

    def process_transform(self, logger_label, item_label, attach_label, transform):
        pass

    def process_updatable_object(self, logger_label, item_label, value):
        pass

    def process_log(self, log):
        if log._severity in (Logger.ERROR_SEVERITY, Logger.WARN_SEVERITY):
            f = stderr
        else:
            f = stdout
        print(log.get_message(), file=f)


class FilterBackend(LoggerBackend):
    def __init__(self, inner, default_setting):
        self._inner = inner
        self._exceptions = set()
        self._default_setting = default_setting
        self._filter = _SeverityFilter(default_setting, set())

    def add_exception(self, exception):
        self._exceptions.add(exception)
        self._filter = _SeverityFilter(self._default_setting, self._exceptions)
        return self

    def process_position(self, logger_label, item_label, position):
        self._inner.process_position(logger_label, item_label, position)

    def process_vector(self, logger_label, item_label, attach_label, vector):
        self._inner.process_vector(self, logger_label, item_label, attach_label, vector)

    def process_transform(self, logger_label, item_label, attach_label, transform):
        self._inner.process_transform(self, logger_label, item_label, attach_label, transform)

    def process_updatable_object(self, logger_label, item_label, value):
        self._inner.process_updatable_object(self, logger_label, item_label, value)

    def process_log(self, log):
        if self._filter.permit(log._severity):
            self._inner.process_log(log)


class LoggerProvider:
    def __init__(self):
        self._backends = []
        self._default_severity_name = Logger.INFO_SEVERITY
        self._default_severity_only = False
        self._use_timestamp = True
        self._timestamp_exceptions = set()
        self._use_location = False
        self._location_exceptions = set()

    def clone(self):
        copy = LoggerProvider()
        copy._backends = self._backends
        copy._default_severity_name = self._default_severity_name
        copy._default_severity_only = self._default_severity_only
        copy._use_timestamp = self._use_timestamp
        copy._timestamp_exceptions = self._timestamp_exceptions
        copy._use_location = self._use_location
        copy._location_exceptions = self._location_exceptions
        return copy

    def get_logger(self, label):
        backend = None
        if len(self._backends) == 0:
            backend = _NoopBackend()
        elif len(self._backends) == 1:
            backend = self._backends[0]
        else:
            backend = _AggregateBackend(self._backends.copy())
        return Logger(
            label,
            backend,
            self._default_severity_name,
            self._default_severity_only,
            _SeverityFilter(
                self._use_location,
                self._location_exceptions.copy()
            ),
            _SeverityFilter(
                self._use_timestamp,
                self._timestamp_exceptions.copy()
            )
        )

    def add_backend(self, backend):
        self._backends.append(backend)
        return self

    def default_severity(self, severity):
        self._default_severity_name = severity
        return self

    def default_severity_error(self):
        self._default_severity_name = Logger.ERROR_SEVERITY
        return self

    def default_severity_warn(self):
        self._default_severity_name = Logger.WARN_SEVERITY
        return self

    def default_severity_info(self):
        self._default_severity_name = Logger.INFO_SEVERITY
        return self

    def default_severity_trace(self):
        self._default_severity_name = Logger.TRACE_SEVERITY
        return self

    def use_default_severity_only(self, enable):
        self._default_severity_only = enable
        return self

    def timestamp(self, enable):
        self._use_timestamp = enable
        self._timestamp_exceptions.clear()
        return self

    def except_timestamp(self, severity):
        self._timestamp_exceptions.add(severity)
        return self

    def except_timestamp_error(self):
        self._timestamp_exceptions.add(Logger.ERROR_SEVERITY)
        return self

    def except_timestamp_warn(self):
        self._timestamp_exceptions.add(Logger.WARN_SEVERITY)
        return self

    def except_timestamp_info(self):
        self._timestamp_exceptions.add(Logger.INFO_SEVERITY)
        return self

    def except_timestamp_trace(self):
        self._timestamp_exceptions.add(Logger.TRACE_SEVERITY)
        return self

    def location(self, enable):
        self._use_location = enable
        self._location_exceptions.clear()
        return self

    def except_location(self, severity):
        self._location_exceptions.add(severity)
        return self

    def except_location_error(self):
        self._location_exceptions.add(Logger.ERROR_SEVERITY)
        return self

    def except_location_warn(self):
        self._location_exceptions.add(Logger.WARN_SEVERITY)
        return self

    def except_location_info(self):
        self._location_exceptions.add(Logger.INFO_SEVERITY)
        return self

    def except_location_trace(self):
        self._location_exceptions.add(Logger.TRACE_SEVERITY)
        return self


class _NoopBackend(LoggerBackend):
    def process_position(self, logger_label, item_label, position):
        pass

    def process_vector(self, logger_label, item_label, attach_label, vector):
        pass

    def process_transform(self, logger_label, item_label, attach_label, transform):
        pass

    def process_updatable_object(self, logger_label, item_label, value):
        pass

    def process_log(self, log):
        pass


class _AggregateBackend(LoggerBackend):
    def __init__(self, backends):
        self._backends = backends

    def process_position(self, logger_label, item_label, position):
        for backend in self._backends:
            backend.process_position(logger_label, item_label, position)

    def process_vector(self, logger_label, item_label, attach_label, vector):
        for backend in self._backends:
            backend.process_vector(logger_label, item_label, attach_label, vector)

    def process_transform(self, logger_label, item_label, attach_label, transform):
        for backend in self._backends:
            backend.process_transform(logger_label, item_label, attach_label, transform)

    def process_updatable_object(self, logger_label, item_label, value):
        for backend in self._backends:
            backend.process_transform(logger_label, item_label, value)

    def process_log(self, log):
        for backend in self._backends:
            backend.process_log(log)


class _SeverityFilter:
    def __init__(self, allow, exceptions):
        self._allow = allow
        self._exceptions = exceptions

    def permit(self, severity):
        return self._allow != (severity in self._exceptions)
