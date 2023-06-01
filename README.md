# Pyomnilogic Local

<p align="center">
  <a href="https://pypi.org/project/python-omnilogic-local/">
    <img src="https://img.shields.io/pypi/v/python-omnilogic-local.svg?logo=python&logoColor=fff&style=flat-square" alt="PyPI Version">
  </a>
  <img src="https://img.shields.io/pypi/pyversions/python-omnilogic-local.svg?style=flat-square&logo=python&amp;logoColor=fff" alt="Supported Python versions">
  <img src="https://img.shields.io/pypi/l/python-omnilogic-local.svg?style=flat-square" alt="License">
  <a href="https://www.buymeacoffee.com/cryptk" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 20px !important;" ></a>
</p>

A library implementing the UDP XML Local Control api for Hayward OmniLogic and OmniHub pool controllers

## Installation

This package is published to pypi at https://pypi.org/project/python-omnilogic-local/:

`pip install python-omnilogic-local`

## Functionality

This library is still under development and is not yet able to control every function of a Hayward pool controller.  The implemented functionality is:

- Pulling the MSP Config
- Polling telemetry
- Polling a list of active alarms
- Polling filter/pump diagnostic information
- Polling the logging configuration
- Setting pool heater temperature
- Turning pool heaters on/off
- Turning other pool equipment on/off, including countdown timers
- Setting filter/pump speed
- Controlling ColorLogic lights including brightness, speed, and selected shows, with support for countdown timers

If your controller has functionality outside of this list, please do not hesitate to [Open an Issue](https://github.com/cryptk/python-omnilogic-local/issues)

## Credits

The work on this library would not have been possible without the efforts of [djtimca](https://github.com/djtimca/) and [John Sutherland](garionphx@gmail.com)
