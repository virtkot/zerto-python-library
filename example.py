import urllib3
import json
import argparse
import logging
import ssl
import sys
from zerto import ZertoClient

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to validate VPG parameters
def validate_vpg_params(vpg_name, vpg_payload_file):
    if not vpg_name:
        logging.error("VPG name is required.")
        sys.exit(1)
    if not vpg_payload_file:
        logging.error("JSON payload file is required.")
        sys.exit(1)

# Main function to parse arguments and orchestrate the script
def main():
    # Argument parsing
    parser = argparse.ArgumentParser(description="Create a Zerto VPG and retrieve vCenter data")
    parser.add_argument('--zvm_address', required=True, help='ZVM address (IP or hostname)')
    parser.add_argument('--client_id', required=True, help='Keycloak client ID')
    parser.add_argument('--client_secret', required=True, help='Keycloak client secret')
    parser.add_argument('--vpg_name', required=True, help='Name of the VPG to create')
    parser.add_argument('--vpg_payload_file', required=True, help='Path to the JSON file containing the VPG payload')
    parser.add_argument('--vms_payload_file', required=True, help='Path to the JSON file containing the VMs payload')
    args = parser.parse_args()

    # Validate VPG parameters
    validate_vpg_params(args.vpg_name, args.vpg_payload_file)

    # Initialize the ZertoClient
    zerto_client = ZertoClient(args.zvm_address, args.client_id, args.client_secret)

    # Load the VPG payload
    try:
        with open(args.vpg_payload_file, 'r') as file:
            vpg_payload = json.load(file)
        vpg_payload["Basic"]["Name"] = args.vpg_name
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading VPG payload: {e}")
        sys.exit(1)

    # Load the VMs payload
    try:
        with open(args.vms_payload_file, 'r') as file:
            vm_payload = json.load(file)
        logging.info(f"Loaded VMs payload from {args.vms_payload_file}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading VMs payload: {e}")
        sys.exit(1)

    # Create VPG
    zerto_client.create_vpg(vpg_payload, sync=True)

    # Add first VM to the VPG, Microsoft VM
    vm_payload['VmIdentifier'] = '12fb5b13-8740-41f9-a76c-2740221b6006.vm-23'
    zerto_client.add_vm_to_vpg(args.vpg_name, vm_payload)

    # Add second VM to the VPG, Ubuntu VM
    vm_payload['VmIdentifier'] = '12fb5b13-8740-41f9-a76c-2740221b6006.vm-1010'
    zerto_client.add_vm_to_vpg(args.vpg_name, vm_payload)

    # Remove the Microsoft VM from the VPG
    # zerto_client.remove_vm_from_vpg(args.vpg_name, '12fb5b13-8740-41f9-a76c-2740221b6006.vm-23')


    # delete vpg 
    # zerto_client.delete_vpg(args.vpg_name, force=False, keep_recovery_volumes=False)

if __name__ == "__main__":
    main()
