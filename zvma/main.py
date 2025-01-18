import argparse
import logging
from zvma import ZVMAClient

def main():
    parser = argparse.ArgumentParser(description="ZVMA Client")
    parser.add_argument("--zvm_address", required=True, help="ZVM address")
    parser.add_argument("--username", required=True, help="Username")
    parser.add_argument("--password", required=True, help="Password")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    try:
        client = ZVMAClient(zvm_address=args.zvm_address, username=args.username, password=args.password)
        # Example usage
        vpgs = client.vpgs.list_vpgs()
        logging.info(f"VPGs: {vpgs}")
    except Exception as e:
        logging.error(f"Error: {e}")

if __name__ == "__main__":
    main()