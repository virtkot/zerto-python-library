# zerto-python-library
A Python library for interacting with the Zerto Virtual Manager (ZVM) API.

## Overview
This library provides a comprehensive Python interface to manage and automate Zerto Virtual Replication operations. It includes functionality for:

- Managing Virtual Protection Groups (VPGs)
- Handling VM protection and recovery
- Managing checkpoints and recovery points
- Monitoring alerts and events
- Managing licenses
- Configuring service profiles
- Handling encryption detection
- Managing datastores and VRAs
- Working with server date/time settings
- Managing ZORGs (Zerto Organizations)

## Installation

git clone https://github.com/your-repo/zerto-python-library.git
cd zerto-python-library
pip install -r requirements.txt

## Dependencies

- requests
- urllib3
- logging
- json
- typing

## Library Structure

The library is organized into several modules:

- `zvml/` - Core library components
  - `alerts.py` - Alert management and monitoring
  - `checkpoints.py` - Checkpoint operations and management
  - `common.py` - Common enums and utilities
  - `encryptiondetection.py` - Encryption detection functionality
  - `license.py` - License management
  - `localsite.py` - Local site operations
  - `recovery_reports.py` - Recovery reporting functionality
  - `server_date_time.py` - Server time operations
  - `service_profiles.py` - Service profile configuration
  - `tasks.py` - Task management and monitoring
  - `virtualization_sites.py` - Site management operations
  - `vpgs.py` - VPG operations and management
  - `vras.py` - VRA deployment and management
  - `zorgs.py` - ZORG operations

## Examples

Each example script demonstrates specific functionality:

### Alert Management
`alerts_example.py` - Simple alert monitoring and management (list, dismiss, undismiss):

python examples/alerts_example.py \
--zvm_address "192.168.111.20" \
--client_id "zerto-api" \
--client_secret "your-secret-here" \
--ignore_ssl

### VPG Management
`vpg_vms_example.py` - VPG creation and VM management between VPGs:

python examples/vpg_vms_example.py \
--zvm_address "192.168.111.20" \
--client_id "zerto-api" \
--client_secret "your-secret-here" \
--ignore_ssl

### VPG Failover Testing
`vpg_failover_example.py` - Complete VPG lifecycle including failover testing:

python examples/vpg_failover_example.py \
--zvm_address "192.168.111.20" \
--client_id "zerto-api" \
--client_secret "your-secret-here" \
--ignore_ssl

### VRA Management
`vras_example.py` - Interactive VRA deployment and management:

python examples/vras_example.py \
--zvm_address "192.168.111.20" \
--client_id "zerto-api" \
--client_secret "your-secret-here" \
--ignore_ssl

### ZORG Management
`zorgs_example.py` - ZORG information retrieval and management:

python examples/zorgs_example.py \
--zvm_address "192.168.111.20" \
--client_id "zerto-api" \
--client_secret "your-secret-here" \
--ignore_ssl

## Requirements

- Python 3.6+
- Zerto Virtual Replication environment
- Network access to ZVM server
- Keycloak authentication credentials

## Getting Started

1. Clone the repository
2. Install required dependencies
3. Configure your Zerto environment credentials
4. Run the example scripts to understand basic operations
5. Integrate the library into your automation workflows

## Authentication

The library uses Keycloak authentication. You'll need:
- ZVM server address
- Client ID
- Client Secret
- Optional: SSL verification settings

## Error Handling

The library includes comprehensive error handling and logging:
- Input validation
- Error status checking
- Detailed error messages
- Operation status logging

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project includes a legal disclaimer. See the header of each file for details.

For detailed API documentation and examples, please refer to the individual module files and example scripts.

  