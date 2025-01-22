import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import logging
import urllib3
import json
from zvma import ZVMAClient
from vcenter import connect_to_vcenter, list_datastores

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def main():
    parser = argparse.ArgumentParser(description="Zerto Datastores Example")
    parser.add_argument("--zvm_address", required=True, help="ZVM address")
    parser.add_argument('--client_id', required=True, help='Keycloak client ID')
    parser.add_argument('--client_secret', required=True, help='Keycloak client secret')
    parser.add_argument("--vcenter_address", required=True, help="vCenter address")
    parser.add_argument("--vcenter_user", required=True, help="vCenter username")
    parser.add_argument("--vcenter_password", required=True, help="vCenter password")
    parser.add_argument("--ignore_ssl", action="store_true", help="Ignore SSL certificate verification")
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    try:
        # Connect to ZVM
        logging.info(f"Connecting to ZVM at {args.zvm_address}")
        client = ZVMAClient(
            zvm_address=args.zvm_address,
            client_id=args.client_id,
            client_secret=args.client_secret,
            verify_certificate=not args.ignore_ssl
        )

        # Connect to vCenter
        logging.info(f"Connecting to vCenter at {args.vcenter_address}")
        si = connect_to_vcenter(
            args.vcenter_address,
            args.vcenter_user,
            args.vcenter_password
        )

        # Get all datastores from vCenter
        vcenter_datastores = list_datastores(si)
        logging.info("\nDatastores in vCenter:")
        for ds in vcenter_datastores:
            logging.info(f"Name: {ds['Name']}, Identifier: {ds['Identifier']}")

        # Get all datastores from ZVM
        zvm_datastores = client.datastores.list_datastores()
        logging.info("\nDatastores in ZVM:")
        logging.info(json.dumps(zvm_datastores, indent=2))

        # Get specific datastore details
        if vcenter_datastores:
            # Get the first datastore identifier from vCenter
            first_ds_id = vcenter_datastores[0]['Identifier']
            logging.info(f"\nGetting details for specific datastore: {first_ds_id}")
            
            ds_details = client.datastores.list_datastores(first_ds_id)
            logging.info("Datastore details:")
            logging.info(json.dumps(ds_details, indent=2))

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        raise

if __name__ == "__main__":
    main() 