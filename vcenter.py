import ssl
import atexit
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
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

# Function to list all resource pools
def list_resource_pools(si):
    content = si.RetrieveContent()
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.ResourcePool], True)
    resource_pools = container.view
    resource_pool_list = []
    for pool in resource_pools:
        resource_pool_info = {
            "Name": pool.name,
            "Identifier": pool._moId
        }
        resource_pool_list.append(resource_pool_info)
    return resource_pool_list

# Function to list all networks
def list_networks(si):
    content = si.RetrieveContent()
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.Network], True)
    networks = container.view
    network_list = []
    for network in networks:
        network_info = {
            "Name": network.name,
            "Identifier": network._moId
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

# Function to list all folders with the correct identifier format
def list_folders(si):
    # Get the vCenter Server UUID
    vcenter_uuid = get_vcenter_server_uuid(si)

    content = si.RetrieveContent()
    container = content.rootFolder
    viewType = [vim.Folder]
    recursive = True
    containerView = content.viewManager.CreateContainerView(container, viewType, recursive)

    folders = containerView.view
    folder_identifiers = []

    for folder in folders:
        # Get the MoID of the folder
        folder_moid = folder._moId.split('-')[-1]

        # Construct FolderIdentifier in the correct format: <vcenter_uuid>.group-v<MoID>
        folder_identifier = f"{vcenter_uuid}.group-v{folder_moid}"

        # Collect folder information
        folder_identifiers.append({
            'Name': folder.name,
            'Identifier': folder_identifier
        })

    return folder_identifiers

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

# Function to get the vCenter server's instance UUID
def get_vcenter_server_uuid(si):
    content = si.RetrieveContent()

    # The vCenter instance UUID is part of the 'about' information
    vcenter_uuid = content.about.instanceUuid  # This should be the system-wide UUID you're looking for
    return vcenter_uuid


# Additional methods for specific objects (e.g., volumes, clusters) can be added as needed
