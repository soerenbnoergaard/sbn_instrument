import time
import sbn_instrument

scope = sbn_instrument.oscilloscope.KeysightDsox1102G("/dev/usbtmc0")
print(scope.get_id())
scope.save_screenshot_png(time.strftime("%Y-%m-%d_%H%M%S") + "_screenshot.png")
