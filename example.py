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
import urllib3
import json
import argparse
import logging
import ssl
import sys
from zerto import ZertoClient

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to validate VPG parameters
def validate_vpg_params(vpg_name, vpg_payload_file):
    if not vpg_name:
        logging.error("VPG name is required.")
        sys.exit(1)
    if not vpg_payload_file:
        logging.error("JSON payload file is required.")
        sys.exit(1)

# Main function to parse arguments and orchestrate the script
def main():
    # Argument parsing
    parser = argparse.ArgumentParser(description="Create a Zerto VPG and retrieve vCenter data")
    parser.add_argument('--zvm_address', required=True, help='ZVM address (IP or hostname)')
    parser.add_argument('--client_id', required=True, help='Keycloak client ID')
    parser.add_argument('--client_secret', required=True, help='Keycloak client secret')
    parser.add_argument('--vpg_name', required=True, help='Name of the VPG to create')
    parser.add_argument('--vpg_payload_file', required=True, help='Path to the JSON file containing the VPG payload')
    parser.add_argument('--vms_payload_file', required=True, help='Path to the JSON file containing the VMs payload')
    args = parser.parse_args()

    # Validate VPG parameters
    validate_vpg_params(args.vpg_name, args.vpg_payload_file)

    # Initialize the ZertoClient
    zerto_client = ZertoClient(args.zvm_address, args.client_id, args.client_secret)

    # Load the VPG payload
    try:
        with open(args.vpg_payload_file, 'r') as file:
            vpg_payload = json.load(file)
        vpg_payload["Basic"]["Name"] = args.vpg_name
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading VPG payload: {e}")
        sys.exit(1)

    # Load the VMs payload
    try:
        with open(args.vms_payload_file, 'r') as file:
            vm_payload = json.load(file)
        logging.info(f"Loaded VMs payload from {args.vms_payload_file}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading VMs payload: {e}")
        sys.exit(1)


    # # Parameters for VRA installation on cluster
    # cluster_identifier = "79e3f102-92c2-4c3a-9783-6367165e8c73.domain-c22"
    # datastore_identifier = "79e3f102-92c2-4c3a-9783-6367165e8c73.datastore-13"
    # network_identifier = "79e3f102-92c2-4c3a-9783-6367165e8c73.network-14"
    # memory_in_gb = 8
    # num_of_cpus = 4
    # group_name = "MyVRAGroup"
    # vra_network_data = {
    #     "vraIPConfigurationTypeApi": "IpPool",
    #     "vraIPAddress": "192.168.10.50",
    #     "vraIPAddressRangeEnd": "192.168.10.60",
    #     "subnetMask": "255.255.255.0",
    #     "defaultGateway": "192.168.10.1"
    # }
    # host_root_password = "YourPassword"


    # response = zerto_client.list_resource_reports()
    # logging.info(f'license={json.dumps(response, indent=2)}')

    response = zerto_client.get_recovery_reports(recovery_operation_identifier='b1e7156c-48ce-4bf1-b11a-eff22c2f9ef3')
    logging.info(f'license={json.dumps(response, indent=2)}')

    # response = zerto_client.delete_license()
    # logging.info(f'response={json.dumps(response, indent=2)}')

    # license = zerto_client.get_license()
    # logging.info(f'license={json.dumps(license, indent=2)}')

    # license = zerto_client.put_license(license_key='HVHGP7H7HKK9FFEX87MVGVREXWUFRBXME6L5ZAXC4Q')
    # logging.info(f'license={json.dumps(license, indent=2)}')

    # license = zerto_client.get_license()
    # logging.info(f'license={json.dumps(license, indent=2)}')

    # checkpoints = zerto_client.list_checkpoints(vpg_name='test', start_date='2024-12-02T00:00:00.000Z')
    # logging.info(f'checkpoints={json.dumps(checkpoints, indent=2)}')

    # flr_response = zerto_client.initiate_file_level_restore(vpg_name='test', vm_name='Debian11', 
    #                                                                    initial_download_path='Volume1-Ext4/etc/cron.d')
    # logging.info(f'response={json.dumps(flr_response, indent=2)}')


    # task_id = zerto_client.install_vra_on_cluster(
    #     cluster_identifier=cluster_identifier,
    #     datastore_identifier=datastore_identifier,
    #     network_identifier=network_identifier,
    #     memory_in_gb=memory_in_gb,
    #     num_of_cpus=num_of_cpus,
    #     group_name=group_name,
    #     vra_network_data=vra_network_data,
    #     host_root_password=host_root_password,
    #     sync=True
    # )
    # print(f"VRA Installation Task Completed: {task_id}")


    # # Parameters for VRA installation
    # host_identifier = "12fb5b13-8740-41f9-a76c-2740221b6006.host-18"
    # datastore_identifier = "12fb5b13-8740-41f9-a76c-2740221b6006.datastore-11"
    # network_identifier = "12fb5b13-8740-41f9-a76c-2740221b6006.network-14"
    # host_root_password = "your-host-password"
    # memory_in_gb = 3
    # group_name = "default_group"
    # vra_ip_config_type = "STATIC"  # or "DHCP"
    # vra_ip_address = "192.168.111.31"
    # vra_ip_address_range_end = "192.168.111.35"
    # subnet_mask = "255.255.255.0"
    # default_gateway = "192.168.111.254"
    # use_public_key_instead_of_credentials = True
    # populate_post_installation = True
    # num_of_cpus = 2
    # vm_instance_type = "m5.large"
    # sync = True  # Wait for the installation to complete


    # response = zerto_client.install_vra(
    #         host_identifier=host_identifier,
    #         datastore_identifier=datastore_identifier,
    #         network_identifier=network_identifier,
    #         host_root_password=host_root_password,
    #         memory_in_gb=memory_in_gb,
    #         group_name=group_name,
    #         vra_ip_config_type=vra_ip_config_type,
    #         vra_ip_address=vra_ip_address,
    #         vra_ip_address_range_end=vra_ip_address_range_end,
    #         subnet_mask=subnet_mask,
    #         default_gateway=default_gateway,
    #         use_public_key_instead_of_credentials=use_public_key_instead_of_credentials,
    #         populate_post_installation=populate_post_installation,
    #         num_of_cpus=num_of_cpus,
    #         vm_instance_type=vm_instance_type,
    #         sync=sync
    #     )
    # logging.info(f"VRA installation response: {response}")

    # response = zerto_client.list_vras()
    # logging.info(f'list_vras response={json.dumps(response, indent=2)}')
   

    # response = zerto_client.failover(vpg_name='ScottVpg', vm_name_list=['Microsoft2022', 'Debian11'], commit_policy=1, 
    #                                  is_reverse_protection=True, shutdown_policy=1, sync=True)
    # response = zerto_client.failover(vpg_name='ScottVpg', commit_policy=1, 
    #                                  is_reverse_protection=True, shutdown_policy=1, sync=True)
    # logging.info(f'failover response={json.dumps(response, indent=2)}')

    # input('Enter to rollback...')

    # response = zerto_client.commit_failover(vpg_name='ScottVpg', is_reverse_protection=False, sync=True)
    # logging.info(f'commit failover response={json.dumps(response, indent=2)}')

    # failover_commit_policies = zerto_client.list_failover_commit_policies()
    # logging.info(f'failover_commit_policies={json.dumps(failover_commit_policies, indent=2)}')

    # failover_shutdown_policies = zerto_client.list_failover_shutdown_policies()
    # logging.info(f'failover_shutdown_policies={json.dumps(failover_shutdown_policies, indent=2)}')

    # vms = zerto_client.list_vms(vm_name='Debian11-2');
    # logging.info(f'vms={json.dumps(vms, indent=2)}')
   

    # checkpoints = zerto_client.list_checkpoints(vpg_name='ScottVpg', start_date='2024-11-19T00:00:00.000Z')
    # logging.info(f'checkpoints={json.dumps(checkpoints, indent=2)}')
    
    # response = zerto_client.failover_test(vpg_name='ScottVpg', vm_name_list=['Microsoft2022', 'Debian11'], sync=True)
    # logging.info(f'failover_test response={json.dumps(response, indent=2)}')
    
    # input("Press Enter to add vms...")

    # response = zerto_client.stop_failover_test(vpg_name='ScottVpg', sync=True)
    # logging.info(f'failover_test response={json.dumps(response, indent=2)}')

    # checkpoints = zerto_client.list_checkpoints(vpg_name='ARCUS1', start_date='2024-11-13T23:00:31.000Z', endd_date='2024-11-13T23:30:36.000Z')
    # logging.info(f'checkpoints={json.dumps(checkpoints, indent=2)}')
    # checkpoints = zerto_client.list_checkpoints(vpg_name='ARCUS1', checkpoint_date_str='November 13, 2024 5:22:03 PM')
    # logging.info(f'checkpoints={json.dumps(checkpoints, indent=2)}')
    # checkpoints = zerto_client.list_checkpoints(vpg_name='ARCUS1', latest=True)
    # logging.info(f'checkpoints={json.dumps(checkpoints, indent=2)}')

    # event_entities = zerto_client.list_event_entities()
    # logging.info(f'event_entities={json.dumps(event_entities, indent=4)}')

    # event_types = zerto_client.list_event_types()
    # logging.info(f'event_types={json.dumps(event_types, indent=4)}')
   
    # events = zerto_client.list_events()
    # logging.info(f'events={json.dumps(events, indent=4)}')

    # event = zerto_client.list_events(event_identifier='a0953c83-db28-4fcc-bd92-990058824a96')
    # logging.info(f'event={json.dumps(event, indent=4)}')

    # datastores = zerto_client.list_datastores()
    # logging.info(f'datastores={json.dumps(datastores, indent=4)}')
 
    # datastore = zerto_client.list_datastores(datastore_identifier='12fb5b13-8740-41f9-a76c-2740221b6006.datastore-12')
    # logging.info(f'datastore={json.dumps(datastore, indent=4)}')

    # #get alerts from ZVM
    # alerts = zerto_client.get_alerts();
    # logging.info(f'alerts={json.dumps(alerts, indent=4)}')

    # alerts = zerto_client.get_alerts(alert_identifier='f51d3969-958d-4e70-b378-d1583c26aa9a');
    # logging.info(f'alerts={json.dumps(alerts, indent=4)}')

    # zerto_client.dismiss_alert(alert_identifier='f51d3969-958d-4e70-b378-d1583c26aa9a')

    # zerto_client.undismiss_alert(alert_identifier='f51d3969-958d-4e70-b378-d1583c26aa9a')
    
    # alert_levels = zerto_client.get_alert_levels();
    # logging.info(f'alerts={json.dumps(alert_levels, indent=4)}')

    # alert_entities = zerto_client.get_alert_entities();
    # logging.info(f'alert_entities={json.dumps(alert_entities, indent=4)}')

    # alert_help_identifiers = zerto_client.get_alert_help_identifiers();
    # logging.info(f'alert_help_identifiers={json.dumps(alert_help_identifiers, indent=4)}')

    # Create VPG
    # zerto_client.create_vpg(vpg_payload, sync=True)

    # Add first VM to the VPG, Microsoft VM
    # vm_payload['VmIdentifier'] = '12fb5b13-8740-41f9-a76c-2740221b6006.vm-23'
    # zerto_client.add_vm_to_vpg(args.vpg_name, vm_payload)

    # Add second VM to the VPG, Ubuntu VM
    # vm_payload['VmIdentifier'] = '12fb5b13-8740-41f9-a76c-2740221b6006.vm-1010'
    # zerto_client.add_vm_to_vpg(args.vpg_name, vm_payload)

    # Remove the Microsoft VM from the VPG
    # zerto_client.remove_vm_from_vpg(args.vpg_name, '12fb5b13-8740-41f9-a76c-2740221b6006.vm-23')


    # delete vpg 
    # zerto_client.delete_vpg(args.vpg_name, force=False, keep_recovery_volumes=False)

if __name__ == "__main__":
    main()
