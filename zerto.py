import requests
import json
import logging
import sys
import ssl
import time

# Disable SSL warnings for self-signed certificates
context = ssl._create_unverified_context()
verifyCertificate = False  # Toggle SSL verification

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ZertoClient:
    def __init__(self, zvm_address, client_id, client_secret):
        self.zvm_address = zvm_address
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = self.__get_keycloak_token()

    def __get_keycloak_token(self):
        logging.debug(f'__get_keycloak_token(zvm_address={self.zvm_address})')
        keycloak_uri = f"https://{self.zvm_address}/auth/realms/zerto/protocol/openid-connect/token"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        body = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials'
        }

        try:
            logging.info("Connecting to Keycloak to get token...")
            response = requests.post(keycloak_uri, headers=headers, data=body, verify=verifyCertificate)
            response.raise_for_status()
            token = response.json().get('access_token')
            logging.info("Successfully retrieved token.")
            return token
        except requests.exceptions.RequestException as e:
            logging.error(f"Error retrieving token: {e}")
            sys.exit(1)

    def commit_vpg(self, vpg_settings_id, vpg_name, sync=False, expected_status=0):
        logging.debug(f'commit_vpg(zvm_address={self.zvm_address}, vpg_settings_id={vpg_settings_id}, vpg_name={vpg_name}, sync={sync})')
        commit_uri = f"https://{self.zvm_address}/v1/vpgSettings/{vpg_settings_id}/commit"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        try:
            response = requests.post(commit_uri, headers=headers, verify=verifyCertificate)
            response.raise_for_status()
            task_id = response.json()
            logging.info(f"VPGSettings {vpg_settings_id} successfully committed, {vpg_name} is created, task_id={task_id}")

            if sync:
                # Wait for task completion
                self.wait_for_task_completion(task_id, timeout=30, interval=5)
                logging.debug('sleeping 5 seconds ...')
                self.wait_for_vpg_ready(vpg_name=vpg_name, timeout=30, interval=5, expected_status=expected_status)

        except requests.exceptions.RequestException as e:
            logging.error(f"Error committing VPGSettings: {e}")
            sys.exit(1)

    def list_vpg_settings(self, vpg_settings_id=None):
        logging.debug(f'list_vpg_settings(zvm_address={self.zvm_address}, vpg_settings_id={vpg_settings_id})')
        if vpg_settings_id:
            vpg_settings_uri = f"https://{self.zvm_address}/v1/vpgSettings/{vpg_settings_id}"
        else:
            vpg_settings_uri = f"https://{self.zvm_address}/v1/vpgSettings"

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        try:
            logging.info(f"Fetching VPG settings from: {vpg_settings_uri}...")
            response = requests.get(vpg_settings_uri, headers=headers, verify=verifyCertificate)
            response.raise_for_status()
            vpg_settings = response.json()

            if not vpg_settings:
                logging.warning("No VPG settings found.")
                return []

            if vpg_settings_id:
                return vpg_settings

            return vpg_settings

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching VPG settings: {e}")
            sys.exit(1)

    # def list_vpgs(self, detailed=False, vpg_name=None):
    def list_vpgs(self, vpg_name=None):
        logging.debug(f'list_vpgs(zvm_address={self.zvm_address},vpg_name={vpg_name})')
        vpgs_uri = f"https://{self.zvm_address}/v1/vpgs"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        try:
            response = requests.get(vpgs_uri, headers=headers, verify=verifyCertificate)
            response.raise_for_status()
            vpgs = response.json()

            if not vpgs:
                logging.warning("No VPGs found.")
                return []

            if vpg_name:
                matching_vpg = next((vpg for vpg in vpgs if vpg.get("VpgName") == vpg_name), None)
                if not matching_vpg:
                    logging.warning(f"No VPG found with the name '{vpg_name}'")
                    return {}
                return matching_vpg

            return vpgs

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching VPGs: {e}")
            sys.exit(1)

    def create_vpg(self, payload, sync):
        vpg_name = payload.get("Basic", {}).get("Name")
        logging.debug(f'create_vpg(zvm_address={self.zvm_address}, vpg_name={vpg_name})')
        vpg_settings_id = self.create_vpg_settings(payload)
        self.commit_vpg(vpg_settings_id, vpg_name, sync, expected_status=2)

    def create_vpg_settings(self, payload):
        vpg_name = payload.get("Basic", {}).get("Name")
        vpg_identifier = payload.get("vpgIdentifier")
        logging.debug(f'create_vpg_settings(zvm_address={self.zvm_address}, vpg_identifier={vpg_identifier}, vpg_name={vpg_name})')
        vpg_settings_uri = f"https://{self.zvm_address}/v1/vpgSettings"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        try:
            response = requests.post(vpg_settings_uri, headers=headers, json=payload, verify=verifyCertificate)
            response.raise_for_status()
            vpg_settings_id = response.json()
            logging.info(f"VPGSettings ID: {vpg_settings_id} created")
            return vpg_settings_id
        except requests.exceptions.RequestException as e:
            logging.error(f"Error creating VPG settings: {e}")
            sys.exit(1)

    def wait_for_task_completion(self, task_identifier, timeout=600, interval=5):
        logging.debug(f'wait_for_task_completion(zvm_address={self.zvm_address}, task_identifier={task_identifier}, timeout={timeout}, interval={interval})')
        start_time = time.time()
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        while True:
            url = f"https://{self.zvm_address}/v1/tasks/{task_identifier}"
            response = requests.get(url, headers=headers, verify=verifyCertificate)
            response.raise_for_status()
            task_info = response.json()
            status = task_info.get("Status", {}).get("State", -1)
            progress = task_info.get("Status", {}).get("Progress", 0)
            logging.debug(f'Task response: status={status}, progress={progress}')

            if status == 6 and progress == 100:
                logging.info("Task completed successfully.")
                time.sleep(interval)
                return task_info
            elif status == 2:
                raise Exception(f"Task failed: {task_info.get('CompleteReason', 'No reason provided')}")

            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                raise TimeoutError("Task did not complete within the allotted time.")
            time.sleep(interval)

    def wait_for_vpg_ready(self, vpg_name, timeout=180, interval=5, expected_status=0):
        logging.debug(f'wait_for_vpg_ready(zvm_address={self.zvm_address}, vpg_name={vpg_name}, timeout={timeout}, interval={interval})')
        start_time = time.time()

        while True:
            time.sleep(interval)
            vpg_info = self.list_vpgs(vpg_name=vpg_name)
            logging.debug(f'vpg_info={json.dumps(vpg_info)}')
            vpg_status = vpg_info.get("Status")
            logging.debug(f"Checking VPG status for {vpg_name}: Current status = {vpg_status}")

            if vpg_status == expected_status: 
                logging.info(f"VPG {vpg_name} is now in the expected state.")
                return vpg_info

            # Check if the timeout has been reached
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                raise TimeoutError(f"VPG {vpg_name} did not reach the ready state within the allotted time.")

    def add_vm_to_vpg(self, vpg_name, vm_list):
        logging.debug(f'add_vm_to_vpg(zvm_address={self.zvm_address}, vpg_name={vpg_name})')
        vpg = self.list_vpgs(vpg_name=vpg_name)
        
        if not vpg:
            logging.error(f"VPG with name '{vpg_name}' not found.")
            return

        vpg_identifier = vpg['VpgIdentifier']
        logging.info(f"Found VPG '{vpg_name}' with Identifier: {vpg_identifier}")

        vpg_settings_payload = {
            "vpgIdentifier": vpg_identifier,
            "Basic": {
                "Name": vpg_name
            }
        }
        new_vpg_settings_id = self.create_vpg_settings(vpg_settings_payload)

        logging.info(f"Adding VMs to VPGSettings ID: {new_vpg_settings_id}")
        vms_uri = f"https://{self.zvm_address}/v1/vpgSettings/{new_vpg_settings_id}/vms"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        try:
            response = requests.post(vms_uri, headers=headers, json=vm_list, verify=verifyCertificate)
            response.raise_for_status()
            logging.info(f"Successfully added VMs to VPG {new_vpg_settings_id}.")
            self.commit_vpg(new_vpg_settings_id, vpg_name, sync=True, expected_status=0)

        except requests.exceptions.RequestException as e:
            logging.error(f"Error adding VMs to VPG: {e}")
            sys.exit(1)

    def remove_vm_from_vpg(self, vpg_name, vm_identifier):
        logging.debug(f'remove_vm_from_vpg(zvm_address={self.zvm_address}, vpg_name={vpg_name}, vm_identifier={vm_identifier})')
        vpg = self.list_vpgs(vpg_name=vpg_name)

        if not vpg:
            logging.error(f"VPG with name '{vpg_name}' not found.")
            return

        vpg_id = vpg['VpgIdentifier']
        logging.info(f"Found VPG '{vpg_name}' with Identifier: {vpg_id}")

        vpg_settings_payload = {
            "vpgIdentifier": vpg_id,
            "Basic": {
                "Name": vpg_name
            }
        }
        new_vpg_settings_id = self.create_vpg_settings(vpg_settings_payload)
        remove_vm_uri = f"https://{self.zvm_address}/v1/vpgSettings/{new_vpg_settings_id}/vms/{vm_identifier}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        try:
            response = requests.delete(remove_vm_uri, headers=headers, verify=verifyCertificate)
            response.raise_for_status()
            logging.info(f"VM {vm_identifier} successfully removed from VPG '{vpg_name}' (ID: {new_vpg_settings_id}).")
            self.commit_vpg(new_vpg_settings_id, vpg_name, sync=True, expected_status=0)

        except requests.exceptions.RequestException as e:
            logging.error(f"Error removing VM from VPG: {e}")
            sys.exit(1)

    def delete_vpg(self, vpg_name, force=False, keep_recovery_volumes=True):
        """
        Deletes a VPG by its name.

        :param vpg_name: The name of the VPG to delete.
        :return: Success message if deleted, else an error message.
        """
        logging.debug(f"delete_vpg(vpg_name={vpg_name})")

        # Step 1: Retrieve the VPG details using the VPG name
        vpg = self.list_vpgs(vpg_name=vpg_name)

        if not vpg:
            logging.error(f"No VPG found with the name '{vpg_name}'.")
            return

        # Get the VPG Identifier
        vpg_identifier = vpg.get("VpgIdentifier")
        if not vpg_identifier:
            logging.error(f"Could not retrieve Identifier for VPG '{vpg_name}'.")
            return

        # Step 2: Construct the DELETE request URL
        delete_vpg_uri = f"https://{self.zvm_address}/v1/vpgs/{vpg_identifier}"

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        payload = {
            "keepRecoveryVolumes": force,
            "force": keep_recovery_volumes
        }

        try:
            # Step 3: Send DELETE request
            response = requests.delete(delete_vpg_uri, headers=headers, json=payload, verify=verifyCertificate)

            response.raise_for_status()  # Ensure the request was successful
            logging.info(f"Successfully deleted VPG '{vpg_name}' (ID: {vpg_identifier}).")
            return f"VPG '{vpg_name}' deleted successfully."

        except requests.exceptions.RequestException as e:
            logging.error(f"Error deleting VPG '{vpg_name}': {e}")
            return f"Failed to delete VPG '{vpg_name}'."
