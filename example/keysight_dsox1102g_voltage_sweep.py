import time
import sys
from math import log10, sqrt
import sbn_instrument

"""
Using the waveform generator to sweep a voltage in x dB increments. The
instrument must manually be set up at a low voltage with a sine wave input on
channel 1 and output on channel 2.
"""

filelabel = time.strftime("%Y-%m-%d_%H%M%S") + "_voltage_sweep"
if len(sys.argv) >= 2:
    filelabel += "_" + sys.argv[1]
output = sbn_instrument.CsvWriter(filelabel + ".csv")
scope = sbn_instrument.oscilloscope.KeysightDsox1102G("/dev/usbtmc0")

def scope_write(s):
    return scope.phy.write(s)

def scope_query(s):
    return scope.phy.query(s)

def argnearest(value, search_array):
    idx = min(range(len(search_array)), key=lambda i: abs(search_array[i] - value))
    return idx

def scope_get_available_scales():
    return [50e-6, 10e-6, 50e-6, 100e-6, 200e-6, 500e-6, 1e-3, 2e-3, 5e-3, 10e-3, 20e-3, 50e-3, 100e-3, 200e-3, 500e-3, 1, 2, 5, 10]

def scope_scale_next(channel, up=True):
    scale = float(scope_query(f"CHANNEL{channel}:SCALE?"))
    scales = scope_get_available_scales()
    n = argnearest(scale, scales)
    if up:
        n_new = n + 1
        if n_new > len(scales):
            raise IndexError
    else:
        n_new = n - 1
        if n_new < 0:
            raise IndexError
    scope_write(f"CHANNEL{channel}:SCALE {scales[n_new]}")
    scale_new = float(scope_query(f"CHANNEL{channel}:SCALE?"))
    if scale_new == scale:
        raise ValueError

def scope_autoscale(channel=1):
    V_min = float(scope_query(f":MEASURE:VMIN? CHAN{channel}"))
    V_max = float(scope_query(f":MEASURE:VMAX? CHAN{channel}"))
    V_scale = float(scope_query(f"CHANNEL{channel}:SCALE?"))

    try:
        if V_min < -3.5*V_scale or V_max > 3.5*V_scale:
            scope_scale_next(channel, up=True)
            scope_autoscale(channel)
        if V_min > -1*V_scale or V_max < 1*V_scale:
            scope_scale_next(channel, up=False)
            scope_autoscale(channel)
    except IndexError:
        pass
    except ValueError:
        pass

def scope_measure():
    input_Vrms = float(scope_query(":MEASURE:VRMS? CHAN1"))
    output_Vrms = float(scope_query(":MEASURE:VRMS? CHAN2"))
    phase_deg = float(scope_query(":MEASURE:PHASE? CHAN1, CHAN2"))
    input_dBV = 20*log10(input_Vrms)
    output_dBV = 20*log10(output_Vrms)
    gain_dB = output_dBV - input_dBV
    return {
        "input_dBV": input_dBV,
        "output_dBV": output_dBV,
        "gain_dB": gain_dB,
        "phase_deg": phase_deg,
    }

def set_generator_frequency_Hz(frequency_Hz):
    scope_write(f":WGEN:FREQUENCY {frequency_Hz:.2e}")

def set_generator_voltage_dBV(voltage_dBV):
    voltage_Vrms = 10**(voltage_dBV/20)
    voltage_Vpp = 2 * sqrt(2) * voltage_Vrms
    scope_write(f":WGEN:VOLTAGE {voltage_Vpp:.2e}")

def analyze(records):
    import matplotlib.pyplot as plt
    x = [_r["input_dBV"] for _r in records]
    y = [_r["gain_dB"] for _r in records]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(x, y, "k.-")
    ax.set_xlabel("Input voltage [dBV]")
    ax.set_ylabel("Gain [dB]")
    ax.yaxis.set_major_locator(plt.MultipleLocator(1))
    ax.grid(True, "both", "both")
    fig.tight_layout()
    fig.savefig(filelabel + ".png")
    plt.show()

def main():
    print(scope.get_id())
    frequency_Hz = 300
    V_step_dB = 1
    V_start_dBV = -60
    V_stop_dBV = 0
    set_generator_frequency_Hz(frequency_Hz)

    records = []
    voltage_dBV = V_start_dBV

    while voltage_dBV <= V_stop_dBV:
        set_generator_voltage_dBV(voltage_dBV)
        scope_autoscale(1)
        scope_autoscale(2)
        meas = scope_measure()
        record = {
            "generator_Hz": frequency_Hz,
            "generator_dBV": voltage_dBV,
            **meas,
        }
        output.write(record)
        print(record)
        records.append(record)
        voltage_dBV += V_step_dB

    set_generator_voltage_dBV(V_start_dBV)
    analyze(records)

if __name__ == "__main__":
    main()

