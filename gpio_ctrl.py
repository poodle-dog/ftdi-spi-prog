import argparse 
import sys 

from pyftdi.gpio import GpioAsyncController

IO_CDONE  = 0x10 # Mask corresponding to port b, pin 4
IO_RST_L  = 0x20 # Mask corresponding to port b, pin 5

parser = argparse.ArgumentParser()

parser.add_argument("url", type=str, help="URL of FTDI device")
parser.add_argument(
        "action", 
        type=str, 
        choices=['done', 'reset', 'run'], 
        help="Action to execute"
)
parser.add_argument("--verbose", "-v", action='store_true')

def assert_fpga_reset(gpio):
    """
    sets IO_RST_L low to hold FPGA in reset
    """
    portval = gpio.read()
    portval = (portval & ~IO_RST_L)
    gpio.write(portval)

def deassert_fpga_reset(gpio):
    """
    sets IO_RST_L high to release FPGA from reset
    """
    portval = gpio.read()
    portval = (portval | IO_RST_L)
    gpio.write(portval)


def check_cdone(gpio):
    """
    reads IO_CDONE; 
    if high, return True  (FPGA configured succesfully)
    if low , return False (FPGA configuration failure)
    """
    portval = gpio.read()
    portval = (portval & IO_RST_L)
    if portval:
        return True
    else:
        return False

def main(args):
    if args.verbose:
        print(args)

    if not args.url.endswith("/2"):
        sys.exit("Requires device /2 of FTDI to work properly. Exiting.")

    # Configure all IO as inputs, except IO_RST_L, which is output
    gpio = GpioAsyncController()
    gpio.configure(args.url, direction=0x00)

    if args.action == 'done':
        if check_cdone(gpio):
            print("FPGA is configured.")
        else:
            print("FPGA not configured;")
    elif args.action == 'reset':
        gpio.set_direction(IO_RST_L, direction=(0x00 | IO_RST_L))
        assert_fpga_reset(gpio)
    elif args.action == 'run':
        gpio.set_direction(IO_RST_L, direction=(0x00 | IO_RST_L))
        deassert_fpga_reset(gpio)
        gpio.set_direction(IO_RST_L, direction=0x00)
    
    del gpio


if __name__ == "__main__":
    args = parser.parse_args()
    main(args)

