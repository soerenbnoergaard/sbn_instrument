from ipaddress import ip_address
import re
from abc import ABC, abstractmethod

from . import InstrumentSerial

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

class KoradKA3005PS(PowerSupply):
    """Korad KA3005PS power supply."""

    IDN_SUBSTRING = "KA3005"

    def __init__(self, serial_port="", phy=None):
        self.phy = phy
        if self.phy is None:
            self.phy = InstrumentSerial(ip_address)

        idn = self.get_id()
        if not self.IDN_SUBSTRING in idn:
            raise ValueError(f"Invalid instrument ID: '{idn}'")

    def get_id(self):
        return self.phy.query("*IDN?")

    def reset(self):
        self.phy.write("*RST")

    def close(self):
        self.phy.close()

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
        return 0.0

    def measure_current_A(self):
        return 0.0

    def measure_power_W(self):
        return 0.0

