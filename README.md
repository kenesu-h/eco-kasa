# eco-kasa
A command line application intended for personal use in automatically powering on
or off Kasa smart devices in response to an Internet connection.

# Installation
This uses [Poetry](https://python-poetry.org/) for dependency management. You
should probably install it to ensure that its Python version and dependencies are
isolated on your system.

## Prerequisites
You need:
- a Git installation.
- a [Poetry](https://python-poetry.org/) installation.
- an nmap installation.

## Instructions
1. Clone eco-kasa's Git repo.
2. Run `poetry install` inside eco-kasa's directory.
3. Wait until the installation is done.

# Usage

## Prerequisites
- Kasa smart plugs connected to the same Internet connection as your computer.
  - Go to [Smart Plug Setup](./docs/smart-plug-setup.md) for some instructions on
    this.

## Instructions
Run the script using `poetry run main <operation>` inside the repo directory.

`<operation>` can be any one of:
- `turn_on <target>`
  - Turns on the smart device with the target IP or alias.
  - `<target>` must be the IP or alias of the device you want to turn on.
- `turn_off <target>`
  - Same as above, but it turns the device off.
- `list`
  - Lists out all the smart devices currently found on the network.
- `set_alias <target> <new_alias>`
  - Sets the alias of the smart device with the target IP or alias to a new
    alias.
  - `<target>` must be the IP or alias of the device you want to set.
  - `<new_alias>` is the new alias to set to.
- `update`
  - Updates all smart devices on the network. Turns them off if there is no
    Internet connection on this computer, and turns them on if there is.

## Possible Issues
- You may have to use `kasa --host <IP of your smart plug>` to get it to show up
  when using `poetry run main list`.