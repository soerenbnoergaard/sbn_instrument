from abc import ABC, abstractmethod
import serial

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

class BrymenBm257s(Multimeter):
    """Brymen BM257s multimeter.
    To enable serial output, hold "HOLD" while powering on.
    Then the serial is continuously written without asking.

    Example serial output:
    LoZ VDC, 08.98V:    02 1A 20 3E 4B 5E 6F 7E 8F 9D AF B8 C0 D2 E3
    VAC, 0.168V:        02 1A 20 3E 4B 51 6A 7E 87 9E AF B8 C0 D0 E5
    VDC, 0.077V:        02 1C 20 3E 4B 5F 6B 78 8A 98 AA B8 C0 D0 E5
    Ohm, 428.3 ohm:     02 18 20 34 4E 5A 6D 7E 8F 9B AD B8 C4 D0 E1
    C, 00.03 nF:        02 18 20 3E 4B 5E 6B 7F 8B 98 AF B8 C1 D4 E0
    Diode, 0.938V:      02 10 20 3E 4B 5D 6F 78 8F 9E AF B8 C0 D0 E4
    Diode, .OL          02 10 20 30 40 5F 6B 76 81 90 A0 B8 C0 D0 E4
    mVDC, -02.11mV      02 1C 20 3F 4B 5A 6D 71 8A 90 AA B8 C0 D1 E5
    mVAC, 30.77mV       02 1A 20 38 4F 5E 6B 7F 87 98 AA B8 C0 D1 E5
    T, 024C             02 10 20 3E 4B 5A 6D 74 8E 9E A1 B8 C0 D0 E0
    T, 076F             02 10 20 3E 4B 58 6A 7E 87 9E A4 B8 C0 D0 E0
    ADC, 0.069A         02 1C 20 3E 4B 5F 6B 7E 87 9C AF B8 C0 D0 E3
    AAC, 0.018A         02 1A 20 3E 4B 5F 6B 70 8A 9E AF B8 C0 D0 E3
    mADC, 70.5mA        02 1C 20 3E 4B 58 6A 7E 8B 9D A7 B8 C0 D1 E3
    mAAC, 05.86mA       02 1A 20 3E 4B 5C 67 7F 8F 9E A7 B8 C0 D1 E3
    uADC, 1677uA        02 1C 20 30 4A 5E 67 78 8A 98 AA B8 C0 D2 E3
    uAAC, 088.9uA       02 1A 20 3E 4B 5E 6F 7E 8F 9D AF B8 C0 D2 E3

    Inspired by https://github.com/RobertWilbrandt/bm257s
    """

    def __init__(self, serial_port):
        self.serial_port = serial_port
        self.ser = serial.Serial(
            serial_port,
            baudrate=9600,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1,
        )

    # Abstract methods expected from the base class:
    def get_id(self):
        return f"Brymen BM257s ({self.serial_port})"

    def reset(self):
        pass

    def close(self):
        self.ser.close()

    def measure_voltage_dc_V(self):
        return self.parse_voltage_dc_V(self._measure())

    def measure_voltage_ac_V(self):
        return self.parse_voltage_ac_V(self._measure())

    def measure_current_dc_A(self):
        return self.parse_current_dc_A(self._measure())

    def measure_current_ac_A(self):
        return self.parse_current_ac_A(self._measure())

    def measure_resistance_ohm(self):
        return self.parse_resistance_ohm(self._measure())

    def measure_frequency_Hz(self):
        return self.parse_frequency_Hz(self._measure())

    def measure_temperature_C(self):
        return self.parse_temperature_C(self._measure())

    def _measure(self):
        # TODO
        return [0x02, 0x1C, 0x20, 0x3E, 0x4B, 0x5F, 0x6B, 0x78, 0x8A, 0x98, 0xAA, 0xB8, 0xC0, 0xD0, 0xE5]

    @staticmethod
    def _get_bit(b, byte, bit):
        return (b[byte] >> bit) & 1

    @classmethod
    def _get_segment(cls, b, n):
        # TODO: Make a class for the parser functions
        assert 1 <= n <= 4
        lut = {
            (1, 1, 1, 1, 1, 1, 0): "0",
            (0, 1, 1, 0, 0, 0, 0): "1",
            (1, 1, 0, 1, 1, 0, 1): "2",
            (1, 1, 1, 1, 0, 0, 1): "3",
            (0, 1, 1, 0, 0, 1, 1): "4",
            (1, 0, 1, 1, 0, 1, 1): "5",
            (1, 0, 1, 1, 1, 1, 1): "6",
            (1, 1, 1, 0, 0, 0, 0): "7",
            (1, 1, 1, 1, 1, 1, 1): "8",
            (1, 1, 1, 1, 0, 1, 1): "9",
            (1, 0, 0, 1, 1, 1, 0): "C",
            (1, 0, 0, 0, 1, 1, 1): "F",
            (0, 0, 0, 0, 0, 0, 1): "-",
            (0, 0, 0, 0, 0, 0, 0): " ",
            (0, 0, 0, 1, 1, 1, 0): "L",
        }

        bit = lambda byte, bit: cls._get_bit(b, byte, bit)

        if n == 1:
            v = lut[(bit(3,3), bit(4,3), bit(4,1), bit(4,0), bit(3,1), bit(3,2), bit(4,2))]
        elif n == 2:
            v = lut[(bit(5,3), bit(6,3), bit(6,1), bit(6,0), bit(5,1), bit(5,2), bit(6,2))]
        elif n == 3:
            v = lut[(bit(7,3), bit(8,3), bit(8,1), bit(8,0), bit(7,1), bit(7,2), bit(8,2))]
        elif n == 4:
            v = lut[(bit(9,3), bit(10,3), bit(10,1), bit(10,0), bit(9,1), bit(9,2), bit(10,2))]
        return v

    @classmethod
    def _parse_voltage_dc_V(cls, b):
        assert len(b) == 15
        assert b[0] & 0x0f == 0x02
        for n in range(15):
            assert (b[n] >> 4) & 0x0f == n


        sign = -1 if cls._get_bit(b, 3, 0) else 1
        print(cls._get_segment(b, 1))
        print(cls._get_segment(b, 2))
        print(cls._get_segment(b, 3))
        print(cls._get_segment(b, 4))

        assert cls._get_bit(b, 14, 2) == 1# "V"
        return 0.0 # TODO

    @classmethod
    def _parse_voltage_ac_V(cls, b):
        return 0.0 # TODO

    @classmethod
    def _parse_current_dc_A(cls, b):
        return 0.0 # TODO

    @classmethod
    def _parse_current_ac_A(cls, b):
        return 0.0 # TODO

    @classmethod
    def _parse_resistance_ohm(cls, b):
        return 0.0 # TODO

    @classmethod
    def _parse_frequency_Hz(cls, b):
        return 0.0 # TODO

    @classmethod
    def _parse_temperature_C(cls, b):
        return 0.0 # TODO
