import traceback
from src.core.config import Config

class ActionNotImplementedException:
    """Requested ``Action()`` is not implemented"""
    def __init__(
            self,
            message: str = 'The requested action is not implemented in this driver.'
        ):
        """Initialize the ``ActionNotImplementedException`` object

        Args:
            number (int):   0x040C (1036)
            message (str):  'The requested action is not implemented in this driver.'

        * Logs ``ActionNotImplementedException: {message}``
        """
        self.number = 0x40C
        self.message = message
        cname = self.__class__.__name__

    @property
    def Number(self) -> int:
        return self.number

    @property
    def Message(self) -> str:
        return self.message

class DriverException:
    """
    **Exception Class for Driver Internal Errors**
        This exception is used for device errors and other internal exceptions.
        It can be instantiated with a captured exception object, and if so format
        the Alpaca error message to include line number/module or optionally a
        complete traceback of the exception (a config option).
    """
    def __init__(
            self,
            number: int = 0x500,
            message: str = 'Internal driver error - this should be more specific.',
            exc = None  # Python exception info
        ):
        """Initialize the DeviceException object

        Args:
            number (int):   Alpaca error number between 0x500 and 0xFFF, your choice
                            defaults to 0x500 (1280)
            message (str):  Specific error message or generic if left blank. Defaults
                            to 'Internal driver error - this should be more specific.'
            exc:            Contents 'ex' of 'except Exception as ex:' If not included
                            then only message is included. If supplied, then a detailed
                            error message with traceback is created (see full parameter)

        Notes:
            * Checks error number within legal range and if not, logs this error and substitutes
              0x500 number.
            * If the Python exception object is included as the 3rd argument, it constructs
              a message containing the name of the underlying Python exception and its basic
              context. If :py:attr:`~config.Config.verbose_driver_exceptions` is ``true``, a complete
              Python traceback is included.
            * Logs the constructed ``DriverException`` message
        """
        if number <= 0x500 and number >= 0xFFF:
            number = 0x500
        self.number = number
        cname = self.__class__.__name__
        if not exc is None:
            if Config.verbose_driver_exceptions:
                self.fullmsg = f'{cname}: {message}\n{traceback.format_exc()}'  # TODO Safe if not explicitly using exc?
            else:
                self.fullmsg = f'{cname}: {message}\n{type(exc).__name__}: {str(exc)}'
        else:
            self.fullmsg = f'{cname}: {message}'

    @property
    def Number(self) -> int:
        return self.number

    @property
    def Message(self) -> str:
        return self.fullmsg


class InvalidOperationException:
    """The client asked for something that can't be done"""
    def __init__(
            self,
            message: str = 'The requested operation cannot be undertaken at this time.'
        ):
        """Initialize the ``InvalidOperationException`` object

        Args:
            number (int):   0x040B (1035)
            message (str):  'The requested operation cannot be undertaken at this time.'

        * Logs ``InvalidOperationException: {message}``
        """
        self.number = 0x40B
        self.message = message
        cname = self.__class__.__name__

    @property
    def Number(self) -> int:
        return self.number

    @property
    def Message(self) -> str:
        return self.message


class InvalidValueException:
    """A value given is invalid or out of range"""
    def __init__(
            self,
            message: str = 'Invalid value given.'
        ):
        """Initialize the ``InvalidValueException`` object

        Args:
            number (int):   0x401 (1025)
            message (str):  'Invalid value given.'

        * Logs ``InvalidValueException: {message}``
        """
        self.number = 0x401
        self.message = message
        cname = self.__class__.__name__

    @property
    def Number(self) -> int:
        return self.number

    @property
    def Message(self) -> str:
        return self.message


class NotConnectedException:
    """The device must be connected and is not at this time"""
    def __init__(
            self,
            message: str = 'The device is not connected.'
        ):
        """Initialize the ``NotConnectedException`` object

        Args:
            number (int):   0x407 (1031)
            message (str):  'The device is not connected.'

        * Logs ``NotConnectedException: {message}``
        """
        self.number = 0x407
        self.message = message
        cname = self.__class__.__name__

    @property
    def Number(self) -> int:
        return self.number

    @property
    def Message(self) -> str:
        return self.message

class NotImplementedException:
    """The requested property or method is not implemented"""
    def __init__(
            self,
            message: str = 'Property or method not implemented.'
        ):
        """Initialize the ``NotImplementedException`` object

        Args:
            number (int):   0x400 (1024)
            message (str):  'Property or method not implemented.'

        * Logs ``NotImplementedException: {message}``
        """
        self.number = 0x400
        self.message = message
        cname = self.__class__.__name__

    @property
    def Number(self) -> int:
        return self.number

    @property
    def Message(self) -> str:
        return self.message

class ValueNotSetException:
    """The requested vzalue has not yet een set"""
    def __init__(
            self,
            message: str = 'The value has not yet been set.'
        ):
        """Initialize the ``ValueNotSetException`` object

        Args:
            number (int):   0x402 (1026)
            message (str):  'The value has not yet been set.'

        * Logs ``ValueNotSetException: {message}``
        """
        self.number = 0x402
        self.message = message
        cname = self.__class__.__name__

    @property
    def Number(self) -> int:
        return self.number

    @property
    def Message(self) -> str:
        return self.message
