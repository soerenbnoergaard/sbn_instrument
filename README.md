# sbn_instrument
Python drivers for various electronics test equipment.

Organized as a python module for easy use as a git submodule.
No setuptool package is created yet.

To use the module:
1. Clone it to a path, e.g. `/opt/python_modules/sbn_instrument`.
2. Add the path, e.g. `/opt/python_modules/`, to the `PYTHONPATH` environment variable.
3. Now, it should be possible to import it.

## Linux setup

Add the user to the `dialout` group:

    sudo usermod -a -G dialout $USER

Udev rules to add specific USB devices to the `dialout` group (`/etc/udev/rules.d/99-sbn_instrument.rules`):

    # Brymen BM869s
    SUBSYSTEM=="usb", ATTR{idVendor}=="0820", ATTR{idProduct}=="0001", MODE="0660", GROUP="dialout"

    # Keysight DSOX1102G
    SUBSYSTEM=="usb", ATTR{idVendor}=="2a8d", ATTR{idProduct}=="1797", MODE="0660", GROUP="dialout"
