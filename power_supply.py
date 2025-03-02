import re
import time
from abc import ABC, abstractmethod
import serial

class PowerSupply(ABC):
    """Common interface for a power supply instrument."""

    @abstractmethod
    def get_id(self):
        """Return the instrument ID."""

    @abstractmethod
    def reset(self):
        """Reset the instrument."""

    @abstractmethod
    def close(self):
        """Close the connection to the instrument."""

    @abstractmethod
    def set_channel(self, channel):
        """Select which channel to control. The channel number should follow
        the number scheme used in the SCPI commands of the specific instrument.
        """

    @abstractmethod
    def set_output_enable(self):
        """Enable the selected output."""

    @abstractmethod
    def set_output_disable(self):
        """Disable the selected output."""

    @abstractmethod
    def set_voltage_V(self, value):
        """Set the output voltage of the selected channel."""

    @abstractmethod
    def set_current_limit_A(self, value):
        """Set the current limit of the selected channel."""

    @abstractmethod
    def measure_voltage_V(self):
        """Measure the voltage of the selected channel."""

    @abstractmethod
    def measure_current_A(self):
        """Measure the current of the selected channel."""

    @abstractmethod
    def measure_power_W(self):
        """Measure the power of the selected channel."""

class Dummy(PowerSupply):
    """Dummy power supply for simulation use."""

    def get_id(self):
        return "DummyPowerSupply"

    def reset(self):
        pass

    def close(self):
        pass

    def set_channel(self, channel):
        pass

    def set_output_enable(self):
        pass

    def set_output_disable(self):
        pass

    def set_voltage_V(self, value):
        pass

    def set_current_limit_A(self, value):
        pass

    def measure_voltage_V(self):
        return 0

    def measure_current_A(self):
        return 0

    def measure_power_W(self):
        return 0

class Channel(PowerSupply):
    """Handle for a single channel of the given power supply."""

    def __init__(self, psu: PowerSupply, channel: int):
        self.psu = psu
        self.channel = channel

    def get_id(self):
        return self.psu.get_id()

    def reset(self):
        self.psu.reset()

    def close(self):
        self.psu.close()

    def set_channel(self, channel):
        raise NotImplementedError("The `Channel` class handles `set_channel()` internally - do not use it explicitly!")

    def set_output_enable(self):
        self.psu.set_channel(self.channel)
        self.psu.set_output_enable()

    def set_output_disable(self):
        self.psu.set_channel(self.channel)
        self.psu.set_output_disable()

    def set_voltage_V(self, value):
        self.psu.set_channel(self.channel)
        self.psu.set_voltage_V(value)

    def set_current_limit_A(self, value):
        self.psu.set_channel(self.channel)
        self.psu.set_current_limit_A(value)

    def measure_voltage_V(self):
        self.psu.set_channel(self.channel)
        return self.psu.measure_voltage_V()

    def measure_current_A(self):
        self.psu.set_channel(self.channel)
        return self.psu.measure_current_A()

    def measure_power_W(self):
        self.psu.set_channel(self.channel)
        return self.psu.measure_power_W()

class KoradKa3005Ps(PowerSupply):
    """Korad KA3005PS power supply.
    Inspired by https://github.com/starforgelabs/py-korad-serial/
    """

    IDN_SUBSTRING = "KA3005PS"

    def __init__(self, serial_port):
        self.ser = serial.Serial(
            serial_port,
            baudrate=115200,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1,
        )

        idn = self.get_id()
        if not self.IDN_SUBSTRING in idn:
            raise ValueError(f"Invalid instrument ID: '{idn}'")

    def get_id(self):
        return self._query("*IDN?")

    def reset(self):
        pass

    def close(self):
        self.ser.close()

    def set_channel(self, channel):
        pass

    def set_output_enable(self):
        self._write("OUT1")

    def set_output_disable(self):
        self._write("OUT0")

    def set_voltage_V(self, value):
        self._write(f"VSET1:{value:05.2f}")

    def set_current_limit_A(self, value):
        self._write(f"ISET1:{value:05.3f}")
        pass

    def measure_voltage_V(self):
        return float(self._query("VOUT1?", fixed_length=5))

    def measure_current_A(self):
        return float(self._query("IOUT1?", fixed_length=5))

    def measure_power_W(self):
        return self.measure_voltage_V() * self.measure_current_A()

    def _write(self, command):
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        time.sleep(0.1)
        self.ser.write(command.encode("ascii"))

    def _read(self, fixed_length=None):
        result = []
        c = self.ser.read(1).decode("ascii")
        while len(c) > 0 and ord(c) != 0:
            result.append(c)
            if fixed_length is not None and len(result) == fixed_length:
                break
            c = self.ser.read(1).decode("ascii")
        return ''.join(result)

    def _query(self, command, fixed_length=None):
        self._write(command)
        return self._read(fixed_length)
