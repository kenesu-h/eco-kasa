# eco-kasa
A command line application for powering on or off Kasa smart devices.

# Installation & Usage
This uses [Poetry](https://python-poetry.org/) for dependency management. You can
either install Poetry to ensure this works - and to isolate it and its
dependencies - or you can just install the main dependencies and run it directly.

# With Poetry
1. Clone the Git repo.
2. Run `poetry install` inside the repo's directory.
3. Similarly, run `poetry run python -m rpi_kasa_power.main <alias> <to_power>`.
  - `<alias>` must be the alias of the target device.
  - `<to_power>` must be either `true` or `false`.

# Without Poetry
A Python installation with a version of at least 3.7 is required.

1. Clone the Git repo.
2. Using `pip`, install `python-kasa` and `tabulate`.
3. Run `python -m rpi_kasa_power.main <alias> <to_power>` inside the repo's
   directory.
  - `<alias>` must be the alias of the target device.
  - `<to_power>` must be either `true` or `false`.