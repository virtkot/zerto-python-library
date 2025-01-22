import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import logging
import urllib3
from zvma import ZVMAClient
from zvma.server_date_time import DateTimeFormat

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def main():
    parser = argparse.ArgumentParser(description="Zerto Server Date-Time Example")
    parser.add_argument("--zvm_address", required=True, help="ZVM address")
    parser.add_argument('--client_id', required=True, help='Keycloak client ID')
    parser.add_argument('--client_secret', required=True, help='Keycloak client secret')
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

        # Test all three date-time formats
        logging.info("\nTesting all server date-time formats:")

        # Get local time
        local_time = client.server_date_time.get_server_date_time(DateTimeFormat.LOCAL)
        logging.info(f"\nLocal Time: {local_time}")

        # Get UTC time
        utc_time = client.server_date_time.get_server_date_time(DateTimeFormat.UTC)
        logging.info(f"UTC Time: {utc_time}")

        # Get argument format
        arg_format = client.server_date_time.get_server_date_time(DateTimeFormat.ARGUMENT)
        logging.info(f"Argument Format: {arg_format}")

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        raise

if __name__ == "__main__":
    main() 