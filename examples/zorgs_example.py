# Legal Disclaimer
# This script is an example script and is not supported under any Zerto support program or service. 
# The author and Zerto further disclaim all implied warranties including, without limitation, 
# any implied warranties of merchantability or of fitness for a particular purpose.
# In no event shall Zerto, its authors or anyone else involved in the creation, 
# production or delivery of the scripts be liable for any damages whatsoever (including, 
# without limitation, damages for loss of business profits, business interruption, loss of business 
# information, or other pecuniary loss) arising out of the use of or the inability to use the sample 
# scripts or documentation, even if the author or Zerto has been advised of the possibility of such damages. 
# The entire risk arising out of the use or performance of the sample scripts and documentation remains with you.

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
    parser = argparse.ArgumentParser(description="Zerto Organizations (ZORG) Example")
    parser.add_argument("--zvm_address", required=True, help="ZVM address")
    parser.add_argument('--client_id', required=True, help='Keycloak client ID')
    parser.add_argument('--client_secret', required=True, help='Keycloak client secret')
    parser.add_argument("--ignore_ssl", action="store_true", help="Ignore SSL certificate verification")
    parser.add_argument("--zorg_id", help="Optional: Specific ZORG ID to query")
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

        # Test 1: Get all ZORGs
        logging.info("\n=== Testing get_zorgs (all) ===")
        try:
            zorgs = client.zorgs.get_zorgs()
            logging.info("All ZORGs:")
            logging.info(json.dumps(zorgs, indent=2))
        except Exception as e:
            logging.error(f"Error getting all ZORGs: {e}")

        # Test 2: Get specific ZORG if ID provided
        if args.zorg_id:
            logging.info(f"\n=== Testing get_zorgs with ID: {args.zorg_id} ===")
            try:
                zorg_details = client.zorgs.get_zorgs(args.zorg_id)
                logging.info("ZORG details:")
                logging.info(json.dumps(zorg_details, indent=2))
            except Exception as e:
                logging.error(f"Error getting ZORG {args.zorg_id}: {e}")
        
        # Test 3: Get first ZORG details if any exist
        elif zorgs and len(zorgs) > 0:
            first_zorg = zorgs[0]
            zorg_identifier = first_zorg.get('ZorgIdentifier')
            if zorg_identifier:
                logging.info(f"\n=== Testing get_zorgs with first found ID: {zorg_identifier} ===")
                try:
                    zorg_details = client.zorgs.get_zorgs(zorg_identifier)
                    logging.info("First ZORG details:")
                    logging.info(json.dumps(zorg_details, indent=2))
                except Exception as e:
                    logging.error(f"Error getting ZORG {zorg_identifier}: {e}")

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        raise

if __name__ == "__main__":
    main() 