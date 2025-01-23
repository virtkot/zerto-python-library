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
- Managing datastores
- Working with server date/time settings

## Library Structure

The library is organized into several modules:

- `zvma/` - Core library components
  - `checkpoints.py` - Checkpoint management
  - `common.py` - Common enums and utilities
  - `encryptiondetection.py` - Encryption detection functionality
  - `license.py` - License management
  - `server_date_time.py` - Server time operations
  - `service_profiles.py` - Service profile configuration

## Features

- **Authentication**: Secure authentication using client ID and secret
- **SSL Verification**: Optional SSL certificate verification
- **Comprehensive API Coverage**: Support for all major Zerto operations
- **Error Handling**: Robust error handling and logging
- **Parallel Operations**: Support for parallel failover testing and other operations
- **Monitoring**: Real-time status monitoring and reporting
- **Resource Management**: Complete control over VPGs, VMs, and infrastructure resources

## Requirements

- Python 3.6+
- Zerto Virtual Replication environment
- vSphere environment
- Network access to ZVM and vCenter servers

## Getting Started

1. Clone the repository
2. Install required dependencies
3. Configure your Zerto environment
4. Run the example scripts to understand basic operations
5. Integrate the library into your automation workflows

For detailed API documentation and examples, please refer to the individual module files and example scripts.

## Examples

The library includes several example scripts demonstrating common use cases:

### VPG Command Line
Create and manage Virtual Protection Groups:
This example demonstrates:
- Creating VPGs with multiple VMs
- Adding and removing VMs from VPGs
- Managing VM protection settings
- Monitoring VPG and VM status

cd examples

python3 ./vpg_example.py \
--site1_address <site1_zvm_ip> \
--site1_client_id <site1_client_id> \
--site1_client_secret <site1_client_secret> \
--vcenter1_ip <site1_vcenter_ip> \
--vcenter1_user <site1_vcenter_user> \
--vcenter1_password <site1_vcenter_password> \
--site2_address <site2_zvm_ip> \
--site2_client_id <site2_client_id> \
--site2_client_secret <site2_client_secret> \
--vcenter2_ip <site2_vcenter_ip> \
--vcenter2_user <site2_vcenter_user> \
--vcenter2_password <site2_vcenter_password> \
--ignore_ssl

### Alerts Command Line
Monitor and manage Zerto alerts:

bash
python3 ./alerts_example.py \
--site1_address <site1_zvm_ip> \
--site1_client_id <site1_client_id> \
--site1_client_secret <site1_client_secret> \
--vcenter1_ip <site1_vcenter_ip> \
--vcenter1_user <site1_vcenter_user> \
--vcenter1_password <site1_vcenter_password> \
--site2_address <site2_zvm_ip> \
--site2_client_id <site2_client_id> \
--site2_client_secret <site2_client_secret> \
--vcenter2_ip <site2_vcenter_ip> \
--vcenter2_user <site2_vcenter_user> \
--vcenter2_password <site2_vcenter_password> \
--ignore_ssl


### Datastore Command Line
Manage and monitor datastores:

bash
python3 ./datastore_example.py \
--zvm_address <zvm_ip> \
--client_id <client_id> \
--client_secret <client_secret> \
--vcenter_address <vcenter_ip> \
--vcenter_user <vcenter_user> \
--vcenter_password <vcenter_password> \
--ignore_ssl
