import socket
import struct
from abc import ABC, abstractmethod

import pyvisa
import serial
import vxi11

class Instrument(ABC):
    """Base class for instruments."""

    # Abstract methods (must be overridden by subclasses):
    @abstractmethod
    def close(self):
        """Close access to the instrument."""

    @abstractmethod
    def set_timeout_s(self, value):
        """Set the instrument timeout in seconds."""

    @abstractmethod
    def write(self, s):
        """Write an SCPI command to the instrument."""

    @abstractmethod
    def read(self):
        """Read the response of an SCPI command."""

    @abstractmethod
    def query(self, s):
        """Query an SCPI (write followed by read)."""

    @abstractmethod
    def query_binary_values(self, s, datatype="B"):
        """SCPI binary value query of the format #LNB where L is the number
        of characters in the number N and N is the number of bytes in the
        data section B.

        The datatype uses the format from the ``struct`` module.
        """

    @abstractmethod
    def write_binary_values(self, command, data, datatype="B"):
        """Concatenate a binary block to a SCPI write command. The data will be
        formatted as #LNB where L is the number of characters in the number N
        and N is the number of bytes in the data section B.

        Example::

            write_binary_values("MMEM:DATA 'D:/IQDATA.WV',", data, datatype="B")

        The datatype uses the format from the ``struct`` module. The data must
        be a list of values of the ``datatype`` type.
        """

class InstrumentVxi11(Instrument):
    """VXI-11 compatible instrument through a TCP/IP socket."""

    def __init__(self, ip_address):
        self.inst = vxi11.Instrument(ip_address)
        self.set_timeout_s(30)

    def close(self):
        self.inst.close()

    def set_timeout_s(self, value):
        self.inst.timeout = 1000 * value

    def write(self, s):
        self.inst.write(s)

    def read(self):
        s = self.inst.read()
        return s

    def query(self, s):
        return self.inst.ask(s)

    def query_binary_values(self, s, datatype="B"):
        self.inst.write(s)
        data = self.inst.read_raw()
        assert chr(data[0]) == "#"
        L = int(chr(data[1]))
        N = int("".join(map(chr, data[2:2+L])))
        B = data[2+L:2+L+N]
        return [X[0] for X in struct.iter_unpack(datatype, B)]

    def write_binary_values(self, command, data, datatype="B"):
        if datatype != "B":
            raise ValueError("Only datatype == 'B' is currently supported. Please pack your data into a list of bytes.")
        B = bytearray([X & 0xff for X in data])
        N = str(len(B)).encode()
        L = str(len(N)).encode()
        full_command = command.encode() + b"#" + L + N + B
        self.inst.write_raw(full_command)

class InstrumentSocketAscii(Instrument):
    """Raw socket access through a TCP/IP connection. For most purposes,
    InstrumentVXI11 should be used instead.
    """

    def __init__(self, ip_address, port, newline="\n"):
        self.newline = newline
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip_address, port))
        self.sockfile = self.sock.makefile(mode="rw")

    def close(self):
        self.sock.close()

    def set_timeout_s(self, value):
        self.sock.settimeout(value)

    def write(self, s):
        self.sockfile.write(str(s + self.newline))
        self.sockfile.flush()

    def read(self):
        s = self.sockfile.readline().strip()
        return s

    def query(self, s):
        self.write(s)
        return self.read()

    def query_binary_values(self, s, datatype="B"):
        # Binary query proven quite unstable if implemented directly. On some
        # instruments, the ASCII commands did not work after a binary query had
        # been performed, even though the query worked ok. For binary support,
        # the VXI-11 implementation is recommended.

        raise NotImplementedError(f"{self.__class__.__name__} does not support binary query.")

    def write_binary_values(self, command, data, datatype="B"):
        raise NotImplementedError(f"{self.__class__.__name__} does not support binary write.")

class InstrumentSerial(Instrument):
    """VISA instrument accessed through a serial port."""

    def __init__(self, serial_port, baudrate_Hz, rtscts=False, dsrdtr=False, newline="\r\n"):
        self.newline = newline
        self.ser = serial.Serial(port=serial_port, baudrate=baudrate_Hz, rtscts=rtscts, dsrdtr=dsrdtr)

    def close(self):
        self.ser.close()

    def set_timeout_s(self, value):
        self.ser.timeout = value

    def write(self, s):
        self.ser.write((s + self.newline).encode())

    def read(self):
        r = self.ser.read_until(self.newline.encode()).decode().strip()
        return r

    def query(self, s):
        self.write(s)
        return self.read()

    def query_binary_values(self, s, datatype="B"):
        # FIXME: NOT TESTED
        self.write(s)
        H = self.ser.read(1).decode()
        assert H == "#"
        L = int(self.ser.read(1).decode())
        N = int(self.ser.read(L).decode())
        B = self.ser.read(N)
        return [X[0] for X in struct.iter_unpack(datatype, B)]

    def write_binary_values(self, command, data, datatype="B"):
        raise NotImplementedError("Binary write not implemented yet.")

class InstrumentVisa(Instrument):
    """Instrument using pyvisa. NOTE: This requires NI-VISA to be installed:
    https://www.ni.com/da-dk/support/downloads/drivers/download.ni-visa.html#409839
    """

    def __init__(self, visa_address):
        self.inst = pyvisa.ResourceManager().open_resource(visa_address)

    def close(self):
        self.inst.close()

    def set_timeout_s(self, value):
        self.inst.timeout = 1000*value

    def write(self, s):
        self.inst.write(s)

    def read(self):
        r = self.inst.read()
        return r

    def query(self, s):
        return self.inst.query(s)

    def query_binary_values(self, s, datatype="B"):
        return [X for X in self.inst.query_binary_values(s, datatype=datatype)]

    def write_binary_values(self, command, data, datatype="B"):
        self.inst.write_binary_values(command, data, datatype=datatype)

class InstrumentDummy(Instrument):
    """Instrument dummy for simulation purposes."""

    def __init__(self, query_responses: dict, write_callback=print):
        self.query_responses = query_responses
        self.write_callback = write_callback
        self.active_query = ""

    def close(self):
        pass

    def set_timeout_s(self, value):
        pass

    def write(self, s):
        self.active_query = s
        self.write_callback(s)

    def read(self):
        r = self.query_responses[self.active_query]
        self.write_callback(r)
        return r

    def query(self, s):
        self.write(s)
        return self.read()

    def query_binary_values(self, s, datatype="B"):
        self.write(s)
        B = self.query_responses[self.active_query]
        return [X[0] for X in struct.iter_unpack(datatype, B)]

    def write_binary_values(self, command, data, datatype="B"):
        self.write_callback(command)

