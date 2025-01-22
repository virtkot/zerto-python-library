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
    # Create clients for both sites
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
    
    # Get local site ids
    local_site1_identifier = client1.localsite.get_local_site().get('SiteIdentifier')
    logging.info(f"Site 1 Local Site ID: {local_site1_identifier}")

    local_site2_identifier = client2.localsite.get_local_site().get('SiteIdentifier')
    logging.info(f"Site 2 Local Site ID: {local_site2_identifier}")
    
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
        
        # Setup clients and get site identifiers
        client1, client2, local_site1_identifier, local_site2_identifier = setup_clients(args)

        # Get datastore identifier from site 2
        site2_datastores = client2.datastores.list_datastores()
        # logging.info(f"Site 2 Datastores: {json.dumps(site2_datastores, indent=4)}")
        selected_datastore = next((ds for ds in site2_datastores if ds.get('DatastoreName') == "DS_VM_Right"), None)
        site2_datastore_identifier = selected_datastore.get('DatastoreIdentifier')
        logging.info(f"Site 2 Datastore ID: {site2_datastore_identifier}")


        # Get VRAs from site 2
        site2_vras = client2.vras.list_vras()
        # logging.info(f"Site 2 VRAs: {json.dumps(site2_vras, indent=4)}")
        # Extract host identifier from the first VRA on the list
        if site2_vras:
            selected_vra = next((vra for vra in site2_vras if vra.get('VraName') == "Z-VRA-192.168.222.2"), None)
            site2_host_identifier = selected_vra.get('HostIdentifier')
            logging.info(f"Host Identifier from the first VRA: {site2_host_identifier}")
        else:
            logging.error("No VRAs found on site 2.")
            return

        # Connect to site1 vCenter
        si1 = connect_to_vcenter(args.vcenter1_ip, args.vcenter1_user, args.vcenter1_password)
        
        
        # Connect to site2 vCenter
        si2 = connect_to_vcenter(args.vcenter2_ip, args.vcenter2_user, args.vcenter2_password)

        # List resource pools from site2 vCenter
        resource_pools = list_resource_pools(si2)
        logging.info(f"Site 2 Resource Pools: {resource_pools}")

        # Extract resource pool identifier from the first resource pool on the list
        if resource_pools:
            resource_pool_identifier = resource_pools[0].get('Identifier')
            logging.info(f"Resource Pool Identifier from the first resource pool: {resource_pool_identifier}")
        else:
            logging.error("No resource pools found on site 2.")
            return

        # List networks from site2 vCenter
        networks_list = list_networks(si2)
        # Extract network identifier from the first network on the list
        if networks_list:
            site2_network_identifier = networks_list[0].get('Identifier')
            logging.info(f"Network Identifier from the first network: {site2_network_identifier}")
        else:
            logging.error("No networks found on site 2.")
            return
        
        #list folders from site2 vCenter
        folders = list_folders(si2)
        # logging.info(f"Site 2 Folders: {json.dumps(folders, indent=4)}")
        for folder in folders:
            if folder.get('Name') == '/':
                site2_folder_identifier = folder.get('Identifier')
                logging.info(f"Folder Identifier: {site2_folder_identifier}")
                break

        basic, journal, recovery, networks = construct_vpg_settings(vpg_name_1, local_site1_identifier, local_site2_identifier, 
                                       site2_datastore_identifier, site2_host_identifier, 
                                       resource_pool_identifier, site2_folder_identifier, site2_network_identifier)

        #Create first VPG and add RHEL6 VM
        vpg_id = client1.vpgs.create_vpg(basic=basic, journal=journal, recovery=recovery, networks=networks, sync=True)
        logging.info(f"VPG ID: {vpg_id} created successfully.")

        power_on_vm(si1, vm_name="RHEL6-1")
        # Add RHEL6-1 VM to VPG1 
        vm_name = "RHEL6-1"   
        vm = list_vms_with_details(si1, vm_name=vm_name)
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

        power_off_vm(si1, vm_name="RHEL6-1")

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