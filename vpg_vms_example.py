import argparse
import logging
import urllib3
import json
from zvma import ZVMAClient
from vcenter import connect_to_vcenter, \
    list_resource_pools, list_networks, list_vms_with_details, \
    list_folders, list_datacenter_children

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
        # Setup clients and get site identifiers
        client1, client2, local_site1_identifier, local_site2_identifier = setup_clients(args)
        
        # Fill basic VPG settings info
        vpg_name = 'VpgTest'
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

        # Get datastore identifier from site 2
        site2_datastores = client2.datastores.list_datastores()
        # logging.info(f"Site 2 Datastores: {json.dumps(site2_datastores, indent=4)}")
        selected_datastore = next((ds for ds in site2_datastores if ds.get('DatastoreName') == "DS_VM_Right"), None)
        site2_datastore_identifier = selected_datastore.get('DatastoreIdentifier')
        logging.info(f"Site 2 Datastore ID: {site2_datastore_identifier}")

        # Fill journal structure
        journal = {
            "DatastoreIdentifier": site2_datastore_identifier,
            "Limitation": {
                "HardLimitInMB": 153600,
                "WarningThresholdInMB": 115200
            }
        }

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
            network_identifier = networks_list[0].get('Identifier')
            logging.info(f"Network Identifier from the first network: {network_identifier}")
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
                "DefaultNetworkIdentifier": network_identifier
                }
            },
            "FailoverTest": {
                "Hypervisor": {
                "DefaultNetworkIdentifier": network_identifier
                }
            }
        }
        vpg_id = client1.vpgs.create_vpg(basic=basic, journal=journal, 
                                         recovery=recovery, networks=networks, sync=True)
        logging.info(f"VPG ID: {vpg_id} created successfully.")

        # Add VMs to the first VPG
        vms = list_vms_with_details(si1)
        vms_to_add = ["RHEL6", "Microsoft 2022"]
        vm_list = []
        for vm in vms:
            logging.info(f"VM: Name={vm.get('Name')}, VM Identifier={vm.get('VMIdentifier')}")
            if vm.get('Name') in vms_to_add:
                logging.info(f"Adding VM {vm.get('Name')} to VPG...")
                vm_payload = {
                    "VmIdentifier": vm.get('VMIdentifier'),
                    "Recovery": {
                        "HostIdentifier": site2_host_identifier,
                        "HostClusterIdentifier": None,
                        "DatastoreIdentifier":site2_datastore_identifier,
                        "DatastoreClusterIdentifier": None,
                        "FolderIdentifier": site2_folder_identifier,
                        "ResourcePoolIdentifier": None,
                        "VCD": None,
                        "PublicCloud": None
                    }
                }
                vm_list.append(vm_payload)
                task_id = client1.vpgs.add_vm_to_vpg(vpg_name, vm_list_payload=vm_payload)
                logging.info(f"Task ID: {task_id} to add VM {vm.get('Name')} to VPG.")

        input("Press Enter to remove Microsoft 2022 VM from the first VPG...")

        # Remove Microsoft 2022 VM from the first VPG
        vm_to_remove = "Microsoft 2022"
        vm_identifier_to_remove = None
        for vm in vms:
            if vm.get('Name') == vm_to_remove:
                vm_identifier_to_remove = vm.get('VMIdentifier')
                task_id = client1.vpgs.remove_vm_from_vpg(vpg_name, vm_identifier_to_remove)
                logging.info(f"Task ID: {task_id} to remove VM {vm_to_remove} from VPG {vpg_name}")
                break

        input("Press Enter to create second VPG...")

        # Create second VPG
        vpg_name_2 = 'VpgTest2'
        basic['Name'] = vpg_name_2  # Update VPG name for second VPG
        
        vpg_id_2 = client1.vpgs.create_vpg(basic=basic, journal=journal, 
                                          recovery=recovery, networks=networks, sync=True)
        logging.info(f"Second VPG ID: {vpg_id_2} created successfully.")

        # Add the removed VM to the second VPG
        if vm_identifier_to_remove:
            vm_payload = {
                "VmIdentifier": vm_identifier_to_remove,
                "Recovery": {
                    "HostIdentifier": site2_host_identifier,
                    "HostClusterIdentifier": None,
                    "DatastoreIdentifier":site2_datastore_identifier,
                    "DatastoreClusterIdentifier": None,
                    "FolderIdentifier": site2_folder_identifier,
                    "ResourcePoolIdentifier": None,
                    "VCD": None,
                    "PublicCloud": None
                }
            }
            task_id = client1.vpgs.add_vm_to_vpg(vpg_name_2, vm_list_payload=vm_payload)
            logging.info(f"Task ID: {task_id} to add VM {vm_to_remove} to VPG {vpg_name_2}")

    except Exception as e:
        logging.exception("Error:")
        logging.error(f"Error: {e}")


    # wait for user input to continue
    input("Press Enter to delete the VPGs...")

    # Delete the VPGs
    client1.vpgs.delete_vpg(vpg_name, force=True, keep_recovery_volumes=False)
    logging.info(f"VPG {vpg_name} deleted successfully.")   
    client1.vpgs.delete_vpg(vpg_name_2, force=True, keep_recovery_volumes=False)
    logging.info(f"VPG {vpg_name_2} deleted successfully.")

if __name__ == "__main__":
    main()