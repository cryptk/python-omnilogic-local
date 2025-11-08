# Docker Usage Guide

This guide explains how to build and use the Docker image for the `omnilogic` CLI tool.

## Quick Start

### Build the Image

```bash
docker build -t omnilogic-cli .
```

### Run the CLI

Replace `192.168.1.100` with your OmniLogic controller's IP address:

```bash
# Show help
docker run --rm omnilogic-cli --help

# Get raw MSP configuration
docker run --rm omnilogic-cli --host 192.168.1.100 debug --raw get-mspconfig

# Get telemetry data parsed with pydantic
docker run --rm omnilogic-cli --host 192.168.1.100 debug get-telemetry

# List lights
docker run --rm omnilogic-cli --host 192.168.1.100 get lights

# List pumps
docker run --rm omnilogic-cli --host 192.168.1.100 get pumps

```

## CLI Structure

The CLI has two main command groups:

### `get` - Query Equipment Information

Retrieves information about specific pool equipment.

```bash
# View available equipment types
docker run --rm omnilogic-cli get --help

# Examples
docker run --rm omnilogic-cli --host 192.168.1.100 get lights
docker run --rm omnilogic-cli --host 192.168.1.100 get heaters
docker run --rm omnilogic-cli --host 192.168.1.100 get pumps
docker run --rm omnilogic-cli --host 192.168.1.100 get chlorinators
docker run --rm omnilogic-cli --host 192.168.1.100 get schedules
docker run --rm omnilogic-cli --host 192.168.1.100 get sensors
```

### `debug` - Low-level Controller Access

Provides direct access to controller data and debugging utilities.

```bash
# View debug commands
docker run --rm omnilogic-cli debug --help

# Get configuration (use --raw for unprocessed XML)
docker run --rm omnilogic-cli --host 192.168.1.100 debug get-mspconfig
docker run --rm omnilogic-cli --host 192.168.1.100 debug --raw get-mspconfig

# Get telemetry (use --raw for unprocessed XML)
docker run --rm omnilogic-cli --host 192.168.1.100 debug get-telemetry
docker run --rm omnilogic-cli --host 192.168.1.100 debug --raw get-telemetry

# Get filter diagnostics (requires pool-id and filter-id)
docker run --rm omnilogic-cli --host 192.168.1.100 debug get-filter-diagnostics --pool-id 1 --filter-id 5

# Control equipment directly (BOW_ID EQUIP_ID IS_ON)
docker run --rm omnilogic-cli --host 192.168.1.100 debug set-equipment 7 10 true
docker run --rm omnilogic-cli --host 192.168.1.100 debug set-equipment 7 8 50
```

## Network Considerations

The container needs to reach your OmniLogic controller on UDP port 10444. Ensure:

1. Your Docker network can reach the controller's IP
2. No firewall is blocking UDP port 10444
3. The default bridge networking should work fine
4. For host networking (if needed):

```bash
docker run --rm --network host omnilogic-cli --host 192.168.1.100 get lights
```

## Advanced Usage

### Save Output to File

```bash
# Redirect output to a file on the host
docker run --rm omnilogic-cli --host 192.168.1.100 debug get-telemetry > telemetry.xml

# Using volume mounts
docker run --rm -v $(pwd):/data omnilogic-cli --host 192.168.1.100 debug get-mspconfig > /data/config.xml
```

### Interactive Shell

Run multiple commands without rebuilding the connection:

```bash
docker run --rm -it --entrypoint /bin/bash omnilogic-cli

# Inside container:
omnilogic --host 192.168.1.100 get lights
omnilogic --host 192.168.1.100 get pumps
omnilogic --host 192.168.1.100 debug get-telemetry
```

### Parse PCAP Files

The CLI includes a PCAP parser for analyzing OmniLogic protocol traffic. Mount the PCAP file into the container:

```bash
# Capture traffic with tcpdump (on your host or network device)
tcpdump -i eth0 -w pool.pcap udp port 10444

# Parse the PCAP file with Docker
docker run --rm -v $(pwd):/data omnilogic-cli debug parse-pcap /data/pool.pcap
```

**Note**: The `parse-pcap` command analyzes existing PCAP files; it does NOT capture live traffic. Use tcpdump, Wireshark, or similar tools to create the PCAP file first.

## Docker Compose

Create a `docker-compose.yml` file for easier usage:

```yaml
version: '3.8'

services:
  omnilogic:
    build: .
    image: omnilogic-cli
    volumes:
      - ./captures:/data  # For PCAP file analysis
```

Run commands with:

```bash
# Query equipment
docker-compose run --rm omnilogic --host 192.168.1.100 get lights

# Debug commands
docker-compose run --rm omnilogic --host 192.168.1.100 debug get-telemetry

# Parse PCAP files from ./captures directory
docker-compose run --rm omnilogic debug parse-pcap /data/pool.pcap
```

## Building for Multiple Architectures

Build for both AMD64 and ARM64 (useful for Raspberry Pi):

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t omnilogic-cli .
```

## Image Details

### Size

The multi-stage build keeps the image size minimal:
- Builder stage: ~500MB (discarded after build)
- Final runtime image: ~150-200MB

### Included Dependencies

- Python 3.12
- Core dependencies: pydantic, click, xmltodict
- CLI dependencies: scapy (for PCAP parsing)
- Runtime tools: tcpdump (for potential traffic capture outside container)

## Security Notes

- The container runs as a non-root user (`omnilogic`, UID 1000) for security
- No sensitive data is stored in the image
- Network access is only required to communicate with your OmniLogic controller on UDP port 10444
- PCAP parsing does NOT require elevated privileges (only parsing existing files)

## Troubleshooting

### Cannot reach controller

```bash
# Test basic connectivity
docker run --rm omnilogic-cli --host 192.168.1.100 debug get-mspconfig
```

If this fails, check:
- Controller IP address is correct and reachable
- Docker container can access your network
- No firewall blocking UDP port 10444
- Controller is powered on and responsive

### Connection timeout

The default timeout is 5 seconds. If your network is slow:
- Check network latency to the controller
- Ensure UDP port 10444 is not being filtered
- Try from host networking mode: `--network host`

### PCAP file not found

When parsing PCAP files, ensure the file path is accessible from inside the container:

```bash
# BAD - file not accessible to container
docker run --rm omnilogic-cli debug parse-pcap /home/user/pool.pcap

# GOOD - mount the directory containing the PCAP
docker run --rm -v /home/user:/data omnilogic-cli debug parse-pcap /data/pool.pcap
```

## Command Reference

### Equipment Query Commands

```bash
# Get information about specific equipment types
docker run --rm omnilogic-cli --host <IP> get backyard     # Backyard info
docker run --rm omnilogic-cli --host <IP> get bows         # Bodies of water
docker run --rm omnilogic-cli --host <IP> get chlorinators # Chlorinators
docker run --rm omnilogic-cli --host <IP> get csads        # Chemical systems
docker run --rm omnilogic-cli --host <IP> get filters      # Filters/pumps
docker run --rm omnilogic-cli --host <IP> get groups       # Equipment groups
docker run --rm omnilogic-cli --host <IP> get heaters      # Heaters
docker run --rm omnilogic-cli --host <IP> get lights       # Lights
docker run --rm omnilogic-cli --host <IP> get pumps        # Pumps
docker run --rm omnilogic-cli --host <IP> get relays       # Relays
docker run --rm omnilogic-cli --host <IP> get schedules    # Schedules
docker run --rm omnilogic-cli --host <IP> get sensors      # Sensors
docker run --rm omnilogic-cli --host <IP> get valves       # Valves
```

### Debug Commands

```bash
# Configuration and telemetry
docker run --rm omnilogic-cli --host <IP> debug get-mspconfig
docker run --rm omnilogic-cli --host <IP> debug get-telemetry
docker run --rm omnilogic-cli --host <IP> debug --raw get-mspconfig  # Raw XML

# Filter diagnostics (requires IDs from get-mspconfig)
docker run --rm omnilogic-cli --host <IP> debug get-filter-diagnostics --pool-id 1 --filter-id 5

# Equipment control (BOW_ID EQUIP_ID VALUE)
docker run --rm omnilogic-cli --host <IP> debug set-equipment 7 10 true   # Turn on
docker run --rm omnilogic-cli --host <IP> debug set-equipment 7 10 false  # Turn off
docker run --rm omnilogic-cli --host <IP> debug set-equipment 7 8 50      # 50% speed

# PCAP analysis (file must be mounted into container)
docker run --rm -v $(pwd):/data omnilogic-cli debug parse-pcap /data/capture.pcap
```
