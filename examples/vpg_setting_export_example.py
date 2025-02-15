#!/usr/bin/python3

# Legal Disclaimer
# This script is an example script and is not supported under any Zerto support program or service. 
# The author and Zerto further disclaim all implied warranties including, without limitation, 
# any implied warranties of merchantability or of fitness for a particular purpose.

import argparse
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
import urllib3
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from zvma import ZVMAClient

# Disable SSL warningss
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def setup_client(args):
    """Initialize and return Zerto client"""
    client = ZVMAClient(
        zvm_address=args.site1_address,
        client_id=args.site1_client_id,
        client_secret=args.site1_client_secret,
        verify_certificate=not args.ignore_ssl
    )
    return client

def main():
    parser = argparse.ArgumentParser(description="Export and Import VPG settings example")
    parser.add_argument("--site1_address", required=True, help="Site 1 ZVM address")
    parser.add_argument('--site1_client_id', required=True, help='Site 1 Keycloak client ID')
    parser.add_argument('--site1_client_secret', required=True, help='Site 1 Keycloak client secret')
    parser.add_argument("--ignore_ssl", action="store_true", help="Ignore SSL certificate verification")
    parser.add_argument("--vpg_names", help="Comma-separated list of VPG names to export settings for")
    parser.add_argument("--output_file", help="Optional file to save the exported settings")
    args = parser.parse_args()

    try:
        # Setup client
        client = setup_client(args)
        
        # If no VPG names provided, get all VPGs
        if not args.vpg_names:
            vpgs = client.vpgs.list_vpgs()
            vpg_names = [vpg['VpgName'] for vpg in vpgs]
            logging.info(f"No VPG names provided, exporting all {len(vpg_names)} VPGs")
        else:
            # Split the comma-separated string and strip whitespace
            vpg_names = [name.strip() for name in args.vpg_names.split(',')]
            logging.info(f"Exporting settings for VPGs: {vpg_names}")

        # Step 1: Export VPG settings
        print("\nStep 1: Exporting VPG settings...")
        result = client.vpgs.export_vpg_settings(vpg_names)
        
        print("Export Result:")
        print(f"Timestamp: {result.get('TimeStamp')}")
        print(f"Result: {result.get('ExportResult', {}).get('Result')}")
        print(f"Message: {result.get('ExportResult', {}).get('Message')}")

        # Save to file if specified
        if args.output_file:
            with open(args.output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\nExported settings saved to: {args.output_file}")

        # Step 2: Verify export and read settings
        print("\nStep 2: Reading exported settings...")
        exported_settings = client.vpgs.list_exported_vpg_settings()
        export_timestamp = result.get('TimeStamp', '').split('.')[0] + '.000Z'
        
        if any(setting.get('TimeStamp') == export_timestamp for setting in exported_settings):
            print(f"Found export with timestamp {export_timestamp}")
            settings = client.vpgs.read_exported_vpg_settings(export_timestamp)
            
            # Display summary of exported VPG settings
            vpg_settings = settings.get('ExportedVpgSettingsApi', [])
            print(f"\nFound settings for {len(vpg_settings)} VPGs:")
            for vpg in vpg_settings:
                basic = vpg.get('Basic', {})
                print(f"\nVPG Name: {basic.get('Name')}")
                print(f"Source Site: {vpg.get('SourceSiteName')}")
                print(f"Target Site: {vpg.get('TargetSiteName')}")
                print(f"RPO (seconds): {basic.get('RpoInSeconds')}")
                print(f"Journal History (hours): {basic.get('JournalHistoryInHours')}")

            #pause
            input("Make change to VPG settings and Press Enter to continue...")

            # Step 3: Import the settings back
            print("\nStep 3: Importing VPG settings...")
            import_result = client.vpgs.import_vpg_settings(settings)
            print("\nImport Result:")
            print(f"Result: {import_result.get('Result')}")
            print(f"Message: {import_result.get('Message')}")
            if import_result.get('VpgSettingsIds'):
                print(f"Created VPG Settings IDs: {', '.join(import_result.get('VpgSettingsIds'))}")
            
            #pause
            input("Look at the VPG and verify whether the manual channges are reverted back to the original settings. Press Enter to continue...")
        else:
            print(f"\nWarning: Export with timestamp {export_timestamp} not found in exported settings list")

    except Exception as e:
        logging.exception("Error occurred:")
        sys.exit(1)

if __name__ == "__main__":
    main() 