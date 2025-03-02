from abc import ABC, abstractmethod
import hid
import serial

_SEVEN_SEGMENT_LUT = {
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
    def set_mode_voltage_dc_V(self):
        """Set the instrument to DC voltage mode (V)."""

    @abstractmethod
    def set_mode_voltage_ac_V(self):
        """Set the instrument to AC voltage mode (V)."""

    @abstractmethod
    def set_mode_current_dc_A(self):
        """Set the instrument to DC current mode (A)."""

    @abstractmethod
    def set_mode_current_ac_A(self):
        """Set the instrument to AC current mode (A)."""

    @abstractmethod
    def set_mode_resistance_ohm(self):
        """Set the instrument to resistance mode (ohm)."""

    @abstractmethod
    def set_mode_frequency_Hz(self):
        """Set the instrument to frequency mode (Hz)."""

    @abstractmethod
    def set_mode_temperature_C(self):
        """Set the instrument to temperature mode (degrees Celsius)."""

    @abstractmethod
    def measure(self):
        """Return a measurement value for the selected mode."""

    @abstractmethod
    def measure_dual(self):
        """Return a measurement 2-tuple of values for the selected mode (for
        dual-display multimeters).
        """

class Dummy(Multimeter):
    """Dummy multimeter for simulation use."""

    def get_id(self):
        return "DummyMultimeter"

    def reset(self):
        pass

    def close(self):
        pass

    def set_mode_voltage_dc_V(self):
        pass

    def set_mode_voltage_ac_V(self):
        pass

    def set_mode_current_dc_A(self):
        pass

    def set_mode_current_ac_A(self):
        pass

    def set_mode_resistance_ohm(self):
        pass

    def set_mode_frequency_Hz(self):
        pass

    def set_mode_temperature_C(self):
        pass

    def measure(self):
        return 0.0

    def measure_dual(self):
        return 0.0, 0.0

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

    def set_mode_voltage_dc_V(self):
        """Mode must be selected manually for this instrument."""
        pass

    def set_mode_voltage_ac_V(self):
        """Mode must be selected manually for this instrument."""
        pass

    def set_mode_current_dc_A(self):
        """Mode must be selected manually for this instrument."""
        pass

    def set_mode_current_ac_A(self):
        """Mode must be selected manually for this instrument."""
        pass

    def set_mode_resistance_ohm(self):
        """Mode must be selected manually for this instrument."""
        pass

    def set_mode_frequency_Hz(self):
        """Mode must be selected manually for this instrument."""
        pass

    def set_mode_temperature_C(self):
        """Mode must be selected manually for this instrument."""
        pass

    def measure(self):
        value, unit, flags = self._parse_data(self._read())
        return value

    def measure_dual(self):
        return self.measure(), None

    def _read(self):
        def read_one_byte():
            s = self.ser.read(1)
            if len(s) < 1:
                raise ValueError("Serial error: No serial data read")
            return ord(s)

        # Try a few times before giving up.
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

                # Read and store all 15 bytes
                result = [c]
                for _ in range(14):
                    result.append(read_one_byte())

                # Check that the first nibble of each byte contains the correct index.
                for n, b in enumerate(result):
                    if (b >> 4) & 0x0f != n:
                        raise ValueError("Serial error: Incorrect byte ordering")

                return result

            except ValueError:
                pass

        raise ValueError("Failed to read serial data")

    @staticmethod
    def _parse_data(data):
        """Return 3-tuple: Value, unit, flags."""

        # Parse segments

        # Check bits in bytes. Bytes are 1-indexed like the Brymen documentation.
        b = lambda byte, bit: (data[byte-1] >> bit) & 1
        f = lambda s, byte, bit: s if b(byte, bit) else ""

        d1 = _SEVEN_SEGMENT_LUT[(b(4,3),  b(5,3),  b(5,1),  b(5,0), b(4,1), b(4,2),  b(5,2))]
        d2 = _SEVEN_SEGMENT_LUT[(b(6,3),  b(7,3),  b(7,1),  b(7,0), b(6,1), b(6,2),  b(7,2))]
        d3 = _SEVEN_SEGMENT_LUT[(b(8,3),  b(9,3),  b(9,1),  b(9,0), b(8,1), b(8,2),  b(9,2))]
        d4 = _SEVEN_SEGMENT_LUT[(b(10,3), b(11,3), b(11,1), b(11,0), b(10,1), b(10,2), b(11,2))]

        # Extract value and scale it according to the engineering prefixes
        if b(12,1): # M
            scale = 1e6
        elif b(12,0): # k
            scale = 1e3
        elif b(14,0): # m
            scale = 1e-3
        elif b(14,1): # u
            scale = 1e-6
        elif b(13,0): # n
            scale = 1e-9
        else:
            scale = 1.0

        value_string = "".join([f("-",4,0), d1, f(".",6,0), d2, f(".",8,0), d3, f(".",10,0), d4])
        try:
            if value_string.endswith("C") or value_string.endswith("F"):
                value_string = value_string[:-1]
            value = float(value_string) * scale
        except ValueError:
            value = None

        # Extract unit
        if b(12,2):
            unit = "dBm"
        elif b(13,2):
            unit = "Ohm"
        elif b(14,2):
            unit = "F"
        elif b(15,2):
            unit = "V"
        elif b(13,1):
            unit = "Hz"
        elif b(15,1):
            unit = "A"
        else:
            unit = None

        # Extract flags
        # TODO: Optionally add info about MIN, MAX, AUTO, AC, DC, etc.
        flags = ()

        return value, unit, flags

class BrymenBm869s(Multimeter):
    """Brymen BM869s multimeter.

    Interface through USB HID (on linux, remember to add a udev rule!):
    1. Write an output report: [0x00, 0x00, 0x86, 0x66].
    2. Read three input reports (27 bytes in total, including report IDs).
    3. The 27 bytes are bit maps for each LCD segment and must be decoded.

    See more details in the Brymen documentation:
    - Protocol for 500000-count professional dual display DMM series

    Example USB output (each report is 8 bytes):
    VDC 0.3301V                 00 19 10 be f9 f8 be a0 01 00 00 00 00 00 00 00 86 86 86 86 00 00 00 00
    VDC 0.4988V (VAC 0.175V)    00 18 00 be e5 fc fe fe 01 20 be a1 a8 7c 08 00 86 86 86 86 00 00 00 00
    """

    def __init__(self, hid_index=0):
        self.hid_index = hid_index

        hid_devices = hid.enumerate(0x0820, 0x0001)
        self.hid = hid.device()
        self.hid.open_path(hid_devices[hid_index]["path"])

    # Abstract methods expected from the base class:
    def get_id(self):
        return f"Brymen BM869s ({self.hid_index})"

    def reset(self):
        pass

    def close(self):
        self.hid.close()

    def set_mode_voltage_dc_V(self):
        """Mode must be selected manually for this instrument."""
        pass

    def set_mode_voltage_ac_V(self):
        """Mode must be selected manually for this instrument."""
        pass

    def set_mode_current_dc_A(self):
        """Mode must be selected manually for this instrument."""
        pass

    def set_mode_current_ac_A(self):
        """Mode must be selected manually for this instrument."""
        pass

    def set_mode_resistance_ohm(self):
        """Mode must be selected manually for this instrument."""
        pass

    def set_mode_frequency_Hz(self):
        """Mode must be selected manually for this instrument."""
        pass

    def set_mode_temperature_C(self):
        """Mode must be selected manually for this instrument."""
        pass

    def measure(self):
        return self.measure_dual()[0]

    def measure_dual(self):
        return self._parse_data(self._read())

    def _read(self):
        # Try a few times vefore giving up
        for _ in range(10):
            try:
                self.hid.write([0x00, 0x00, 0x86, 0x66])
                r1 = self.hid.read(max_length=9, timeout_ms=3000)
                r2 = self.hid.read(max_length=9, timeout_ms=3000)
                r3 = self.hid.read(max_length=9, timeout_ms=3000)
                r = r1 + r2 + r3
                if len(r) != 24:
                    raise ValueError("Failed to read multimeter data")
                return r
            except ValueError:
                pass
        raise ValueError("Failed to read multimeter data after multiple attempts")

    @staticmethod
    def _parse_data(data):
        # Return a 2-tuple with the numerical readout for each display (or None
        # for non-numeric values).

        # Helper functions for check a (byte, bit) according to the table in the
        # Brymen documentation. b() returns the bit value and f() returns a
        # given string if the bit is set and an empty string otherwise.
        def b(byte, bit):
            assert 1 <= byte <= 27
            if byte < 10:
                return (data[byte-2] >> bit) & 1
            elif byte < 19:
                return (data[byte-3] >> bit) & 1
            else:
                return (data[byte-4] >> bit) & 1

        def f(s, byte, bit):
            if b(byte, bit):
                return s
            else:
                return ""

        # Parse segments
        d1  = _SEVEN_SEGMENT_LUT[(b( 5,3),  b( 5,7),  b( 5,5),  b( 5,4), b( 5,1), b( 5,2),  b( 5,6))]
        d2  = _SEVEN_SEGMENT_LUT[(b( 6,3),  b( 6,7),  b( 6,5),  b( 6,4), b( 6,1), b( 6,2),  b( 6,6))]
        d3  = _SEVEN_SEGMENT_LUT[(b( 7,3),  b( 7,7),  b( 7,5),  b( 7,4), b( 7,1), b( 7,2),  b( 7,6))]
        d4  = _SEVEN_SEGMENT_LUT[(b( 8,3),  b( 8,7),  b( 8,5),  b( 8,4), b( 8,1), b( 8,2),  b( 8,6))]
        d5  = _SEVEN_SEGMENT_LUT[(b( 9,3),  b( 9,7),  b( 9,5),  b( 9,4), b( 9,1), b( 9,2),  b( 9,6))]
        d6  = _SEVEN_SEGMENT_LUT[(b(11,3),  b(11,7),  b(11,5),  b(11,4), b(11,1), b(11,2),  b(11,6))]
        d7  = _SEVEN_SEGMENT_LUT[(b(13,3),  b(13,7),  b(13,5),  b(13,4), b(13,1), b(13,2),  b(13,6))]
        d8  = _SEVEN_SEGMENT_LUT[(b(14,3),  b(14,7),  b(14,5),  b(14,4), b(14,1), b(14,2),  b(14,6))]
        d9  = _SEVEN_SEGMENT_LUT[(b(15,3),  b(15,7),  b(15,5),  b(15,4), b(15,1), b(15,2),  b(15,6))]
        d10 = _SEVEN_SEGMENT_LUT[(b(16,3),  b(16,7),  b(16,5),  b(16,4), b(16,1), b(16,2),  b(16,6))]

        # Parse primary display
        if b(18,1): # dB (conflicts with "m")
            scale = 1.0
        elif b(18,5): # M
            scale = 1e6
        elif b(18,6): # k
            scale = 1e3
        elif b(18,2): # m
            scale = 1e-3
        elif b(18,3): # u
            scale = 1e-6
        elif b(17,6): # n
            scale = 1e-9
        else:
            scale = 1.0

        value_string = "".join([f("-",4,7), d1, f(".",6,0), d2, f(".",7,0), d3, f(".",8,0), d4, f(".",9,0), d5])
        try:
            if value_string.endswith("C") or value_string.endswith("F"):
                value_string = value_string[:-1]
            value1 = float(value_string) * scale
        except ValueError:
            value1 = None

        # Parse secondary display
        if b(17,0): # M
            scale = 1e6
        elif b(17,1): # k
            scale = 1e3
        elif b(12,1): # m
            scale = 1e-3
        elif b(12,0): # u
            scale = 1e-6
        else:
            scale = 1.0

        value_string = "".join([f("-",12,4), d7, f(".",14,0), d8, f(".",15,0), d9, f(".",16,0), d10])
        try:
            if value_string.endswith("C") or value_string.endswith("F"):
                value_string = value_string[:-1]
            value2 = float(value_string) * scale
        except ValueError:
            value2 = None

        # TODO: Consider parsing units and flags

        return value1, value2
