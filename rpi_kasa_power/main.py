from argparse import ArgumentParser
from kasa import Discover, SmartDevice, SmartDeviceException
from tabulate import tabulate
from typing import Dict, List, Optional, Tuple
import asyncio, netifaces, nmap

def init_parser() -> ArgumentParser:
  """ Initializes the argument parser. """
  parser = ArgumentParser(
    description="A command line application for remotely powering on or off Kasa"
      + " smart devices."
  )

  parser.add_argument(
    "alias", type=str,
    help="The alias of the device to power on or off."
  )

  parser.add_argument(
    "to_power", type=str,
    help="Must be one of either \"true\" or \"false\". Decides whether to power"
      + " the target device on or off."
  )

  return parser

def discover_devices() -> Dict[str, SmartDevice]:
  """ Discovers the devices that exist on the local network. """
  devices: Dict[str, SmartDevice] = asyncio.run(Discover.discover())
  for _, device in devices.items():
    asyncio.run(device.update())
  return devices

def discover_devices_nmap() -> Dict[str, SmartDevice]:
  """
  Discovers the devices that exist on the local network, but using nmap instead
  since python-kasa's implementation of discovery doesn't work too well...
  """
  # Borrowed this part from https://stackoverflow.com/questions/2761829/python-get-default-gateway-for-a-local-interface-ip-address-in-linux/6556951
  default_gateway: str = netifaces.gateways()["default"][netifaces.AF_INET][0]
  parts: List[str] = default_gateway.split(".")
  parts[-1] = str(0)
  to_check: str = ".".join(parts)

  # Borrowing this from python-nmap's documentation
  nm: nmap.PortScanner = nmap.PortScanner
  nm.scan(hosts=to_check + "/" + str(24))

  devices: List[SmartDevice] = [] 
  for host in nm.all_hosts():
    try:
      devices.append(asyncio.run(Discover.discover_single(host)))
    except SmartDeviceException:
      pass
  return devices

def device_by_alias(
  alias: str, devices: Dict[str, SmartDevice]
) -> Optional[SmartDevice]:
  """ Retrieves a device by some given alias. """
  for _, device in devices.items():
    if device.alias == alias:
      return device
  return None

def print_devices(devices: Dict[str, SmartDevice]) -> None:
  """ Prints all devices out in a simple table. """
  table: List[List[str]] = []
  for addr, device in devices.items():
    table.append([addr, device.alias, str(device.is_on)])
  print(tabulate(table, ["IP", "Alias", "Is on?"]))

def try_device_on(device: SmartDevice) -> None:
  """ Attempts to turn the device on, but will fail if it's already on. """
  if device.is_on:
    print("The device is already on.")
  else:
    asyncio.run(device.turn_on())

def try_device_off(device: SmartDevice) -> None:
  """ Attempts to turn the device off, but will fail if it's already off. """
  if device.is_off:
    print("The device is already off.")
  else:
    asyncio.run(device.turn_off())

if __name__ == "__main__":
  parser: ArgumentParser = init_parser()
  args: vars = vars(parser.parse_args())

  alias: str = args.get("alias")
  to_power: bool = args.get("to_power")

  devices: Dict[str, SmartDevice] = discover_devices_nmap()
  maybe_device: Optional[SmartDevice] = device_by_alias(alias, devices)

  if maybe_device == None:
    print("No devices with the following alias were found.")
    if len(devices) > 0:
      response: str = input(
        "Would you like a list of the devices found on the network? (y/n)"
      )
      if response.lower() == "y":
        print_devices(devices)
  else:
    maybe_device: SmartDevice
    if to_power:
      try_device_on(maybe_device)
    else:
      try_device_off(maybe_device)