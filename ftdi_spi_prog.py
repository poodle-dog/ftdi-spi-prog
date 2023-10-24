import argparse 
import subprocess 
import sys 
import time 

from pyftdi.gpio import GpioAsyncController
from pyftdi.spi import SpiController
from spiflash.serialflash import SerialFlashManager

IO_RST_L  = 0x10 # Mask corresponding to port b, pin 4
IO_CDONE  = 0x40 # Mask corresponding to port b, pin 6

parser = argparse.ArgumentParser()

parser.add_argument("url", type=str, help="URL of FTDI device")
parser.add_argument("binfile", type=str, help="URL of FTDI device")
parser.add_argument("--verbose", "-v", action='store_true')

def find_flash(verbose, flash_pn="MX25L1606E"):
    """
    searches for flash chips via subprocess call to Flashrom
    """
    find_command = [
        "flashrom",
        "-p",
        "ft2232_spi:type=2232H,port=A,divisor=64",
    ]

    if verbose:
        print(f'$ {" ".join(find_command)}')

    ret = None

    if verbose:
        ret = subprocess.run(
            find_command,
            capture_output=True,
            timeout=5
        )
        print(vars(ret))
        # always returns True in verbose mode; on user to know flash cfg
        return True
    else:
        ret = subprocess.run(
            find_command,
            capture_output=True,
            timeout=5
        )
        output = str(ret.stdout).split('\n')
        for line in output:
            if line.startswith("Found") and flash_pn in line:
                print(line)
                return True

    return False


def program_flash(binfile, verbose):
    """
    programs for flash chips via subprocess call to Flashrom
    """
    prog_command = [
        "flashrom",
        "-p",
        "ft2232_spi:type=2232H,port=A,divisor=16",
        "-c",
        "MX25L1605A/MX25L1606E/MX25L1608E",
        "-w",
    ]

    prog_command.append(binfile)

    if verbose:
        print(f'$ {" ".join(prog_command)}')

    ret = subprocess.run(prog_command, capture_output=True)

    if verbose:
        print(vars(ret))



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
    """
    1. configure GPIO system
    1. assert FPGA reset. 
    2. enable level translator.
    3. program FPGA SPI flash.
    4. disable level translator.
    5. deassert FPGA reset.
    6. check CDONE Pin for program success/failure. 
    """
    if args.verbose:
        print(args)

    if not args.url.endswith("/2"):
        sys.exit("Requires device /2 of FTDI to work properly. Exiting.")

    # Configure all IO as inputs, except IO_RST_L, which is output
    gpio = GpioAsyncController()
    gpio.configure(args.url, direction=(0x00 | IO_RST_L))

    assert_fpga_reset(gpio)

    time.sleep(1)

    # Reprogram flash if program can find it 
    if find_flash(args.verbose):
        program_flash(args.binfile, args.verbose)
        print("Flash has been reprogrammed.")
        time.sleep(1)
    else:
        print("No flash found - releasing FPGA from reset.")
    

    # Grabs device /1 of FTDI module, configures as GPIO inputs / Hi-Z
    #   Needed to allow FPGA to latch in its boot config settings properly
    gpio_spi = GpioAsyncController()
    gpio_spi.configure(args.url.rstrip('/2') + '/1', direction=0x00)
    time.sleep(1)

    # Deasserts FPGA reset; sleeps to wait for FPGA to boot up
    deassert_fpga_reset(gpio)
    time.sleep(0.2)

    if check_cdone(gpio):
        print("FPGA configured successfully!")
    else:
        print("FPGA configuration failure; check bitstream")

if __name__ == "__main__":
    args = parser.parse_args()
    main(args)

