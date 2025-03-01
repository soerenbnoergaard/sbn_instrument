import re
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
    LoZ, Auto:          02 10 22 3E 4E 52 63 76 85 92 A7 B0 C0 D0 E0
    LoZ VDC, 08.98V:    02 1C 22 3E 4B 5E 6F 7D 8F 9E AF B8 C0 D0 E5
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
            timeout=5,
        )

    # Abstract methods expected from the base class:
    def get_id(self):
        return f"Brymen BM257s ({self.serial_port})"

    def reset(self):
        pass

    def close(self):
        self.ser.close()

    def measure_voltage_dc_V(self):
        s = self._get_display()
        m = re.search(r"([-\.\d]+)V", s)
        if m is not None:
            return float(m[1])
        m = re.search(r"([-\.\d]+)mV", s)
        if m is not None:
            return float(m[1]) * 1e-3

    def measure_voltage_ac_V(self):
        return self.measure_voltage_dc_V()

    def measure_current_dc_A(self):
        s = self._get_display()
        m = re.search(r"([-\.\d]+)A", s)
        if m is not None:
            return float(m[1])
        m = re.search(r"([-\.\d]+)mA", s)
        if m is not None:
            return float(m[1]) * 1e-3
        m = re.search(r"([-\.\d]+)uA", s)
        if m is not None:
            return float(m[1]) * 1e-6

    def measure_current_ac_A(self):
        return self.measure_current_dc_A()

    def measure_resistance_ohm(self):
        s = self._get_display()
        m = re.search(r"([-\.\d]+)Ohm", s)
        if m is not None:
            return float(m[1])
        m = re.search(r"([-\.\d]+)kOhm", s)
        if m is not None:
            return float(m[1]) * 1e3
        m = re.search(r"([-\.\d]+)MOhm", s)
        if m is not None:
            return float(m[1]) * 1e6

    def measure_frequency_Hz(self):
        s = self._get_display()
        m = re.search(r"([-\.\d]+)Hz", s)
        if m is not None:
            return float(m[1])
        m = re.search(r"([-\.\d]+)kHz", s)
        if m is not None:
            return float(m[1]) * 1e3
        m = re.search(r"([-\.\d]+)MHz", s)
        if m is not None:
            return float(m[1]) * 1e6

    def measure_temperature_C(self):
        s = self._get_display()
        if "---" in s:
            return -273.15
        m = re.search(r"([-\.\d]+)C", s)
        if m is not None:
            return float(m[1])

    def _read(self):
        def read_one_byte():
            s = self.ser.read(1)
            if len(s) < 1:
                raise ValueError("Serial error: No serial data read")
            return ord(s)

        # Try a few times
        for _ in range(10):
            try:
                self.ser.reset_input_buffer()

                # First byte must be 0x02
                for _ in range(16):
                    c = read_one_byte()
                    if c == 0x02:
                        break
                else:
                    raise ValueError("Serial error: No 0x02 byte found")

                result = [c]
                for _ in range(14):
                    result.append(read_one_byte())

                for n, b in enumerate(result):
                    if (b >> 4) & 0x0f != n:
                        raise ValueError("Serial error: Incorrect byte ordering")

                return result
            except ValueError as e:
                pass
        raise ValueError("Failed to read serial data")

    def _get_display(self):
        return self._parse_data(self._read())

    @staticmethod
    def _parse_data(data):
        # Parse segments
        seven_segment_lut = {
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
            (1, 1, 1, 0, 1, 1, 1): "A",
            (0, 0, 1, 1, 1, 0, 0): "u",
            (0, 0, 0, 1, 1, 1, 1): "t",
            (0, 0, 1, 1, 1, 0, 1): "o",
            (0, 1, 1, 1, 1, 0, 1): "d",
            (0, 0, 1, 0, 0, 0, 0): "i",
        }

        # Check bits in bytes. Bytes are 1-indexed like the Brymen documentation.
        b = lambda byte, bit: (data[byte-1] >> bit) & 1
        f = lambda s, byte, bit: s if b(byte, bit) else ""

        d1 = seven_segment_lut[(b(4,3),  b(5,3),  b(5,1),  b(5,0), b(4,1), b(4,2),  b(5,2))]
        d2 = seven_segment_lut[(b(6,3),  b(7,3),  b(7,1),  b(7,0), b(6,1), b(6,2),  b(7,2))]
        d3 = seven_segment_lut[(b(8,3),  b(9,3),  b(9,1),  b(9,0), b(8,1), b(8,2),  b(9,2))]
        d4 = seven_segment_lut[(b(10,3), b(11,3), b(11,1), b(11,0), b(10,1), b(10,2), b(11,2))]

        # Format string
        s_elements = [
            f("-",4,0), d1, f(".",6,0), d2, f(".",8,0), d3, f(".",10,0), d4, # Segments
            f("M",12,1), f("k",12,0), f("n",13,0), f("m",14,0), f("u",14,1), # Prefix
            f("dBm",12,2), f("Ohm",13,2), f("F",14,2), f("V",15,2), f("Hz",13,1), f("A",15,1), # Unit
            # TODO: Optionally add info about MIN, MAX, AUTO, AC, DC, etc.
        ]
        s = "".join(s_elements)
        return s
