import ssl
import atexit
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
from pyVim.task import WaitForTask
import logging

# Disable SSL verification for vCenter connections (if needed)
context = ssl._create_unverified_context()

# Function to connect to vCenter server
def connect_to_vcenter(vcenter_ip, vcenter_user, vcenter_password):
    try:
        si = SmartConnect(host=vcenter_ip, user=vcenter_user, pwd=vcenter_password, sslContext=context)
        atexit.register(Disconnect, si)  # Disconnect at the end of the script
        logging.info("Successfully connected to vCenter")
        return si
    except Exception as e:
        logging.error(f"Failed to connect to vCenter: {e}")
        sys.exit(1)

# Function to get the vCenter server's instance UUID
def get_vcenter_server_uuid(si):
    content = si.RetrieveContent()
    vcenter_uuid = content.about.instanceUuid  # This should be the system-wide UUID you're looking for
    return vcenter_uuid

# Function to list all hosts with the vCenter Server UUID
def list_hosts(si):
    # Get the common vCenter UUID
    vcenter_uuid = get_vcenter_server_uuid(si)

    content = si.RetrieveContent()
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True)
    hosts = container.view
    host_list = []

    for host in hosts:
        host_info = {
            "Name": host.name,
            # Use the vCenter UUID and host identifier
            "HostIdentifier": f"{vcenter_uuid}.host-{host._moId.split('-')[-1]}"
        }
        host_list.append(host_info)

    return host_list

# Function to list all datastores with the vCenter Server UUID
def list_datastores(si):
    # Get the common vCenter UUID
    vcenter_uuid = get_vcenter_server_uuid(si)

    content = si.RetrieveContent()
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.Datastore], True)
    datastores = container.view
    datastore_list = []

    for datastore in datastores:
        # Construct DatastoreIdentifier using vCenter UUID
        datastore_id = f"{vcenter_uuid}.datastore-{datastore._moId.split('-')[-1]}"

        datastore_info = {
            "Name": datastore.name,
            "Identifier": datastore_id
        }
        datastore_list.append(datastore_info)

    return datastore_list

# Function to list all resource pools with the vCenter Server UUID and cluster ID
def list_resource_pools(si):
    content = si.RetrieveContent()
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.ResourcePool], True)
    resource_pools = container.view
    resource_pool_list = []

    for pool in resource_pools:
        # Get the cluster ID
        cluster = pool.owner
        cluster_id = cluster._moId.split('-')[-1]

        # Get the vCenter UUID
        vcenter_uuid = get_vcenter_server_uuid(si)

        # Construct the resource pool identifier
        resource_pool_identifier = f"{vcenter_uuid}.resgroup-{cluster_id}"

        resource_pool_info = {
            "Name": pool.name,
            "Identifier": resource_pool_identifier
        }
        resource_pool_list.append(resource_pool_info)

    return resource_pool_list

# Function to list all networks with the vCenter Server UUID and network ID
def list_networks(si):
    content = si.RetrieveContent()
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.Network], True)
    networks = container.view
    network_list = []

    for network in networks:
        # Get the vCenter UUID
        vcenter_uuid = get_vcenter_server_uuid(si)

        # Construct the network identifier
        network_id = f"{vcenter_uuid}.network-{network._moId.split('-')[-1]}"

        network_info = {
            "Name": network.name,
            "Identifier": network_id
        }
        network_list.append(network_info)

    return network_list

# Function to list all VMs with the vCenter Server UUID
def list_vms_with_details(si, vm_name=None):
    # Get the common vCenter UUID
    vcenter_uuid = get_vcenter_server_uuid(si)

    content = si.RetrieveContent()
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
    vms = container.view
    vm_list = []

    for vm in vms:
        summary = vm.summary
        config = vm.config

        if vm_name and summary.config.name != vm_name:
            continue

        # Construct VMIdentifier using vCenter UUID
        vm_identifier = f"{vcenter_uuid}.vm-{vm._moId.split('-')[-1]}"

        vm_info = {
            "Name": summary.config.name,
            "VMIdentifier": vm_identifier,
            "PowerState": summary.runtime.powerState,
            "Host": summary.runtime.host.name if summary.runtime.host else "N/A",
            "Datastore": [ds.name for ds in vm.datastore] if vm.datastore else "N/A",
            "ResourcePool": vm.resourcePool.name if vm.resourcePool else "N/A"
        }

        vm_list.append(vm_info)

        if vm_name:
            return vm_info

    return vm_list

def list_datacenter_children(si):
    """
    Lists all child objects under each Datacenter in the vCenter environment.
    """
    content = si.RetrieveContent()
    container = content.rootFolder
    datacenter_children = []

    # Iterate through all child entities in the rootFolder to find Datacenters
    for child_entity in container.childEntity:
        if isinstance(child_entity, vim.Datacenter):
            datacenter_info = {
                'Datacenter': child_entity.name,
                'Children': []
            }

            # Add vmFolder
            if child_entity.vmFolder:
                datacenter_info['Children'].append({
                    'Type': 'vmFolder',
                    'Name': child_entity.vmFolder.name,
                    'MoID': child_entity.vmFolder._moId
                })

            # Add datastoreFolder
            if child_entity.datastoreFolder:
                datacenter_info['Children'].append({
                    'Type': 'datastoreFolder',
                    'Name': child_entity.datastoreFolder.name,
                    'MoID': child_entity.datastoreFolder._moId
                })

            # Add networkFolder
            if child_entity.networkFolder:
                datacenter_info['Children'].append({
                    'Type': 'networkFolder',
                    'Name': child_entity.networkFolder.name,
                    'MoID': child_entity.networkFolder._moId
                })

            # Add hostFolder
            if child_entity.hostFolder:
                datacenter_info['Children'].append({
                    'Type': 'hostFolder',
                    'Name': child_entity.hostFolder.name,
                    'MoID': child_entity.hostFolder._moId
                })

            datacenter_children.append(datacenter_info)

    return datacenter_children

def list_folders(si):
    """
    Lists VM folders for each Datacenter in the vCenter environment,
    including the root vmFolder ("/") for each Datacenter and its subfolders.
    """
    # Get the vCenter Server UUID
    vcenter_uuid = get_vcenter_server_uuid(si)

    # List all child objects of Datacenters
    datacenter_children = list_datacenter_children(si)
    folder_identifiers = []

    for datacenter in datacenter_children:
        # Filter for the vmFolder element by its Type
        vm_folder = next((child for child in datacenter["Children"] if child["Type"] == "vmFolder"), None)
        if vm_folder:
            # Construct FolderIdentifier in the format <vcenter_uuid>.group-v<MoID>
            vm_folder_identifier = f"{vcenter_uuid}.{vm_folder['MoID']}"

            # Append the root folder ("/") for the current Datacenter
            folder_identifiers.append({
                "Datacenter": datacenter["Datacenter"],
                "Name": "/",
                "Identifier": vm_folder_identifier
            })

            # Recursively explore child folders under the root vmFolder
            folder_identifiers += explore_folder(vm_folder["MoID"], si, vcenter_uuid, datacenter["Datacenter"])

    return folder_identifiers

def explore_folder(folder_moid, si, vcenter_uuid, datacenter_name):
    """
    Recursively explores subfolders of a given folder by its MoID.
    """
    folder_identifiers = []

    # Retrieve the folder object via its MoID
    content = si.RetrieveContent()
    folder = next((item for item in content.viewManager.CreateContainerView(
        content.rootFolder, [vim.Folder], True).view if item._moId == folder_moid), None)

    if folder and hasattr(folder, 'childEntity'):
        for child in folder.childEntity:
            if isinstance(child, vim.Folder):
                # Construct FolderIdentifier
                child_moid = child._moId.split('-')[-1]
                folder_identifier = f"{vcenter_uuid}.group-v{child_moid}"

                folder_identifiers.append({
                    "Datacenter": datacenter_name,
                    "Name": child.name,
                    "Identifier": folder_identifier
                })

                # Recursively explore subfolders
                folder_identifiers += explore_folder(child._moId, si, vcenter_uuid, datacenter_name)

    return folder_identifiers

def find_folder_by_moid(moid):
    """
    Finds a folder object by its Managed Object ID (MoID) using the vSphere API.
    """
    # Implement folder lookup by MoID here if necessary.
    # This might involve iterating through folders in the environment.
    pass

def get_vm_scsi_identifiers(si, vm_name):
    content = si.RetrieveContent()
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
    
    vm_list = container.view
    for vm in vm_list:
        if vm.name == vm_name:
            scsi_devices = []
            for device in vm.config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualSCSIController):
                    for scsi_disk in device.device:
                        scsi_info = {
                            "device_key": scsi_disk,
                            "scsi_controller": device.deviceInfo.label,
                            "unit_number": device.scsiCtlrUnitNumber
                        }
                        scsi_devices.append(scsi_info)
            return scsi_devices
    return []

# List all volumes (disks) attached to a specific VM
def list_volumes(si, vm_name):
    content = si.RetrieveContent()
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
    
    vm_list = container.view
    volumes = []
    
    for vm in vm_list:
        if vm.name == vm_name:
            for device in vm.config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualDisk):  # Look for virtual disk devices
                    volume_info = {
                        "label": device.deviceInfo.label,
                        "backing": device.backing.fileName,
                        "controllerKey": device.controllerKey,
                        "unitNumber": device.unitNumber,
                        "diskMode": device.backing.diskMode,
                        "capacityInKB": device.capacityInKB,
                        "scsi_id": f"scsi:{device.controllerKey}:{device.unitNumber}"
                    }
                    volumes.append(volume_info)
    
    if not volumes:
        print(f"No volumes found for VM '{vm_name}'")
    return volumes

# Function to get the correct host system UUID
def list_host_system_uuid(si):
    content = si.RetrieveContent()
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True)
    hosts = container.view
    host_uuids = []

    for host in hosts:
        # Try retrieving systemInfo UUID
        if hasattr(host.hardware, 'systemInfo') and host.hardware.systemInfo:
            system_uuid = host.hardware.systemInfo.uuid
            host_uuids.append({
                "HostName": host.name,
                "SystemUUID": system_uuid
            })
        else:
            host_uuids.append({
                "HostName": host.name,
                "SystemUUID": "Unknown"
            })
    
    return host_uuids

# Additional methods for specific objects (e.g., volumes, clusters) can be added as needed

def power_off_vm(vcenter_connection, vm_identifier=None, vm_name=None):
    """
    Power off a VM using its identifier or name.
    
    Args:
        vcenter_connection: The vCenter connection object
        vm_identifier: The VM's identifier/moref (optional)
        vm_name: The VM's name (optional)
    """
    logging.info(f"Attempting to power off VM with identifier: {vm_identifier} or name: {vm_name}")
    try:
        # Get all VMs and print their details for debugging
        container = vcenter_connection.content.viewManager.CreateContainerView(
            vcenter_connection.content.rootFolder, [vim.VirtualMachine], True
        )
        all_vms = container.view
        logging.info("Available VMs in vCenter:")
        # for vm in all_vms:
        #     logging.info(f"VM Name: {vm.name}, MoRef ID: {vm._moId}")

        # Find VM by identifier or name
        if vm_identifier:
            # Parse the moRef ID from the identifier (e.g., "uuid.vm-9008" -> "vm-9008")
            mo_ref = vim.VirtualMachine(vm_identifier.split('.')[-1])
            mo_ref._moId = vm_identifier.split('.')[-1]
            vm = next((v for v in all_vms if v._moId == mo_ref._moId), None)
        elif vm_name:
            vm = next((v for v in all_vms if v.name == vm_name), None)
        else:
            raise ValueError("Either vm_identifier or vm_name must be provided")
        
        if vm is None:
            raise Exception(f"VM with identifier {vm_identifier} or name {vm_name} not found")
            
        if vm.runtime.powerState == 'poweredOn':
            logging.info(f"Powering off VM {vm.name}")
            task = vm.PowerOffVM_Task()
            WaitForTask(task)
            logging.info(f"Successfully powered off VM {vm.name}")
        else:
            logging.info(f"VM {vm.name} is already powered off")
            
    except Exception as e:
        logging.error(f"Failed to power off VM: {e}")
        raise

def power_on_vm(vcenter_connection, vm_identifier=None, vm_name=None):
    """
    Power on a VM using its identifier or name.
    
    Args:
        vcenter_connection: The vCenter connection object
        vm_identifier: The VM's identifier/moref (optional)
        vm_name: The VM's name (optional)
    """
    logging.info(f"Attempting to power on VM with identifier: {vm_identifier} or name: {vm_name}")
    try:
        # Get all VMs and print their details for debugging
        container = vcenter_connection.content.viewManager.CreateContainerView(
            vcenter_connection.content.rootFolder, [vim.VirtualMachine], True
        )
        all_vms = container.view
        logging.info("Available VMs in vCenter:")
        # for vm in all_vms:
        #     logging.info(f"VM Name: {vm.name}, MoRef ID: {vm._moId}")

        # Find VM by identifier or name
        if vm_identifier:
            # Parse the moRef ID from the identifier (e.g., "uuid.vm-9008" -> "vm-9008")
            mo_ref = vim.VirtualMachine(vm_identifier.split('.')[-1])
            mo_ref._moId = vm_identifier.split('.')[-1]
            vm = next((v for v in all_vms if v._moId == mo_ref._moId), None)
        elif vm_name:
            vm = next((v for v in all_vms if v.name == vm_name), None)
        else:
            raise ValueError("Either vm_identifier or vm_name must be provided")
        
        if vm is None:
            raise Exception(f"VM with identifier {vm_identifier} or name {vm_name} not found")
            
        if vm.runtime.powerState == 'poweredOff':
            logging.info(f"Powering on VM {vm.name}")
            task = vm.PowerOnVM_Task()
            WaitForTask(task)
            logging.info(f"Successfully powered on VM {vm.name}")
        else:
            logging.info(f"VM {vm.name} is already powered on")
            
    except Exception as e:
        logging.error(f"Failed to power on VM: {e}")
        raise