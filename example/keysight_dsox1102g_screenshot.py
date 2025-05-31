import time
import sys
import sbn_instrument

scope = sbn_instrument.oscilloscope.KeysightDsox1102G("/dev/usbtmc0")
print(scope.get_id())
if len(sys.argv) >= 2:
    filename = time.strftime("%Y-%m-%d_%H%M%S") + "_screenshot_" + sys.argv[1] + ".png"
else:
    filename = time.strftime("%Y-%m-%d_%H%M%S") + "_screenshot.png"
scope.save_screenshot_png(filename)
scope.get_id() # Read ID a second time to avoid the "query interrupted" for whatever reason

