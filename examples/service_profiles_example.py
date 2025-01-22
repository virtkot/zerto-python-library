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
    parser = argparse.ArgumentParser(description="Zerto Service Profiles Example")
    parser.add_argument("--zvm_address", required=True, help="ZVM address")
    parser.add_argument('--client_id', required=True, help='Keycloak client ID')
    parser.add_argument('--client_secret', required=True, help='Keycloak client secret')
    parser.add_argument("--site_identifier", help="Optional site identifier to filter profiles")
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

        # Get all service profiles
        logging.info("\nFetching service profiles...")
        profiles = client.service_profiles.get_service_profiles(
            site_identifier=args.site_identifier
        )

        # Display service profiles information
        if profiles:
            logging.info(f"\nFound {len(profiles)} service profiles:")
            for profile in profiles:
                logging.info("\nService Profile Details:")
                logging.info(f"Name: {profile.get('serviceProfileName')}")
                logging.info(f"RPO: {profile.get('rpo')}")
                logging.info(f"History: {profile.get('history')}")
                logging.info(f"Max Journal Size: {profile.get('maxJournalSizeInPercent')}%")
                logging.info(f"Test Interval: {profile.get('testInterval')}")
                if profile.get('description'):
                    logging.info(f"Description: {profile.get('description')}")
                logging.info("-" * 50)
        else:
            logging.warning("No service profiles found")

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        raise

if __name__ == "__main__":
    main() 