from abc import ABC, abstractmethod

class Multimeter(ABC):
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
    def measure_voltage_dc_V(self):
        """Measure a DC voltage in volts."""

    @abstractmethod
    def measure_voltage_ac_V(self):
        """Measure an AC voltage in volts."""

    @abstractmethod
    def measure_current_dc_A(self):
        """Measure a DC current in ampere."""

    @abstractmethod
    def measure_current_ac_A(self):
        """Measure an AC current in ampere."""

    @abstractmethod
    def measure_resistance_ohm(self):
        """Measure resistance in ohm."""

    @abstractmethod
    def measure_frequency_Hz(self):
        """Measure frequency in hertz."""

    @abstractmethod
    def measure_temperature_C(self):
        """Measure temperature in degrees Celsius."""

class Dummy(Multimeter):
    """Dummy multimeter for simulation use."""

    def get_id(self):
        return "DummyMultimeter"

    def reset(self):
        pass

    def close(self):
        pass

    def measure_voltage_dc_V(self):
        return 0

    def measure_voltage_ac_V(self):
        return 0

    def measure_current_dc_A(self):
        return 0

    def measure_current_ac_A(self):
        return 0

    def measure_resistance_ohm(self):
        return 0

    def measure_frequency_Hz(self):
        return 0

    def measure_temperature_C(self):
        return 0

