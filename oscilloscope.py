from abc import ABC, abstractmethod

from . import InstrumentVxi11, InstrumentUsbtmcLinux

class Oscilloscope(ABC):
    """Interface class for an oscilloscope. This instrument is mostly
    expected to be set up manually due to the required calibration, so the
    interface is minimal.
    """

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
    def save_screenshot_png(self, filename):
        """Save a screenshot to a PNG file."""

class Dummy(Oscilloscope):
    """Dummy oscilloscope for simulation use."""

    def get_id(self):
        return "DummyOscilloscope"

    def reset(self):
        pass

    def close(self):
        pass

    def save_screenshot_png(self, filename):
        pass

class RigolDs1104Z(Oscilloscope):
    """Rigol DS1104Z oscilloscope."""

    def __init__(self, ip_address="", phy=None):
        self.phy = phy
        if self.phy is None:
            self.phy = InstrumentVxi11(ip_address)

    def get_id(self):
        return self.phy.query("*IDN?")

    def reset(self):
        self.phy.write("*RST")

    def close(self):
        self.phy.close()

    def save_screenshot_png(self, filename):
        data = bytearray(self.phy.query_binary_values("DISPLAY:DATA? ON,OFF,PNG", datatype="B"))
        with open(filename, "wb") as fh:
            fh.write(data)

class KeysightDsox1102G(Oscilloscope):
    """Keysight DSOX1102G oscilloscope with signal generator."""

    def __init__(self, device_address="", phy=None):
        self.phy = phy
        if self.phy is None:
            self.phy = InstrumentUsbtmcLinux(device_address)

    def get_id(self):
        return self.phy.query("*IDN?")

    def reset(self):
        self.phy.write("*RST")

    def close(self):
        self.phy.close()

    def save_screenshot_png(self, filename):
        data = bytearray(self.phy.query_binary_values(":DISPLAY:DATA? PNG, COLOR", datatype="B"))
        with open(filename, "wb") as f:
            f.write(data)
