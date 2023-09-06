# ftdi-spi-prog

A little script that turns an FT2232H into a SPI flash programmer.

Great for reprogramming configuration SPI flash chips, especially for FPGAs.

There's two scripts:

* `gpio_ctrl.py` - for controlling only the IO sideband (`RESET_L` and `CDONE`)
* `ftdi_spi_prog.py` - omnibus sideband control, and `flashrom` wrapper. Be advised - there is timing weirdness with the `subprocess` interaction with `flashrom`.
