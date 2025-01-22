import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import logging
import urllib3
import json
from zvma import ZVMAClient

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def main():
    parser = argparse.ArgumentParser(description="Zerto License Example")
    parser.add_argument("--zvm_address", required=True, help="ZVM address")
    parser.add_argument('--client_id', required=True, help='Keycloak client ID')
    parser.add_argument('--client_secret', required=True, help='Keycloak client secret')
    parser.add_argument("--license_key", help="License key to add/update")
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

        # Get current license information
        logging.info("\nFetching current license information...")
        license_info = client.license.get_license()
        if license_info:
            logging.info("Current license details:")
            logging.info(json.dumps(license_info, indent=2))
        else:
            logging.info("No license currently installed")

        # If license key is provided, update the license
        if args.license_key:
            logging.info(f"\nUpdating license with new key...")
            update_result = client.license.put_license(args.license_key)
            if update_result:
                logging.info("License update result:")
                logging.info(json.dumps(update_result, indent=2))
            else:
                logging.info("License updated successfully (no content returned)")

            # Get updated license information
            logging.info("\nFetching updated license information...")
            updated_license = client.license.get_license()
            if updated_license:
                logging.info("Updated license details:")
                logging.info(json.dumps(updated_license, indent=2))

        # Delete license (commented out for safety - uncomment if needed)
        """
        logging.info("\nDeleting license...")
        delete_result = client.license.delete_license()
        if delete_result:
            logging.info("License deletion result:")
            logging.info(json.dumps(delete_result, indent=2))
        else:
            logging.info("License deleted successfully (no content returned)")

        # Verify license is deleted
        final_check = client.license.get_license()
        if not final_check:
            logging.info("License successfully removed")
        """

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        raise

if __name__ == "__main__":
    main() 