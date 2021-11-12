# eco-kasa
A command line application intended for personal use in automatically powering on
or off Kasa smart devices in response to an Internet connection.

# Installation
This uses [Poetry](https://python-poetry.org/) for dependency management. You can
either install Poetry to ensure this works - and to isolate it and its
dependencies - or you can just install the main dependencies and run it directly.

## Prerequisites
You need:
- a Git installation.
- a [Poetry](https://python-poetry.org/) installation.
- an nmap installation.

## Instructions
1. Clone the Git repo.
2. Run `poetry install` inside the repo's directory.

# Usage
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