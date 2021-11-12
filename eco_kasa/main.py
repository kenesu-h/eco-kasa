from argparse import ArgumentParser, Action, Namespace
from enum import Enum
from io import TextIOWrapper
from kasa import Discover, SmartDevice, SmartDeviceException
from pathlib import Path
from tabulate import tabulate
from typing import Dict, List, Optional
import asyncio, json, netifaces, nmap, platform, subprocess

class Operation(Enum):
  TurnOn = "turn_on"
  TurnOff = "turn_off"
  ListDevices = "list"
  SetAlias = "set_alias"
  Update = "update"
  UpdateOne = "update_one"

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
  elif as_lower == Operation.UpdateOne.value:
    return Operation.UpdateOne
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

  parser_update_one: ArgumentParser = subparsers.add_parser("update_one")
  parser_update_one.add_argument(
    "target", type=str,
    help="The target smart device. Can be either the device's IP or its alias."
  )

  return parser

class Config:
  def __init__(self, targets: List[str]) -> None:
    self.__targets: List[str] = targets

  def get_targets(self) -> List[str]:
    return self.__targets

  def as_dict(self) -> Dict[str, List[str]]:
    as_dict: Dict[str, List[str]] = {}
    as_dict["target"] = self.__targets
    return as_dict

def config_default() -> Config:
  return Config([])

def config_from_dict(d: Dict[str, List[str]]) -> Config:
  return Config(d["target"])

class Application:
  def __init__(self) -> None:
    self.__config: Config = self.load_config()
    self.__devices: Dict[str, SmartDevice] = {}
    self.discover_devices_config()

  def load_config(self) -> Config:
    if Path("./config.json").is_file():
      file: TextIOWrapper = open("./config.json", "r")
      return Config(json.load(file)["targets"])
    else:
      print("No config.json found, writing a new one.")
      file: TextIOWrapper = open("./config.json", "w")
      json.dump(config_default().as_dict(), file)
      print(
        "Config written. Please edit it with your target IPs and/or aliases."
        + " and rerun the script."
      )
      exit()

  def discover_devices_config(self) -> None:
    for target in self.__config.get_targets():
      try:
        self.__devices[target] = asyncio.run(Discover.discover_single(target))
      except SmartDeviceException:
        print(
          "Was unable to create a smart device from target "
          + target + ", skipping."
        )
        pass

  def discover_devices_nmap(self) -> None:
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

    for host in nm.all_hosts():
      try:
        self.__devices[host] = asyncio.run(Discover.discover_single(host))
      except SmartDeviceException:
        print(
          "Was unable to create a smart device from host "
          + host + ", skipping."
        )
        pass

  def get_device(self, target: str) -> Optional[SmartDevice]:
    """
    Retrieves a device corresponding with the given target. The target can either
    be the device's IP or alias.
    """
    if target in self.__devices:
      return self.__devices[target]
    else:
      for _, device in self.__devices.items():
        if target == device.alias:
          return device
      return None

  def try_turn_on(self, target: str) -> None:
    """ Attempts to turn on the target device. """
    maybe_device: Optional[SmartDevice] = self.get_device(target)
    if maybe_device == None:
      print("No devices with the given IP or alias were found.")
    else:
      maybe_device: SmartDevice
      if maybe_device.is_off:
        asyncio.run(maybe_device.turn_on())

  def try_turn_off(self, target: str) -> None:
    """ Attempts to turn off the target device. """
    maybe_device: Optional[SmartDevice] = self.get_device(target)
    if maybe_device == None:
      print("No devices with the given IP or alias were found.")
    else:
      maybe_device: SmartDevice
      if maybe_device.is_on:
        asyncio.run(maybe_device.turn_off())

  def list_devices(self) -> None:
    """ Lists all devices out in a simple table. """
    table: List[List[str]] = []
    for addr, device in self.__devices.items():
      table.append([addr, device.alias, str(device.is_on)])
    print(tabulate(table, ["IP", "Alias", "Is on?"]))

  def try_set_alias(self, target: str, new_alias: str) -> None:
    """ Attempts to set the alias of the target device. """
    maybe_device: Optional[SmartDevice] = self.get_device(target)
    if maybe_device == None:
      print("No devices with the given IP or alias were found.")
    else:
      maybe_device: SmartDevice
      asyncio.run(maybe_device.set_alias(new_alias))

  def computer_has_internet(self):
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

  def try_update(self) -> None:
    if self.computer_has_internet():
      for _, device in self.__devices.items():
        if device.is_off:
          asyncio.run(device.turn_on())
    else:
      for _, device in self.__devices.items():
        if device.is_on:
          asyncio.run(device.turn_off()) 

  def try_update_one(self, target: str) -> None:
    maybe_device: Optional[SmartDevice] = self.get_device(target)
    if maybe_device == None:
      print("No devices with the given IP or alias were found.")
    else:
      maybe_device: SmartDevice
      if self.computer_has_internet():
        if maybe_device.is_off:
          asyncio.run(maybe_device.turn_on())
      else:
        if maybe_device.is_on:
          asyncio.run(maybe_device.turn_on())

def main():
  app: Application = Application()
  args: Namespace = init_parser().parse_args()
  if args.operation == Operation.TurnOn.value:
    app.try_turn_on(args.target)
  elif args.operation == Operation.TurnOff.value:
    app.try_turn_off(args.target)
  elif args.operation == Operation.ListDevices.value:
    app.list_devices()
  elif args.operation == Operation.SetAlias.value:
    app.try_set_alias(args.target, args.new_alias)
  elif args.operation == Operation.Update.value:
    app.try_update()
  elif args.operation == Operation.UpdateOne.value:
    app.try_update_one(args.target)