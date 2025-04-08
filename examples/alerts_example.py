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


"""
Zerto Alert Management Example Script

This script demonstrates how monitor for specific alerts (VRA0020) and manage them (dismiss/undismiss)
The script creates a VPG (Virtual Protection Group), powers off a VM, and monitors for the VRA0020 alert.

The script performs the following steps:
1. Creates a VPG (Virtual Protection Group)
2. Powers off a VM
3. Monitors for the VRA0020 alert
4. Dismisses the alert
5. Undismisses the alert
6. Powers on the VM

Required Arguments:
    --site1_address: Site 1 ZVM address
    --site1_client_id: Site 1 Keycloak client ID
    --site1_client_secret: Site 1 Keycloak client secret
    --site2_address: Site 2 ZVM address
    --site2_client_id: Site 2 Keycloak client ID
    --site2_client_secret: Site 2 Keycloak client secret
    --vcenter1_ip: Site 1 vCenter IP address (temporary, for power operations)
    --vcenter1_user: Site 1 vCenter username (temporary, for power operations)
    --vcenter1_password: Site 1 vCenter password (temporary, for power operations)

Optional Arguments:
    --ignore_ssl: Ignore SSL certificate verification

Example Usage:
    python examples/alerts_example.py \
        --site1_address <zvm1_address> \
        --site1_client_id <client_id1> \
        --site1_client_secret <secret1> \
        --site2_address <zvm2_address> \
        --site2_client_id <client_id2> \
        --site2_client_secret <secret2> \
        --vcenter1_ip <vcenter1_ip> \
        --vcenter1_user <vcenter1_user> \
        --vcenter1_password <vcenter1_pass> \
        --ignore_ssl
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import logging
import urllib3
import json
from zvma import ZVMAClient
from vcenter import connect_to_vcenter, \
    list_resource_pools, list_networks, list_vms_with_details, \
    list_folders, list_datacenter_children, power_off_vm, power_on_vm
import time
from zvma.common import ZertoVPGStatus, ZertoVPGSubstatus
from zvma.recovery_reports import RecoveryReports
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#name sure the api client lifespan settion is complete the initial sync, in my case I set it to 3600 seconds

def setup_clients(args):
    """
    Initialize and return Zerto clients and their local site identifiers for both sites
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        tuple: (client1, client2, local_site1_id, local_site2_id)
    """
    # Connect to ZVM sites
    client1 = ZVMAClient(
        zvm_address=args.site1_address,
        client_id=args.site1_client_id,
        client_secret=args.site1_client_secret,
        verify_certificate=not args.ignore_ssl
    )
    client2 = ZVMAClient(
        zvm_address=args.site2_address,
        client_id=args.site2_client_id,
        client_secret=args.site2_client_secret,
        verify_certificate=not args.ignore_ssl
    )

    # Get local site identifiers
    local_site1 = client1.localsite.get_local_site()
    local_site2 = client2.localsite.get_local_site()
    local_site1_identifier = local_site1.get('SiteIdentifier')
    local_site2_identifier = local_site2.get('SiteIdentifier')

    return client1, client2, local_site1_identifier, local_site2_identifier

def construct_vpg_settings(vpg_name, local_site1_identifier, local_site2_identifier, site2_datastore_identifier,
                           site2_host_identifier, resource_pool_identifier, site2_folder_identifier, site2_network_identifier):
    basic = {
        "Name": vpg_name,
        "VpgType": "Remote",
        "RpoInSeconds": 300,
        "JournalHistoryInHours": 1,
        "Priority": "Medium",
        "UseWanCompression": True,
        "ProtectedSiteIdentifier": local_site1_identifier,
        "RecoverySiteIdentifier": local_site2_identifier
    }

    # Fill journal structure
    journal = {
        "DatastoreIdentifier": site2_datastore_identifier,
        "Limitation": {
            "HardLimitInMB": 153600,
            "WarningThresholdInMB": 115200
        }
    }

    # Fill recovery structure
    recovery = {  
            "DefaultHostIdentifier": site2_host_identifier,
            "DefaultDatastoreIdentifier": site2_datastore_identifier,
            "DefaultResourcePoolIdentifier": resource_pool_identifier,
            "DefaultFolderIdentifier": site2_folder_identifier
    }

     # Fill Networks structure
    networks = {
            "Failover": {
                "Hypervisor": {
                "DefaultNetworkIdentifier": site2_network_identifier
                }
            },
            "FailoverTest": {
                "Hypervisor": {
                "DefaultNetworkIdentifier": site2_network_identifier
                }
            }
    }

    return basic, journal, recovery, networks


def main():
    parser = argparse.ArgumentParser(description="ZVMA Client")
    parser.add_argument("--site1_address", required=True, help="Site 1 ZVM address")
    parser.add_argument('--site1_client_id', required=True, help='Site 1 Keycloak client ID')
    parser.add_argument('--site1_client_secret', required=True, help='Site 1 Keycloak client secret')
    parser.add_argument("--site2_address", required=True, help="Site 2 ZVM address")
    parser.add_argument('--site2_client_id', required=True, help='Site 2 Keycloak client ID')
    parser.add_argument('--site2_client_secret', required=True, help='Site 2 Keycloak client secret')
    parser.add_argument("--vcenter1_ip", required=True, help="Site 1 vCenter IP address")
    parser.add_argument("--vcenter1_user", required=True, help="Site 1 vCenter username")
    parser.add_argument("--vcenter1_password", required=True, help="Site 1 vCenter password")
    parser.add_argument("--vcenter2_ip", required=True, help="Site 2 vCenter IP address")
    parser.add_argument("--vcenter2_user", required=True, help="Site 2 vCenter username")
    parser.add_argument("--vcenter2_password", required=True, help="Site 2 vCenter password")
    parser.add_argument("--ignore_ssl", action="store_true", help="Ignore SSL certificate verification")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    try:
        vpg_name_1 = 'VpgTest1'
        vpg_name_2 = 'VpgTest2'
        
        # Setup Zerto clients and get site identifiers
        client1, client2, local_site1_identifier, local_site2_identifier = setup_clients(args)

        # Keep vCenter connection for site1 until we replace power operations
        si1 = connect_to_vcenter(
            vcenter_ip=args.vcenter1_ip,
            vcenter_user=args.vcenter1_user,
            vcenter_password=args.vcenter1_password
        )

        # Get datastore identifier from site 2 using virtualization_sites API
        datastores = client2.virtualization_sites.get_virtualization_site_datastores(local_site2_identifier)
        selected_datastore = next((ds for ds in datastores if ds.get('DatastoreName') == "DS_VM_Right"), None)
        site2_datastore_identifier = selected_datastore.get('DatastoreIdentifier')
        logging.info(f"Site 2 Datastore ID: {site2_datastore_identifier}")

        # Get VRAs from site 2 using virtualization_sites API
        hosts = client2.virtualization_sites.get_virtualization_site_hosts(local_site2_identifier)
        logging.info(f"Site 2 Hosts: {json.dumps(hosts, indent=4)}")
        selected_host = next((host for host in hosts if host.get('VirtualizationHostName') == "192.168.222.2"), None)
        site2_host_identifier = selected_host.get('HostIdentifier')
        logging.info(f"Host Identifier: {site2_host_identifier}")

        # List resource pools using virtualization_sites API
        resource_pools = client2.virtualization_sites.get_virtualization_site_resource_pools(local_site2_identifier)
        if resource_pools:
            resource_pool_identifier = resource_pools[0].get('ResourcePoolIdentifier')
            logging.info(f"Resource Pool Identifier: {resource_pool_identifier}")
        else:
            logging.error("No resource pools found on site 2.")
            return

        # List networks using virtualization_sites API
        networks = client2.virtualization_sites.get_virtualization_site_networks(local_site2_identifier)
        if networks:
            site2_network_identifier = networks[0].get('NetworkIdentifier')
            logging.info(f"Network Identifier: {site2_network_identifier}")
        else:
            logging.error("No networks found on site 2.")
            return

        # List folders using virtualization_sites API
        folders = client2.virtualization_sites.get_virtualization_site_folders(local_site2_identifier)
        for folder in folders:
            if folder.get('FolderName') == '/':
                site2_folder_identifier = folder.get('FolderIdentifier')
                logging.info(f"Folder Identifier: {site2_folder_identifier}")
                break

        basic, journal, recovery, networks = construct_vpg_settings(vpg_name_1, local_site1_identifier, local_site2_identifier, 
                                       site2_datastore_identifier, site2_host_identifier, 
                                       resource_pool_identifier, site2_folder_identifier, site2_network_identifier)

        #Create first VPG and add RHEL6 VM
        vpg_id = client1.vpgs.create_vpg(basic=basic, journal=journal, recovery=recovery, networks=networks, sync=True)
        logging.info(f"VPG ID: {vpg_id} created successfully.")

        # Get VM details using virtualization_sites API
        vm_name = "RHEL6-1"
        vms = client1.virtualization_sites.get_virtualization_site_vms(local_site1_identifier)
        logging.info(f"Site 1 VMs: {json.dumps(vms, indent=4)}")
        vm = next((v for v in vms if v.get('VmName') == vm_name), None)
        
        # Power operations still using vCenter
        power_off_vm(si1, vm_name="RHEL6-1")

        # Add RHEL6-1 VM to VPG1 
        vm_payload = { 
            "VmIdentifier": vm.get('VMIdentifier'),
            "Recovery": {
                "HostIdentifier": site2_host_identifier,
                "HostClusterIdentifier": None,
                "DatastoreIdentifier": site2_datastore_identifier,
                "DatastoreClusterIdentifier": None,
                "FolderIdentifier": site2_folder_identifier,
                "ResourcePoolIdentifier": None,
                "VCD": None,
                "PublicCloud": None
            }
        }
        task_id = client1.vpgs.add_vm_to_vpg(vpg_name_1, vm_list_payload=vm_payload)
        logging.info(f"Task ID: {task_id} to add VM {vm_name} to {vpg_name_1}.")

        # add vm to vpg
        response = client1.vpgs.add_vm_to_vpg(vpg_id, vm_name=vm_name)
        logging.info(f"VM {vm_name} added to VPG {vpg_id} successfully. response: {response}")

        # Wait for up to 3 minutes (180 seconds) for specific alert to appear
        start_time = time.time()
        end_time = start_time + 180  # 3 minutes timeout
        alert_id = None
        logging.info("Starting to monitor for VRA0020 alert...")
        while time.time() < end_time:
            alerts = client1.alerts.get_alerts()
            if alerts:
                # Search for alert with HelpIdentifier VRA0020
                vra_alert = next((alert for alert in alerts if alert.get('HelpIdentifier') == 'VRA0020'), None)
                if vra_alert:
                    alert_id = vra_alert.get('Link').get('identifier')
                    logging.info(f"VRA0020 alert found after {int(time.time() - start_time)} seconds:")
                    logging.info(f"Alert details: {json.dumps(vra_alert, indent=4)}")
                    break
                    
            logging.info(f"VRA0020 alert not found. Waiting... ({int(end_time - time.time())} seconds remaining)")
            time.sleep(10)  # Check every 10 seconds
        else:
            logging.warning("VRA0020 alert not found after 3 minutes")
            return
        # Wait for up to 3 minutes for the VRA0020 alert to disappear
        start_time = time.time()
        end_time = start_time + 180  # 3 minutes timeout

        input("Check the alert in Zerto UI, Press Enter to dismiss the alert...")
        client1.alerts.dismiss_alert(alert_identifier=alert_id)

        input("Check the alert in Zerto UI, Press Enter to undismiss the alert...")
        client1.alerts.undismiss_alert(alert_identifier=alert_id)
        # Power on the VM
        logging.info("Check the alert in Zerto UI, Powering on VM 'RHEL6-1'...")
        power_on_vm(si1, vm_name="RHEL6-1")

        # user input to delete the VPG
        input("Press Enter to delete the VPG...")

        client1.vpgs.delete_vpg(vpg_name_1)
        logging.info(f"VPG {vpg_name_1} deleted successfully.")

    except Exception as e:
        logging.exception("Error:")
        logging.error(f"Error: {e}")

if __name__ == "__main__":
    main()