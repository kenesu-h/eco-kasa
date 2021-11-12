from argparse import ArgumentParser, Action, Namespace
from enum import Enum
from kasa import Discover, SmartDevice, SmartDeviceException
from tabulate import tabulate
from typing import Dict, List, Optional
import asyncio, netifaces, nmap, platform, subprocess

class Operation(Enum):
  TurnOn = "turn_on"
  TurnOff = "turn_off"
  ListDevices = "list"
  SetAlias = "set_alias"
  Update = "update"

def operation_from_str(s: str) -> Optional[Operation]:
  """ Returns an operation from the corresponding string. """
  as_lower: str = s.lower()
  if as_lower == Operation.TurnOn.value:
    return Operation.TurnOn
  elif as_lower == Operation.TurnOff.value:
    return Operation.TurnOff
  elif as_lower == Operation.ListDevices.value:
    return Operation.ListDevices
  elif as_lower == Operation.SetAlias.value:
    return Operation.SetAlias
  elif as_lower == Operation.Update.value:
    return Operation.Update
  else:
    return None

def init_parser() -> ArgumentParser:
  """ Initializes the argument parser. """
  parser: ArgumentParser = ArgumentParser(
    description="A command line application for remotely powering on or off Kasa"
      + " smart devices."
  )
  subparsers: Action = parser.add_subparsers(
    dest="operation",
    help="The operation to perform. Must be one of:"
      + " \"turn_on\", \"turn_off\", \"list\", \"set_alias\", or \"update\"."
  )
  subparsers.required = True

  parser_turn_on: ArgumentParser = subparsers.add_parser("turn_on")
  parser_turn_on.add_argument(
    "target", type=str,
    help="The target smart device. Can be either the device's IP or its alias."
  )

  parser_turn_off: ArgumentParser = subparsers.add_parser("turn_off")
  parser_turn_off.add_argument(
    "target", type=str,
    help="The target smart device. Can be either the device's IP or its alias."
  )
  
  subparsers.add_parser("list")

  parser_set_alias: ArgumentParser = subparsers.add_parser("set_alias")
  parser_set_alias.add_argument(
    "target", type=str,
    help="The target smart device. Can be either the device's IP or its alias."
  )
  parser_set_alias.add_argument(
    "new_alias", type=str,
    help="The new alias to set to."
  )

  subparsers.add_parser("update")

  return parser

def discover_devices_nmap() -> Dict[str, SmartDevice]:
  """
  Discovers the devices that exist on the local network, but using nmap instead
  since python-kasa's implementation of discovery doesn't work too well...
  """
  # Borrowed this part from https://stackoverflow.com/questions/2761829/python-get-default-gateway-for-a-local-interface-ip-address-in-linux/6556951
  default_gateway: str = netifaces.gateways()["default"][netifaces.AF_INET][0]
  parts: List[str] = default_gateway.split(".")
  parts[-1] = str(0)
  to_check: str = ".".join(parts) + "/24"

  # Borrowing this from python-nmap's documentation
  nm: nmap.PortScanner = nmap.PortScanner()
  print("Currently scanning the network using nmap...")
  nm.scan(to_check, arguments = "-sn")
  print("Finished scanning.")

  devices: Dict[str, SmartDevice] = {}
  for host in nm.all_hosts():
    try:
      devices[host] = asyncio.run(Discover.discover_single(host))
    except SmartDeviceException:
      pass
  return devices

def get_device(
  target: str, devices: Dict[str, SmartDevice]
) -> Optional[SmartDevice]:
  """
  Retrieves a device corresponding with the given target. The target can either
  be the device's IP or alias.
  """
  if target in devices:
    return devices[target]
  else:
    for _, device in devices.items():
      if target == device.alias:
        return device
    return None

def try_turn_on(target: str) -> None:
  """ Attempts to turn on the target device. """
  maybe_device: Optional[SmartDevice] = get_device(
    target,
    discover_devices_nmap()
  )
  if maybe_device == None:
    print("No devices with the given IP or alias were found.")
  else:
    maybe_device: SmartDevice
    if maybe_device.is_off:
      asyncio.run(maybe_device.turn_on())

def try_turn_off(target: str) -> None:
  """ Attempts to turn off the target device. """
  maybe_device: Optional[SmartDevice] = get_device(
    target,
    discover_devices_nmap()
  )
  if maybe_device == None:
    print("No devices with the given IP or alias were found.")
  else:
    maybe_device: SmartDevice
    if maybe_device.is_on:
      asyncio.run(maybe_device.turn_off())

def list_devices() -> None:
  """ Lists all devices out in a simple table. """
  devices: Dict[str, SmartDevice] = discover_devices_nmap()
  table: List[List[str]] = []
  for addr, device in devices.items():
    table.append([addr, device.alias, str(device.is_on)])
  print(tabulate(table, ["IP", "Alias", "Is on?"]))

def try_set_alias(target: str, new_alias: str) -> None:
  """ Attempts to set the alias of the target device. """
  maybe_device: Optional[SmartDevice] = get_device(
    target,
    discover_devices_nmap()
  )
  if maybe_device == None:
    print("No devices with the given IP or alias were found.")
  else:
    maybe_device: SmartDevice
    asyncio.run(maybe_device.set_alias(new_alias))

def computer_has_internet():
  """
  Pings Google's servers to see if this computer has an Internet connection.
  """
  # Borrowed from https://stackoverflow.com/questions/2953462/pinging-servers-in-python 
  response: int = subprocess.call(
    [
      "ping",
      ("-n" if platform.system().lower() == "windows" else "-c"),
      "1",
      "8.8.8.8"
    ],
    stdout = subprocess.DEVNULL,
    stderr = subprocess.STDOUT
  )
  return response == 0

def try_update() -> None:
  devices: Dict[str, SmartDevice] = discover_devices_nmap()
  if computer_has_internet():
    for _, device in devices.items():
      if device.is_off:
        asyncio.run(device.turn_on())
  else:
    for _, device in devices.items():
      if device.is_on:
        asyncio.run(device.turn_off()) 

def main():
  args: Namespace = init_parser().parse_args()
  if args.operation == Operation.TurnOn.value:
    try_turn_on(args.target)
  elif args.operation == Operation.TurnOff.value:
    try_turn_off(args.target)
  elif args.operation == Operation.ListDevices.value:
    list_devices()
  elif args.operation == Operation.SetAlias.value:
    try_set_alias(args.target, args.new_alias)
  elif args.operation == Operation.Update.value:
    try_update()