"""ST-Link/V2 USB communication"""

import logging as _logging
import usb.core as _usb


class StlinkComException(Exception):
    """Exception"""


class StlinkComNotFound(Exception):
    """Exception"""


class StlinkComV2Usb():
    """ST-Link/V2 USB communication class"""
    ID_VENDOR = 0x0483
    ID_PRODUCT = 0x3748
    PIPE_OUT = 0x02
    PIPE_IN = 0x81
    DEV_NAME = "V2"

    _LOGGER_LEVEL3 = _logging.DEBUG - 3

    def __init__(self, logger=None):
        self._logger = logger
        self._dev = _usb.find(idVendor=self.ID_VENDOR, idProduct=self.ID_PRODUCT)
        if self._dev is None:
            raise StlinkComNotFound()

    def write(self, data, tout=200):
        """Write data to USB pipe"""
        self._logger.log(self._LOGGER_LEVEL3, "%s", ', '.join(['0x%02x' % i for i in data]))
        try:
            count = self._dev.write(self.PIPE_OUT, data, tout)
        except _usb.USBError as err:
            self._dev = None
            raise StlinkComException("USB Error: %s" % err)
        self._logger.log(self._LOGGER_LEVEL3, "count=%d", count)
        if count != len(data):
            raise StlinkComException("Error Sending data")

    def read(self, size, tout=200):
        """Read data from USB pipe"""
        self._logger.log(self._LOGGER_LEVEL3, "size=%d", size)
        read_size = size
        if read_size < 64:
            read_size = 64
        elif read_size % 4:
            read_size += 3
            read_size &= 0xffc
        try:
            data = self._dev.read(self.PIPE_IN, read_size, tout).tolist()[:size]
        except _usb.USBError as err:
            self._dev = None
            raise StlinkComException("USB Error: %s" % err)
        self._logger.log(self._LOGGER_LEVEL3, "%s", ', '.join(['0x%02x' % i for i in data]))
        return data

    def __del__(self):
        if self._dev is not None:
            self._dev.finalize()


class StlinkComV21Usb(StlinkComV2Usb):
    """ST-Link/V2-1 USB communication"""
    ID_VENDOR = 0x0483
    ID_PRODUCT = 0x374b
    PIPE_OUT = 0x01
    PIPE_IN = 0x81
    DEV_NAME = "V2-1"


class StlinkCom():
    """ST-Link communication class"""
    _STLINK_CMD_SIZE = 16
    _COM_CLASSES = [StlinkComV2Usb, StlinkComV21Usb]

    def __init__(self, logger=None):
        if logger is None:
            logger = _logging.Logger('stlink')
        self._logger = logger
        self._dev = None
        for com_cls in self._COM_CLASSES:
            try:
                self._dev = com_cls(logger=self._logger)
                break
            except StlinkComNotFound:
                continue
        else:
            raise StlinkComNotFound()

    @property
    def version(self):
        """property with device version"""
        return self._dev.DEV_NAME

    def xfer(self, command, data=None, rx_length=0, tout=200):
        """Transfer command between ST-Link

        Arguments:
            command: is an list of bytes with command (max 16 bytes)
            data: data will be sent after command
            rx_length: number of expected data to receive after command and data transfer
            tout: maximum waiting time for received data

        Return:
            received data

        Raises:
            StlinkComException
        """
        if len(command) > self._STLINK_CMD_SIZE:
            raise StlinkComException(
                "Error too many Bytes in command (maximum is %d Bytes)"
                % self._STLINK_CMD_SIZE)
        # pad to _STLINK_CMD_SIZE
        command += [0] * (self._STLINK_CMD_SIZE - len(command))
        self._dev.write(command, tout)
        if data:
            self._dev.write(data, tout)
        if rx_length:
            return self._dev.read(rx_length)
        return None