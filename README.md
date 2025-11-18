<div align="center">

# Python OmniLogic Local

[![PyPI Version](https://img.shields.io/pypi/v/python-omnilogic-local.svg?logo=python&logoColor=fff&style=flat-square)](https://pypi.org/project/python-omnilogic-local/)
![Python Version](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fcryptk%2Fpython-omnilogic-local%2Frefs%2Fheads%2Fmain%2Fpyproject.toml?style=flat-square)
[![Tests](https://img.shields.io/github/actions/workflow/status/cryptk/python-omnilogic-local/ci-testing.yml?style=flat-square&label=Tests)](https://github.com/cryptk/python-omnilogic-local/actions)
[![License](https://img.shields.io/github/license/cryptk/python-omnilogic-local?style=flat-square)](LICENSE)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy_Me_A_Coffee-FFDD00?style=flat-square&logo=buy-me-a-coffee&logoColor=000)](https://www.buymeacoffee.com/cryptk)

**A modern Python library for local control of Hayward OmniLogic and OmniHub pool controllers**

[Features](#features) • [Installation](#installation) • [Quick Start](#quick-start) • [Documentation](#documentation) • [CLI Tool](#cli-tool)

</div>

---

## Overview

Python OmniLogic Local provides complete local control over Hayward OmniLogic and OmniHub pool automation systems using their UDP-based XML protocol. Built with modern Python 3.12+, comprehensive type hints, and Pydantic validation, this library offers a async, type-safe interface for pool automation.

## Features

### Equipment Control
- **Heaters**: Temperature control, mode selection (heat/auto/off), solar support
- **Pumps & Filters**: Variable speed control, on/off operation, diagnostic information
- **ColorLogic Lights**: Multiple models supported (2.5, 4.0, UCL, SAM), brightness, speed, show selection
- **Relays**: Control auxiliary equipment like fountains, deck jets, blowers
- **Chlorinators**: Timed percent control, enable/disable operation
- **Groups**: Coordinated equipment control (turn multiple devices on/off together)
- **Schedules**: Enable/disable automated schedules

### Monitoring & State Management
- **Real-time Telemetry**: Water temperature, chemical readings, equipment state
- **Configuration Discovery**: Automatic detection of all equipment and capabilities
- **Sensor Data**: pH, ORP, TDS, salt levels, flow sensors
- **Filter Diagnostics**: Last speed, valve positions, priming states
- **Equipment Hierarchy**: Automatic parent-child relationship tracking

### Developer-Friendly Design
- **Type Safety**: Comprehensive type hints with strict mypy validation
- **Async/Await**: Non-blocking asyncio-based API
- **Pydantic Models**: Automatic validation and serialization
- **Smart State Management**: Automatic dirty tracking and efficient refreshing
- **Equipment Collections**: Dict-like and attribute access patterns
- **Generic Architecture**: Type-safe equipment hierarchy with generics

## Installation

**Requirements**: Python 3.12 or higher

```bash
pip install python-omnilogic-local
```

**With CLI tools** (includes packet capture utilities):
```bash
pip install python-omnilogic-local[cli]
```

## Quick Start

### Basic Usage

```python
import asyncio
from pyomnilogic_local import OmniLogic

async def main():
    # Connect to your OmniLogic controller
    omni = OmniLogic("192.168.1.100")

    # Initial refresh to load configuration and state
    await omni.refresh()

    # Access equipment by name
    pool = omni.backyard.bow["Pool"]

    # Control heater
    heater = pool.heater
    print(f"Current temperature: {heater.current_temperature}°F")
    print(f"Target temperature: {heater.current_set_point}°F")

    await heater.set_temperature(85)
    await heater.turn_on()

    # Refresh to get updated state
    await omni.refresh()

    # Control lights
    from pyomnilogic_local.omnitypes import ColorLogicBrightness, ColorLogicSpeed

    light = pool.lights["Pool Light"]
    await light.turn_on()
    await light.set_show(
        show=light.effects.TWILIGHT,
        brightness=ColorLogicBrightness.ONE_HUNDRED_PERCENT,
        speed=ColorLogicSpeed.ONE_TIMES
    )

    # Control pump speed
    pump = pool.pumps["Pool Pump"]
    await pump.set_speed(75)  # Set to 75%

asyncio.run(main())
```

### Monitoring Equipment State

```python
async def monitor_pool():
    omni = OmniLogic("192.168.1.100")
    await omni.refresh()

    pool = omni.backyard.bow["Pool"]

    # Check multiple equipment states
    print(f"Water temperature: {pool.heater.current_temperature}°F")
    print(f"Heater is {'on' if pool.heater.is_on else 'off'}")
    print(f"Pump speed: {pool.pumps['Main Pump'].current_speed}%")

    # Check all lights
    for name, light in pool.lights.items():
        if light.is_on:
            print(f"{name}: {light.show.name} @ {light.brightness.name}")
        else:
            print(f"{name}: OFF")

    # Access chemical sensors
    if pool.sensors:
        for name, sensor in pool.sensors.items():
            print(f"{name}: {sensor.current_reading}")

asyncio.run(monitor_pool())
```

### Efficient State Updates

The library includes intelligent state management to minimize unnecessary API calls:

```python
# Force immediate refresh
await omni.refresh(force=True)

# Refresh only if data is older than 30 seconds
await omni.refresh(if_older_than=30.0)

# Refresh only if equipment state changed (default after control commands)
await omni.refresh(if_dirty=True)
```

## Documentation

### Equipment Hierarchy

```
OmniLogic
├── Backyard
│   ├── Bodies of Water (BOW)
│   │   ├── Heater (single virtual heater)
│   │   ├── Pumps
│   │   ├── Filters
│   │   ├── Chlorinator
│   │   ├── Lights (ColorLogic)
│   │   ├── Relays
│   │   ├── Sensors
│   │   └── CSAD (Chemical Sensing & Dispensing)
│   ├── Lights (ColorLogic)
│   ├── Relays
│   └── Sensors
├── Groups
└── Schedules
```

### Accessing Equipment

Equipment can be accessed using dictionary-style or attribute-style syntax:

```python
# Dictionary access (by name)
pool = omni.backyard.bow["Pool"]

# Heater is a single object (not a collection)
heater = pool.heater

# Most equipment are collections
for pump_name, pump in pool.pumps.items():
    print(f"Pump: {pump_name} - Speed: {pump.current_speed}%")

# Lights, relays, and sensors can be on both BOW and backyard levels
for light_name, light in pool.lights.items():
    print(f"BOW Light: {light_name}")

for light_name, light in omni.backyard.lights.items():
    print(f"Backyard Light: {light_name}")

# Groups and schedules are at the OmniLogic level
for group_name, group in omni.groups.items():
    print(f"Group: {group_name}")
```

### Equipment Properties

All equipment exposes standard properties:

```python
equipment.name           # Equipment name
equipment.system_id      # Unique system identifier
equipment.bow_id         # Body of water ID (if applicable)
equipment.is_ready       # Whether equipment can accept commands
equipment.mspconfig      # Configuration data
equipment.telemetry      # Real-time state data
```

### Control Methods

Control methods are async and automatically handle readiness checks:

```python
from pyomnilogic_local.omnitypes import ColorLogicBrightness, ColorLogicSpeed

# All control methods are async
await heater.turn_on()
await heater.turn_off()
await heater.set_temperature(85)

# Light show control - brightness and speed are parameters to set_show()
await light.set_show(
    show=light.effects.CARIBBEAN,
    brightness=ColorLogicBrightness.EIGHTY_PERCENT,
    speed=ColorLogicSpeed.TWO_TIMES
)

# Pump speed control
await pump.set_speed(75)

# State is automatically marked dirty after control commands
# Refresh to get updated telemetry
await omni.refresh()
```

### Exception Handling

The library provides specific exception types:

```python
from pyomnilogic_local import (
    OmniLogicLocalError,          # Base exception
    OmniEquipmentNotReadyError,   # Equipment in transitional state
    OmniEquipmentNotInitializedError,  # Missing required attributes
    OmniConnectionError,          # Network/communication errors
)

try:
    await heater.set_temperature(120)  # Too high
except OmniValidationException as e:
    print(f"Invalid temperature: {e}")

try:
    await light.turn_on()
except OmniEquipmentNotReadyError as e:
    print(f"Light not ready: {e}")
```

## CLI Tool

The library includes a command-line tool for monitoring and debugging:

```bash
# Get telemetry data
omnilogic --host 192.168.1.100 debug get-telemetry

# List all equipment
omnilogic get lights
omnilogic get pumps
omnilogic get heaters

# Get raw XML responses
omnilogic debug --raw get-mspconfig

# View filter diagnostics
omnilogic debug get-filter-diagnostics
```

**Installation with CLI tools**:
```bash
pip install python-omnilogic-local[cli]
```

## Supported Equipment

### Fully Supported
- Pool/Spa Heaters (gas, heat pump, solar, hybrid)
- Variable Speed Pumps & Filters
- ColorLogic Lights (2.5, 4.0, UCL, SAM models)
- Relays (water features, auxiliary equipment)
- Chlorinators (timed percent control)
- Sensors (temperature, pH, ORP, TDS, salt, flow)
- Groups (coordinated equipment control)
- Schedules (enable/disable)
- CSAD (Chemical Sensing & Dispensing) - monitoring

### Partial Support
- CSAD equipment control (monitoring only currently)
- Some advanced heater configurations

> [!NOTE]
> If your controller has equipment not listed here, please [open an issue](https://github.com/cryptk/python-omnilogic-local/issues) with details about your configuration.

## Development

This project uses modern Python tooling:

- **Python**: 3.12+ with type hints
- **Type Checking**: mypy strict mode
- **Validation**: Pydantic v2
- **Testing**: pytest with async support
- **Code Quality**: black, isort, pylint, ruff
- **Package Management**: uv (optional) or pip

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=pyomnilogic_local --cov-report=html

# Type checking
mypy pyomnilogic_local

# Linting
pylint pyomnilogic_local
```

## Credits

This library was made possible by the pioneering work of:

- [djtimca](https://github.com/djtimca/) - Original protocol research and implementation
- [John Sutherland](mailto:garionphx@gmail.com) - Protocol documentation and testing

## Related Projects

- [Home Assistant Integration](https://github.com/cryptk/haomnilogic-local) - Use this library with Home Assistant

## Disclaimer


This is an unofficial library and is not affiliated with, endorsed by, or connected to Hayward Industries, Inc. Use at your own risk. The developers are not responsible for any damage to equipment or property resulting from the use of this software.
