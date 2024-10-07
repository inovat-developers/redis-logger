from __future__ import annotations

import concurrent.futures
import logging
from abc import ABC, abstractmethod
from logging.handlers import SMTPHandler
from threading import Lock

from pydantic import BaseModel, ValidationError


class BaseLoggerConfiguration(BaseModel):
    pass


class SMTPLoggerConfiguration(BaseModel):
    pass


__all__: list[str] = [
    "SMTPLogger",
    "InovatSMTPHandler",
]


class BaseLogger(ABC):
    def __init__(self, configuration: BaseLoggerConfiguration) -> None:
        self._configuration: BaseLoggerConfiguration = configuration
        self._logger: logging.Logger = None

    @property
    def logger(self) -> logging.Logger:
        if not self.configured():
            raise Exception("Exception")
        return self._logger

    @classmethod
    @abstractmethod
    def from_dict(cls, configuration_dict: dict) -> BaseLogger:
        pass

    @abstractmethod
    def configure(self) -> None:
        pass

    def configured(self) -> bool:
        return self._logger is not None

    def log(self, message: str) -> None:
        if not self.configured():
            raise Exception
        self._logger.log(level=self._configuration.log_level, msg=message)

    def debug(self, message: str) -> None:
        if not self.configured():
            raise Exception
        self._logger.debug(msg=message)

    def info(self, message: str) -> None:
        if not self.configured():
            raise Exception
        self._logger.info(msg=message)

    def warning(self, message: str) -> None:
        if not self.configured():
            raise Exception
        self._logger.warning(msg=message)

    def error(self, message: str) -> None:
        if not self.configured():
            raise Exception
        self._logger.error(msg=message)

    def critical(self, message: str) -> None:
        if not self.configured():
            raise Exception
        self._logger.critical(msg=message)


class InovatSMTPHandler(SMTPHandler):
    def __init__(self, *args, **kwargs) -> None:
        mailhost = args[0] if len(args) > 0 else kwargs.get("maihost", "")
        fromaddr = args[1] if len(args) > 1 else kwargs.get("fromaddr", "")
        toaddrs = args[2] if len(args) > 2 else kwargs.get("toaddrs", [])
        subject = args[3] if len(args) > 3 else kwargs.get("subject", "")
        credentials = kwargs.get("credentials", None)
        secure = kwargs.get("secure", False)
        timeout = kwargs.get("timeout", 5.0)
        super().__init__(
            mailhost=mailhost,
            fromaddr=fromaddr,
            toaddrs=toaddrs,
            subject=subject,
            credentials=credentials,
            secure=secure,
            timeout=timeout,
        )
        self.__buffer_size = kwargs.get("buffer_size", 10)
        self.__buffer = list[logging.LogRecord] = []
        self.__executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=10,
        )
        self.__lock = Lock()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            with self.__lock:
                self.__buffer.append(record)
                if len(self.__buffer) >= self.__buffer_size:
                    self.__executor.submit(self.__emit, self).result()
                    self.__buffer = []
        except Exception:
            self.handleError(record=record)

    def __emit(self) -> None:
        import email.utils
        import smtplib
        from email.message import EmailMessage

        port: int | None = self.mailport
        if not port:
            port = smtplib.SMTP_PORT
        smtp = smtplib.SMTP(host=self.mailhost, port=port, timeout=self.timeout)
        msg = EmailMessage()
        msg["From"] = self.fromaddr
        msg["To"] = ",".join(self.toaddrs)
        msg["Subject"] = self.subject  # self.getSubject(record)
        msg["Date"] = email.utils.localtime()
        msg.set_content(
            "\n".join([self.format(record=record) for record in self.__buffer])
        )
        if self.username:
            if self.secure is not None:
                smtp.ehlo()
                smtp.starttls(*self.secure)
                smtp.ehlo()
            smtp.login(user=self.username, password=self.password)
        smtp.send_message(msg=msg)
        smtp.quit()


class SMTPLogger(BaseLogger):
    def __init__(self, configuration: SMTPLoggerConfiguration) -> None:
        super().__init__(configuration=configuration)

    def configure(self) -> None:
        try:
            self._logger: logging.Logger = logging.getLogger(
                name=self._configuration.name
            )
            logger_format = logging.Formatter(
                fmt=self._configuration.format, datefmt=self._configuration.date_format
            )
            logger_handler = InovatSMTPHandler(
                mailhost=self._configuration.mailhost,
                fromaddr=self._configuration.fromaddr,
                toaddrs=self._configuration.toaddrs,
                subject=self._configuration.subject,
                credentials=self._configuration.credentials,
                secure=self._configuration.secure,
                timeout=self._configuration.timeout,
                buffer_size=self._configuration.buffer_size,
            )
            logger_handler.setLevel(level=self._configuration.log_level)
            logger_handler.setFormatter(fmt=logger_format)
            self._logger.addHandler(hdlr=logger_handler)
        except Exception:
            raise Exception

    @classmethod
    def from_dict(cls, configuration_dict: dict) -> SMTPLogger:
        try:
            configuration: SMTPLoggerConfiguration = SMTPLoggerConfiguration(
                **configuration_dict
            )
            return cls(configuration)
        except ValidationError:
            raise Exception
        except Exception:
            raise Exception
