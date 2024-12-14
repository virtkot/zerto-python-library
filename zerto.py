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
import requests
import json
import logging
import sys
import ssl
import time
from datetime import datetime
import pytz

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

    def __convert_datetime_to_timestamp(self, date_str):
        logging.debug(f'__convert_datetime_to_timestamp date_str={date_str}')
        
        # Parse the input date string to a naive datetime object (local time)
        local_dt = datetime.strptime(date_str, "%B %d, %Y %I:%M:%S %p")
        
        # Define the local timezone (e.g., Central Time)
        local_tz = pytz.timezone('America/Chicago')
        
        # Localize the datetime object to the local timezone
        local_dt = local_tz.localize(local_dt)
        
        # Convert the localized datetime object to UTC
        utc_dt = local_dt.astimezone(pytz.utc)
        
        # Format the UTC datetime object to the required string format
        timestamp = utc_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        logging.debug(f'__convert_datetime_to_timestamp timestamp={timestamp}')
        
        return timestamp

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
            logging.error(f"HTTPError: {e.response.status_code} - {e.response.reason}")
            try:
                error_details = e.response.json()
                logging.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except ValueError:
                logging.error(f"Response content: {e.response.text}")
            raise

        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            raise
        # except requests.exceptions.RequestException as e:
        #     logging.error(f"Error fetching VPG settings: {e}")
        #     sys.exit(1)

###########################    VPGS Virtual Protection Groups    #######################
#      Manage VPGs and performs Recovery operations
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
            logging.error(f"HTTPError: {e.response.status_code} - {e.response.reason}")
            try:
                error_details = e.response.json()
                logging.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except ValueError:
                logging.error(f"Response content: {e.response.text}")
            raise

        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            raise
        # except requests.exceptions.RequestException as e:
        #     logging.error(f"Error fetching VPGs: {e}")
        #     sys.exit(1)

    def create_vpg(self, payload, sync):
        vpg_name = payload.get("Basic", {}).get("Name")
        logging.debug(f'create_vpg(zvm_address={self.zvm_address}, vpg_name={vpg_name})')
        vpg_settings_id = self.create_vpg_settings(payload)
        self.commit_vpg(vpg_settings_id, vpg_name, sync, expected_status=2)

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

    def failover_test(self, vpg_name, checkpoint_identifier=None, vm_name_list=None, sync=None):
        """
        Initiate a failover test for a given VPG by its name.

        :param vpg_name: The name of the VPG.
        :param checkpoint_identifier: checkpoint_identifier can be recived by list_checkpoint, if not provided uses the latest checkpoint.
        :param vm_name_list: List of 
        :param options: Optional parameters for the failover test.
        :return: Response from the Zerto API.
        """
        logging.debug(f'failover_test(zvm_address={self.zvm_address}, vpg_name={vpg_name})')

        # Retrieve the VPG identifier using the VPG name
        vpg_info = self.list_vpgs(vpg_name=vpg_name)
        vpg_identifier = vpg_info['VpgIdentifier']
        logging.info(f"Found VPG '{vpg_name}' with Identifier: {vpg_identifier}")

        url = f"https://{self.zvm_address}/v1/vpgs/{vpg_identifier}/FailoverTest"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        payload = {}
        if checkpoint_identifier: payload['CheckpointIdentifier'] = checkpoint_identifier

        vm_identifier_list = []
        if vm_name_list:
            
            for vm in vm_name_list:
                vm_info = self.list_vms(vm_name=vm)
                if not vm_info:
                    logging.error (f'failover_test vm={vm} not found')
                    return
                vm_identifier_list.append(vm_info[0]['VmIdentifier'])
        
        payload['VmIdentifiers'] = vm_identifier_list

        try:
            logging.info(f"Initiating failover test for VPG '{vpg_name}', payload={payload}")
            response = requests.post(url, headers=headers, json=payload, verify=verifyCertificate)
            response.raise_for_status()
            task_id = response.json()

            logging.info(f"Failover test initiated for VPG {vpg_name}, task_id = {task_id}")

            if sync:
                # Wait for task completion
                self.wait_for_task_completion(task_id, timeout=30, interval=5)
            return response.json()

        except requests.exceptions.RequestException as e:
            logging.error(f"Error initiating failover test for VPG '{vpg_name}': {e}")
            sys.exit(1)

    def stop_failover_test(self, vpg_name, sync=None):
        """
        Stop a failover test for a given VPG by its name.

        :param vpg_name: The name of the VPG.
        :param sync: wait until task is completed.

        """
        logging.debug(f'stop_failover_test(zvm_address={self.zvm_address}, vpg_name={vpg_name}, sync={sync})')

        # Retrieve the VPG identifier using the VPG name
        vpg_info = self.list_vpgs(vpg_name=vpg_name)
        vpg_identifier = vpg_info['VpgIdentifier']
        logging.info(f"Found VPG '{vpg_name}' with Identifier: {vpg_identifier}")

        url = f"https://{self.zvm_address}/v1/vpgs/{vpg_identifier}/FailoverTestStop"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        try:
            logging.info(f"Stopping failover test for VPG '{vpg_name}'...")
            response = requests.post(url, headers=headers, verify=verifyCertificate)
            response.raise_for_status()
            task_id = response.json()

            logging.info(f"Failover test stopping for VPG {vpg_name}, task_id = {task_id}")

            if sync:
                # Wait for task completion
                self.wait_for_task_completion(task_id, timeout=30, interval=5)
            return response.json()

        except requests.exceptions.RequestException as e:
            logging.error(f"Error stopping failover test for VPG '{vpg_name}': {e}")
            sys.exit(1)

    def rollback_failover(self, vpg_name, sync=None):
        """
        Rollback failover for a given VPG by its name.

        :param vpg_name: The name of the VPG.
        :param sync: wait until task is completed.

        """
        logging.debug(f'rollback_failover(zvm_address={self.zvm_address}, vpg_name={vpg_name}, sync={sync})')

        # Retrieve the VPG identifier using the VPG name
        vpg_info = self.list_vpgs(vpg_name=vpg_name)
        vpg_identifier = vpg_info['VpgIdentifier']
        logging.info(f"Found VPG '{vpg_name}' with Identifier: {vpg_identifier}")

        url = f"https://{self.zvm_address}/v1/vpgs/{vpg_identifier}/FailoverRollback"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        try:
            logging.info(f"Rollback failover for VPG '{vpg_name}'...")
            response = requests.post(url, headers=headers, verify=verifyCertificate)
            response.raise_for_status()
            task_id = response.json()

            logging.info(f"Rollback faolover for VPG {vpg_name}, task_id = {task_id}")

            if sync:
                # Wait for task completion
                self.wait_for_task_completion(task_id, timeout=30, interval=5)
            return response.json()

        except requests.exceptions.RequestException as e:
            logging.error(f"Error stopping failover test for VPG '{vpg_name}': {e}")
            sys.exit(1)

    def commit_failover(self, vpg_name, is_reverse_protection=False, sync=None):
        """
        Commit failover for a given VPG by its name.

        :param vpg_name: The name of the VPG.
        :param is_reverse_protection: If True, enables reverse protection.
        :param sync: wait until task is completed.

        """
        logging.debug(f'commit_failover(zvm_address={self.zvm_address}, vpg_name={vpg_name}, is_reverse_protection={is_reverse_protection}, sync={sync})')

        # Retrieve the VPG identifier using the VPG name
        vpg_info = self.list_vpgs(vpg_name=vpg_name)
        vpg_identifier = vpg_info['VpgIdentifier']
        logging.info(f"Found VPG '{vpg_name}' with Identifier: {vpg_identifier}")

        payload = {}
        payload['isReverseProtection'] = is_reverse_protection

        url = f"https://{self.zvm_address}/v1/vpgs/{vpg_identifier}/FailoverCommit"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        try:
            logging.info(f"Rollback failover for VPG '{vpg_name}'...")
            response = requests.post(url, headers=headers, json=payload, verify=verifyCertificate)
            response.raise_for_status()
            task_id = response.json()

            logging.info(f"Rollback faolover for VPG {vpg_name}, task_id = {task_id}")

            if sync:
                # Wait for task completion
                self.wait_for_task_completion(task_id, timeout=120, interval=5)
            return response.json()

        except requests.exceptions.RequestException as e:
            logging.error(f"Error stopping failover test for VPG '{vpg_name}': {e}")
            sys.exit(1)

    def failover(self, vpg_name, checkpoint_identifier=None, vm_name_list=None, commit_policy=0, time_to_wait_before_shutdown_sec=3600,
                 shutdown_policy=0, is_reverse_protection=False, sync=None):
        """
        Initiate a failover test for a given VPG by its name.

        :param vpg_name: The name of the VPG.
        :param checkpoint_identifier: checkpoint_identifier can be recived by list_checkpoint, if not provided uses the latest checkpoint.
        :param vm_name_list: List of vm names
        :param shutdown_policy: shutdown policy, 0 - None, 1 - Shutdown, 2 - ForceShutdown
        :param commit_policy: commit policy, 0 - Rollback, 1 - Commit, 2 - None
        :param time_to_wait_before_shutdown_sec: time to wait before shutdown in sec
        :param is_reverse_protection: if True, enables reverse protection
        :return: Response from the Zerto API.
        """
        logging.debug(f'failover_test(zvm_address={self.zvm_address}, vpg_name={vpg_name})')

        # Retrieve the VPG identifier using the VPG name
        vpg_info = self.list_vpgs(vpg_name=vpg_name)
        vpg_identifier = vpg_info['VpgIdentifier']
        logging.info(f"Found VPG '{vpg_name}' with Identifier: {vpg_identifier}")

        url = f"https://{self.zvm_address}/v1/vpgs/{vpg_identifier}/Failover"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        # Building query parameters for general alerts retrieval
        payload = {}
        if checkpoint_identifier:
            payload["checkpointIdentifier"] = checkpoint_identifier
        # if commit_policy:
        payload["commitPolicy"] = commit_policy
        # if time_to_wait_before_shutdown_sec:
        payload["timeToWaitBeforeShutdownInSec"] = time_to_wait_before_shutdown_sec
        # if shutdown_policy:
        payload["shutdownPolicy"] = shutdown_policy
        # if is_reverse_protection:
        payload["isReverseProtection"] = is_reverse_protection

        vm_identifier_list = []
        if vm_name_list:
            for vm in vm_name_list:
                vm_info = self.list_vms(vm_name=vm)
                # logging.debug(f'vm_info={vm_info}')
                if not vm_info:
                    logging.error (f'failover_test vm={vm} not found')
                    return
                vm_identifier_list.append(vm_info[0]['VmIdentifier'])
        
        payload['vmIdentifiers'] = vm_identifier_list

        try:
            logging.info(f"Initiating failover for VPG '{vpg_name}', VpgId={vpg_identifier}, payload={payload}")
            response = requests.post(url, headers=headers, json=payload, verify=verifyCertificate)
            response.raise_for_status()
            task_id = response.json()

            logging.info(f"Failover initiated for VPG {vpg_name}, VpgId={vpg_identifier}, task_id = {task_id}")

            if sync:
                # Wait for task completion
                self.wait_for_task_completion(task_id, timeout=120, interval=5)
            return response.json()

        except requests.exceptions.RequestException as e:
            logging.error(f"Error initiating failover test for VPG '{vpg_name}': {e}")
            sys.exit(1)

    def list_failover_shutdown_policies(self):
        """
        Fetches the available failover shoutdown policies from the Zerto API.

        :return: List of available failover shoutdown policies or an error message if the request fails.
        """
        logging.debug('list_failover_shutdown_policies()')
        
        # Construct the URL for fetching alert levels
        alert_levels_uri = f"https://{self.zvm_address}/v1/vpgs/failovershutdownpolicies"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        try:
            logging.info("Fetching available failover shoutdown policies...")
            response = requests.get(alert_levels_uri, headers=headers, verify=verifyCertificate)
            response.raise_for_status()
            alert_levels = response.json()

            if not alert_levels:
                logging.warning("No failover shoutdown policies found.")
                return []

            return alert_levels

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching alert levels: {e}")
            return None

    def list_failover_commit_policies(self):
        """
        Fetches the available faolover commit  policies from the Zerto API.

        :return: List of available failover commit  policies or an error message if the request fails.
        """
        logging.debug('list_failover_commit_policies()')
        
        # Construct the URL for fetching failover commit policies
        alert_levels_uri = f"https://{self.zvm_address}/v1/vpgs/failovercommitpolicies"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        try:
            logging.info("Fetching available failover commit policies...")
            response = requests.get(alert_levels_uri, headers=headers, verify=verifyCertificate)
            response.raise_for_status()
            alert_levels = response.json()

            if not alert_levels:
                logging.warning("No failover commit policies found.")
                return []

            return alert_levels

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching alert levels: {e}")
            return None

    def list_checkpoints(self, vpg_name, start_date=None, endd_date=None, checkpoint_date_str=None, latest=None):
        """
        Fetches a list of checkpoints for a specified Virtual Protection Group (VPG).
        
        Parameters:
            vpg_name (str): The name of the Virtual Protection Group (VPG) to fetch checkpoints for.
            start_date (str): The start date for filtering checkpoints, in ISO 8601 format (e.g., '2024-11-13T00:00:00Z').
            endd_date (str): The end date for filtering checkpoints, in ISO 8601 format (e.g., '2024-11-14T00:00:00Z').
            checkpoint_date_str (str): A specific date string in the format 'Month Day, Year HH:MM:SS AM/PM'
                                    (e.g., 'November 13, 2024 1:43:02 PM') to search for an exact checkpoint.
            latest (bool): If True, returns the checkpoint with the most recent timestamp.

        Returns:
            dict: A single checkpoint that matches `checkpoint_date_str` or the latest checkpoint if `latest=True`.
            list: The full list of checkpoints if neither `checkpoint_date_str` nor `latest` is specified.
            None: If no matching checkpoint is found or an error occurs.
        
        Raises:
            SystemExit: If a request exception occurs during the API call.
        """        
        logging.debug(f'list_checkpoints(zvm_address={self.zvm_address},vpg_name={vpg_name}, start_date={start_date}, endd_date={endd_date}, checkpoint_date_str={checkpoint_date_str}, latest={latest})')
        vpgid = (self.list_vpgs(vpg_name=vpg_name))['VpgIdentifier']
        vpgs_uri = f"https://{self.zvm_address}/v1/vpgs/{vpgid}/checkpoints"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        params = {
            "startDate": start_date,
            "endDate": endd_date
        }
        try:
            response = requests.get(vpgs_uri, headers=headers, params=params, verify=verifyCertificate)
            response.raise_for_status()
            checkpoints = response.json()

            if not checkpoints:
                logging.warning("No checkpoints found.")
                return []

            if checkpoint_date_str:
                check_point_timestamp = self.__convert_datetime_to_timestamp(date_str = checkpoint_date_str)
                matching_checkpoints = next((checkpoint for checkpoint in checkpoints if checkpoint.get("TimeStamp") == check_point_timestamp), None)
                if not check_point_timestamp:
                    logging.warning(f"No checkpoint {checkpoint_date_str} found")
                    return {}
                return matching_checkpoints
            
            if latest:
                # Find the checkpoint with the most recent timestamp
                latest_checkpoint = max(checkpoints, key=lambda x: x.get("TimeStamp"))
                logging.debug(f"Latest checkpoint found: {latest_checkpoint}")
                return latest_checkpoint  

            return checkpoints

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching checkpoints: {e}")
            sys.exit(1)

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

###########################          ALERTS         #######################
#      Manage ZVM Alerts
    def get_alerts(self, start_date=None, end_date=None, vpg_identifier=None, zorg_identifier=None,
                   site_identifier=None, level=None, entity=None, help_identifier=None, is_dismissed=None,
                   alert_identifier=None):
        """
        Fetches alerts from the Zerto API with optional filters or a specific alert if `alert_identifier` is provided.

        :param start_date: The filter interval start date-time (string in date-time format).
        :param end_date: The filter interval end date-time (string in date-time format).
        :param vpg_identifier: The identifier of the VPG.
        :param zorg_identifier: The identifier of the ZORG.
        :param site_identifier: The internal ZVM site identifier.
        :param level: The alert level.
        :param entity: The alert entity type.
        :param help_identifier: The alert help identifier associated with the alert.
        :param is_dismissed: True if alert was dismissed.
        :param alert_identifier: The specific alert identifier to retrieve a single alert.
        :return: List of alerts or a specific alert based on the provided filters.
        """
        if alert_identifier:
            alerts_uri = f"https://{self.zvm_address}/v1/alerts/{alert_identifier}"
        else:
            alerts_uri = f"https://{self.zvm_address}/v1/alerts"

        logging.debug(f'get_alerts(alert_identifier={alert_identifier}, start_date={start_date}, end_date={end_date}, '
                      f'vpg_identifier={vpg_identifier}, zorg_identifier={zorg_identifier}, site_identifier={site_identifier}, '
                      f'level={level}, entity={entity}, help_identifier={help_identifier}, is_dismissed={is_dismissed})')
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }
        
        # Building query parameters for general alerts retrieval
        params = {}
        if not alert_identifier:
            if start_date:
                params['startDate'] = start_date
            if end_date:
                params['endDate'] = end_date
            if vpg_identifier:
                params['vpgIdentifier'] = vpg_identifier
            if zorg_identifier:
                params['zorgIdentifier'] = zorg_identifier
            if site_identifier:
                params['siteIdentifier'] = site_identifier
            if level:
                params['level'] = level
            if entity:
                params['entity'] = entity
            if help_identifier:
                params['helpIdentifier'] = help_identifier
            if is_dismissed is not None:
                params['isDismissed'] = str(is_dismissed).lower()

        try:
            logging.info("Fetching alerts...")
            response = requests.get(alerts_uri, headers=headers, params=params, verify=verifyCertificate)
            response.raise_for_status()
            alerts = response.json()

            if not alerts:
                logging.warning("No alerts found.")
                return []

            return alerts

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching alerts: {e}")
            return None

    def dismiss_alert(self, alert_identifier):
        """
        Dismisses a specific alert by its identifier.

        :param alert_identifier: The identifier of the alert to be dismissed.
        :return: Success message if the alert was dismissed, else an error message.
        """
        logging.debug(f'dismiss_alert(alert_identifier={alert_identifier})')
        
        # Construct the URL for dismissing the alert
        dismiss_uri = f"https://{self.zvm_address}/v1/alerts/{alert_identifier}/dismiss"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        try:
            logging.info(f"Attempting to dismiss alert with ID: {alert_identifier}")
            response = requests.post(dismiss_uri, headers=headers, verify=verifyCertificate)
            response.raise_for_status()

            if response.status_code == 200:
                logging.info(f"Alert {alert_identifier} successfully dismissed.")
                return f"Alert {alert_identifier} dismissed successfully."
            else:
                logging.warning(f"Unexpected response code: {response.status_code}")
                return f"Alert {alert_identifier} dismissal returned an unexpected status."

        except requests.exceptions.RequestException as e:
            logging.error(f"Error dismissing alert {alert_identifier}: {e}")
            return f"Failed to dismiss alert {alert_identifier}."

    def undismiss_alert(self, alert_identifier):
        """
        Undismisses a specific alert by its identifier.

        :param alert_identifier: The identifier of the alert to be dismissed.
        :return: Success message if the alert was dismissed, else an error message.
        """
        logging.debug(f'undismiss_alert(alert_identifier={alert_identifier})')
        
        # Construct the URL for dismissing the alert
        undismiss_uri = f"https://{self.zvm_address}/v1/alerts/{alert_identifier}/undismiss"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        try:
            logging.info(f"Attempting to undismiss alert with ID: {alert_identifier}")
            response = requests.post(undismiss_uri, headers=headers, verify=verifyCertificate)
            response.raise_for_status()

            if response.status_code == 200:
                logging.info(f"Alert {alert_identifier} successfully undismissed.")
                return f"Alert {alert_identifier} undismissed successfully."
            else:
                logging.warning(f"Unexpected response code: {response.status_code}")
                return f"Alert {alert_identifier} undismissal returned an unexpected status."

        except requests.exceptions.RequestException as e:
            logging.error(f"Error undismissing alert {alert_identifier}: {e}")
            return f"Failed to undismiss alert {alert_identifier}."

    def get_alert_levels(self):
        """
        Fetches the available alert levels from the Zerto API.

        :return: List of alert levels or an error message if the request fails.
        """
        logging.debug('get_alert_levels()')
        
        # Construct the URL for fetching alert levels
        alert_levels_uri = f"https://{self.zvm_address}/v1/alerts/levels"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        try:
            logging.info("Fetching available alert levels...")
            response = requests.get(alert_levels_uri, headers=headers, verify=verifyCertificate)
            response.raise_for_status()
            alert_levels = response.json()

            if not alert_levels:
                logging.warning("No alert levels found.")
                return []

            return alert_levels

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching alert levels: {e}")
            return None

    def get_alert_entities(self):
        """
        Fetches the available alert entities from the Zerto API.

        :return: List of alert entities or an error message if the request fails.
        """
        logging.debug('get_alert_entities()')
        
        # Construct the URL for fetching alert entities
        alert_entities_uri = f"https://{self.zvm_address}/v1/alerts/entities"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        try:
            logging.info("Fetching available alert entities...")
            response = requests.get(alert_entities_uri, headers=headers, verify=verifyCertificate)
            response.raise_for_status()
            alert_entities = response.json()

            if not alert_entities:
                logging.warning("No alert entities found.")
                return []

            return alert_entities

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching alert entities: {e}")
            return None

    def get_alert_help_identifiers(self):
        """
        Fetches the available alert help identifiers from the Zerto API.

        :return: List of alert help identifiers or an error message if the request fails.
        """
        logging.debug('get_alert_help_identifiers()')
        
        # Construct the URL for fetching alert help identifiers
        help_identifiers_uri = f"https://{self.zvm_address}/v1/alerts/helpidentifiers"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        try:
            logging.info("Fetching available alert help identifiers...")
            response = requests.get(help_identifiers_uri, headers=headers, verify=verifyCertificate)
            response.raise_for_status()
            help_identifiers = response.json()

            if not help_identifiers:
                logging.warning("No alert help identifiers found.")
                return []

            return help_identifiers

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching alert help identifiers: {e}")
            return None

###########################          DATASTORES         #######################
#      Get information about datastores available on the current site
    def list_datastores(self, datastore_identifier=None):
        """
        Retrieves a list of all datastores or information about a specific datastore if an identifier is provided.

        :param datastore_identifier: Optional identifier of the datastore.
        :return: List of all datastores or details of a specific datastore.
        """
        if datastore_identifier:
            logging.debug(f'get_datastores(zvm_address={self.zvm_address}, datastore_identifier={datastore_identifier})')
            datastores_uri = f"https://{self.zvm_address}/v1/datastores/{datastore_identifier}"
        else:
            logging.debug(f'get_datastores(zvm_address={self.zvm_address})')
            datastores_uri = f"https://{self.zvm_address}/v1/datastores"

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        try:
            response = requests.get(datastores_uri, headers=headers, verify=verifyCertificate)
            response.raise_for_status()
            datastores = response.json()

            if not datastores:
                logging.warning(f"No datastores found for identifier {datastore_identifier}" if datastore_identifier else "No datastores found.")
                return [] if not datastore_identifier else {}

            logging.info(f"Successfully retrieved {'datastore' if datastore_identifier else 'datastores'}.")
            return datastores

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching {'datastore' if datastore_identifier else 'datastores'}: {e}")
            return None

###########################          EVENTS         #######################
#     Manage ZVM Events
    def list_events(self, event_identifier=None, start_date=None, end_date=None, vpg_identifier=None,
                    site_name=None, site_identifier=None, zorg_identifier=None, event_type=None,
                    entity_type=None, category=None, user_name=None, alert_identifier=None):
        """
        Fetches a list of events or a specific event from the Zerto API with optional filters.

        :param event_identifier: The identifier of the specific event (if fetching a specific event).
        :param start_date: The filter interval start date-time (string in date-time format).
        :param end_date: The filter interval end date-time (string in date-time format).
        :param vpg_identifier: The identifier of the VPG.
        :param site_name: The name of the site.
        :param site_identifier: The internal ZVM site identifier.
        :param zorg_identifier: The identifier of the ZORG.
        :param event_type: The event type.
        :param entity_type: The entity type to return.
        :param category: The event category to return.
        :param user_name: The username for which the event occurred.
        :param alert_identifier: The alert identifier.
        :return: List of events or a specific event based on provided filters.
        """
        logging.debug(f'list_events(event_identifier={event_identifier}, start_date={start_date}, end_date={end_date}, '
                    f'vpg_identifier={vpg_identifier}, site_name={site_name}, site_identifier={site_identifier}, '
                    f'zorg_identifier={zorg_identifier}, event_type={event_type}, entity_type={entity_type}, '
                    f'category={category}, user_name={user_name}, alert_identifier={alert_identifier})')
        
        # Determine endpoint based on whether event_identifier is provided
        if event_identifier:
            events_uri = f"https://{self.zvm_address}/v1/events/{event_identifier}"
        else:
            events_uri = f"https://{self.zvm_address}/v1/events"

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }
        
        # Building query parameters
        params = {}
        if start_date:
            params['startDate'] = start_date
        if end_date:
            params['endDate'] = end_date
        if vpg_identifier:
            params['vpgIdentifier'] = vpg_identifier
        if site_name:
            params['siteName'] = site_name
        if site_identifier:
            params['siteIdentifier'] = site_identifier
        if zorg_identifier:
            params['zorgIdentifier'] = zorg_identifier
        if event_type:
            params['eventType'] = event_type
        if entity_type:
            params['entityType'] = entity_type
        if category:
            params['category'] = category
        if user_name:
            params['userName'] = user_name
        if alert_identifier:
            params['alertIdentifier'] = alert_identifier

        try:
            logging.info("Fetching events with specified filters...")
            response = requests.get(events_uri, headers=headers, params=params, verify=verifyCertificate)
            response.raise_for_status()
            events = response.json()

            if not events:
                logging.warning("No events found.")
                return []

            return events

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching events: {e}")
            return None

    def list_event_types(self):
        """
        Fetches a list of event types from the Zerto API.

        :return: List of event types.
        """
        logging.debug(f'list_event_types(zvm_address={self.zvm_address})')
        event_types_uri = f"https://{self.zvm_address}/v1/events/types"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        try:
            logging.info("Fetching event types...")
            response = requests.get(event_types_uri, headers=headers, verify=verifyCertificate)
            response.raise_for_status()
            event_types = response.json()

            if not event_types:
                logging.warning("No event types found.")
                return []

            return event_types

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching event types: {e}")
            return None

    def list_event_entities(self):
        """
        Fetches a list of event entities from the Zerto API.

        :return: List of event entities.
        """
        logging.debug(f'list_event_entities(zvm_address={self.zvm_address})')
        event_entities_uri = f"https://{self.zvm_address}/v1/events/entities"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        try:
            logging.info("Fetching event entities...")
            response = requests.get(event_entities_uri, headers=headers, verify=verifyCertificate)
            response.raise_for_status()
            event_entities = response.json()

            if not event_entities:
                logging.warning("No event entities found.")
                return []

            return event_entities

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching event entities: {e}")
            return None

    def list_event_categories(self):
        """
        Fetches a list of event categories from the Zerto API.

        :return: List of event categories.
        """
        logging.debug(f'list_event_categories(zvm_address={self.zvm_address})')
        event_categories_uri = f"https://{self.zvm_address}/v1/events/categories"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        try:
            response = requests.get(event_categories_uri, headers=headers, verify=verifyCertificate)
            response.raise_for_status()
            event_categories = response.json()

            if not event_categories:
                logging.warning("No event categories found.")
                return []

            return event_categories

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching event categories: {e}")
            return None

###########################          FILE LEVEL RESTORE         #######################
#     Get all mounted volumes. Results can be filtered by a VM identifier. (Auth)
    def initiate_file_level_restore(self, vpg_name, vm_name, initial_download_path, checkpoint_id=None):
        logging.debug(f'initiate_file_level_restore(zvm_address={self.zvm_address}, vpg_name={vpg_name}, vm_name={vm_name}, initial_download_path={initial_download_path})')

        try:
            # Fetch VPG ID
            vpg = self.list_vpgs(vpg_name=vpg_name)
            vpg_id = vpg['VpgIdentifier']

            # Get checkpoint if not provided
            if not checkpoint_id:
                checkpoint = self.list_checkpoints(vpg_name=vpg_name, latest=True)
                checkpoint_id = checkpoint['CheckpointIdentifier']
                logging.debug(f'checkpoint_id={checkpoint_id}')

            # Fetch VM details
            vm = self.list_vms(vm_name=vm_name)
            # logging.debug(f'vm={vm}')
            vm_id = vm[0]['VmIdentifier']
            
            # if not vm[0]['EnabledActions']['IsFlrEnabled']:
            #     logging.error(f"File-level restore is not enabled for VM {vm_name}.")
            #     raise Exception(f"FLR not enabled for VM {vm_name}")

            # Build the payload
            flr_payload = {
                "jflr": {
                    "vpgIdentifier": vpg_id,
                    "vmIdentifier": vm_id,
                    "checkpointIdentifier": checkpoint_id,
                    "initialDownloadPath": initial_download_path
                },
                "bflr": None # TBD
            }
            logging.info(f"FLR Payload: {json.dumps(flr_payload, indent=2)}")

            # Send the request
            url = f"https://{self.zvm_address}/v1/flrs"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.token}'
            }
            response = requests.post(url, json=flr_payload, headers=headers, verify=verifyCertificate)

            # Raise HTTPError for bad status codes
            response.raise_for_status()
            logging.info("FLR initiation successful.")
            return response.json()

        except requests.exceptions.RequestException as e:
            logging.error(f"HTTPError: {e.response.status_code} - {e.response.reason}")
            try:
                error_details = e.response.json()
                logging.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except ValueError:
                logging.error(f"Response content: {e.response.text}")
            raise

        except Exception as e:
            logging.error(f"Unexpected error during FLR initiation: {e}")
            raise

###########################          VIRTUAL MACHINES         #######################
#     Get information about virtual machines protected by the current site
    def list_vms(self, vpg_name=None, vm_name=None, status=None, sub_status=None, protected_site_type=None,
                recovery_site_type=None, protected_site_identifier=None, recovery_site_identifier=None,
                organization_name=None, priority=None, vm_identifier=None, include_backuped_vms=None,
                include_mounted_vms=True):
        """
        Get information about protected virtual machines with optional filters.
        
        :param vpg_name: The name of the VPG.
        :param vm_name: The name of the virtual machine.
        :param status: The status of the VPG.
        :param sub_status: The substatus of the VPG.
        :param protected_site_type: The protected site type.
        :param recovery_site_type: The recovery site environment.
        :param protected_site_identifier: The identifier of the protected site.
        :param recovery_site_identifier: The identifier of the recovery site.
        :param organization_name: The ZORG for this VPG.
        :param priority: The priority specified for the VPG.
        :param vm_identifier: The identifier of the virtual machine.
        :param include_backuped_vms: Whether to include backup virtual machines.
        :param include_mounted_vms: Whether to include mounted VMs or only unmounted VMs.
        :return: A list of virtual machines based on the provided filters.
        """
        logging.debug(f"list_vms(vpg_name={vpg_name}, vm_name={vm_name}, status={status}, sub_status={sub_status}, "
                    f"protected_site_type={protected_site_type}, recovery_site_type={recovery_site_type}, "
                    f"protected_site_identifier={protected_site_identifier}, recovery_site_identifier={recovery_site_identifier}, "
                    f"organization_name={organization_name}, priority={priority}, vm_identifier={vm_identifier}, "
                    f"include_backuped_vms={include_backuped_vms}, include_mounted_vms={include_mounted_vms})")

        uri = f"https://{self.zvm_address}/v1/vms"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        # Building query parameters
        params = {}
        if vpg_name:
            params['vpgName'] = vpg_name
        if vm_name:
            params['vmName'] = vm_name
        if status:
            params['status'] = status
        if sub_status:
            params['subStatus'] = sub_status
        if protected_site_type:
            params['protectedSiteType'] = protected_site_type
        if recovery_site_type:
            params['recoverySiteType'] = recovery_site_type
        if protected_site_identifier:
            params['protectedSiteIdentifier'] = protected_site_identifier
        if recovery_site_identifier:
            params['recoverySiteIdentifier'] = recovery_site_identifier
        if organization_name:
            params['organizationName'] = organization_name
        if priority:
            params['priority'] = priority
        if vm_identifier:
            params['vmIdentifier'] = vm_identifier
        if include_backuped_vms is not None:  # Check for explicit True/False
            params['includeBackupedVms'] = str(include_backuped_vms).lower()
        if include_mounted_vms is not None:
            params['includeMountedVms'] = str(include_mounted_vms).lower()

        try:
            response = requests.get(uri, headers=headers, params=params, verify=verifyCertificate)
            response.raise_for_status()
            event_categories = response.json()

            if not event_categories:
                logging.warning("No vms found.")
                return []

            return event_categories

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching vms: {e}")
            return None    

###########################          VRAS (Virtual Replication Appliances)        #######################
#     Manage VRAs
    def list_vras(self, vra_identifier=None, site_identifier=None, state=None):
        """
        Fetches a list of Virtual Replication Appliances (VRAs) or details of a specific VRA.

        :param vra_identifier: The unique identifier of a specific VRA.
        :param site_identifier: Optional filter by the site identifier.
        :param state: Optional filter b
        :return: A list of VRAs or details of a specific VRA.
        """
        if vra_identifier:
            logging.debug(f'list_vras(zvm_address={self.zvm_address}, vra_identifier={vra_identifier})')
            vras_uri = f"https://{self.zvm_address}/v1/vras/{vra_identifier}"
        else:
            logging.debug(f'list_vras(zvm_address={self.zvm_address}, site_identifier={site_identifier}, state={state})')
            vras_uri = f"https://{self.zvm_address}/v1/vras"

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        # Building query parameters
        params = {}
        if site_identifier:
            params['siteIdentifier'] = site_identifier
        if state:
            params['state'] = state

        try:
            logging.info("Fetching VRAs...")
            response = requests.get(vras_uri, headers=headers, params=params, verify=verifyCertificate)
            response.raise_for_status()
            vras = response.json()

            if not vras:
                logging.warning("No VRAs found.")
                return []

            logging.info("Successfully retrieved VRAs.")
            return vras

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching VRAs: {e}")
            return None

    def install_vra(self, host_identifier, datastore_identifier, network_identifier, host_root_password,
                    memory_in_gb, group_name, vra_ip_config_type, vra_ip_address, vra_ip_address_range_end,
                    subnet_mask, default_gateway, use_public_key_instead_of_credentials=True,
                    populate_post_installation=True, num_of_cpus=0, vm_instance_type=None, sync=False):
        """
        Installs a VRA on a specified host.
        """
        logging.debug(f"install_vra(zvm_address={self.zvm_address}, host_identifier={host_identifier}, "
                    f"datastore_identifier={datastore_identifier}, network_identifier={network_identifier}, sync={sync})")

        url = f"https://{self.zvm_address}/v1/vras"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        payload = {
            "hostIdentifier": host_identifier,
            "datastoreIdentifier": datastore_identifier,
            "networkIdentifier": network_identifier,
            "hostRootPassword": host_root_password,
            "memoryInGb": memory_in_gb,
            "groupName": group_name,
            "vraNetworkDataApi": {
                "vraIPConfigurationTypeApi": vra_ip_config_type,
                "vraIPAddress": vra_ip_address,
                "vraIPAddressRangeEnd": vra_ip_address_range_end,
                "subnetMask": subnet_mask,
                "defaultGateway": default_gateway
            },
            "usePublicKeyInsteadOfCredentials": use_public_key_instead_of_credentials,
            "populatePostInstallation": populate_post_installation,
            "numOfCpus": num_of_cpus
        }

        logging.debug(f'payload={payload}')

        if vm_instance_type:
            payload["vmInstanceType"] = vm_instance_type

        try:
            logging.info(f"Sending request to install VRA on host {host_identifier}...")
            response = requests.post(url, headers=headers, json=payload, verify=verifyCertificate)
            response.raise_for_status()
            task_id = response.json()
            logging.info(f"VRA installation initiated for host {host_identifier}, task_id={task_id}")

            if sync:
                self.wait_for_task_completion(task_id, timeout=600, interval=10)
                logging.info("VRA installation completed.")
            return task_id

        except requests.exceptions.HTTPError as http_err:
            # Extract detailed error message from response
            if http_err.response is not None:
                try:
                    error_details = http_err.response.json()  # Parse JSON response for error details
                    logging.error(f"HTTPError: {error_details.get('Message', 'No detailed error message provided')}")
                except ValueError:
                    logging.error(f"HTTPError: {http_err.response.text}")  # Raw response text
            else:
                logging.error(f"HTTPError occurred: {http_err}")
            sys.exit(1)

        except requests.exceptions.RequestException as e:
            logging.error(f"Error installing VRA on host '{host_identifier}': {e}")
            sys.exit(1)

    def install_vra_on_cluster(self, cluster_identifier, datastore_identifier, network_identifier, 
                               memory_in_gb, num_of_cpus, group_name, vra_network_data, 
                               host_root_password=None, 
                               use_public_key_instead_of_credentials=False, 
                               auto_populate_post_installation=False, 
                               sync=False):
        """
        Installs VRAs on a specified cluster.

        :param cluster_identifier: Identifier of the cluster where VRAs will be installed.
        :param datastore_identifier: Identifier of the datastore to use for the VRA.
        :param network_identifier: Identifier of the network for the VRA.
        :param memory_in_gb: Amount of memory (in GB) allocated to the VRA.
        :param num_of_cpus: Number of CPUs allocated to the VRA.
        :param group_name: Group name for the VRA installation.
        :param vra_network_data: Dictionary with VRA network configuration.
        :param host_root_password: Root password for the ESXi host(s) (optional if using public key).
        :param use_public_key_instead_of_credentials: Flag to use public key authentication instead of credentials.
        :param auto_populate_post_installation: Auto-populate data after installation.
        :param sync: If True, waits for the task to complete.
        :return: Task identifier or task result (if sync=True).
        """
        logging.debug(f"install_vra_on_cluster(zvm_address={self.zvm_address}, cluster_identifier={cluster_identifier})")
        
        uri = f"https://{self.zvm_address}/v1/vras/clusters"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        payload = {
            "clusterIdentifier": cluster_identifier,
            "datastoreIdentifier": datastore_identifier,
            "networkIdentifier": network_identifier,
            "memoryInGb": memory_in_gb,
            "numOfCpus": num_of_cpus,
            "groupName": group_name,
            "vraNetworkDataApi": vra_network_data,
            "usePublicKeyInsteadOfCredentials": use_public_key_instead_of_credentials,
            "autoPopulatePostInstalltion": auto_populate_post_installation,
            "hostRootPassword": host_root_password
        }

        logging.debug(f'payload={payload}')

        # Include hostRootPassword only if provided
        if host_root_password:
            payload["hostRootPassword"] = host_root_password

        try:
            logging.info(f"Installing VRAs on cluster {cluster_identifier}...")
            response = requests.post(uri, headers=headers, json=payload, verify=verifyCertificate)
            response.raise_for_status()
            task_id = response.json()
            logging.info(f"VRA installation task started, task_id={task_id}")

            if sync:
                # Wait for task completion
                self.wait_for_task_completion(task_id, timeout=600, interval=5)
                logging.info("VRA installation completed.")
                return self.wait_for_task_completion(task_id, timeout=600, interval=5)
            
            return task_id

        except requests.exceptions.RequestException as e:
            logging.error(f"Error installing VRAs on cluster {cluster_identifier}: {e}")
            sys.exit(1)
###########################          Licensing        #######################
#     Manage the current ZVM license
    def get_license(self):
        """
        Fetch license information from the Zerto server.

        Returns:
            dict: The license information from the Zerto server, or an empty dictionary if no content is returned.
        """
        logging.debug(f'get_license(zvm_address={self.zvm_address})')

        url = f"https://{self.zvm_address}/v1/license"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        try:
            logging.info("Fetching license information...")
            response = requests.get(url, headers=headers, verify=verifyCertificate)

            # Handle 204 No Content
            if response.status_code == 204:
                logging.info("No license information available.")
                return {}

            # Raise an error for other non-successful HTTP status codes
            response.raise_for_status()

            # Parse the response JSON
            license_info = response.json()
            logging.info("Successfully fetched license information.")
            return license_info

        except requests.exceptions.RequestException as e:
            if e.response is not None:
                logging.error(f"HTTPError: {e.response.status_code} - {e.response.reason}")
                try:
                    error_details = e.response.json()
                    logging.error(f"Error details: {json.dumps(error_details, indent=2)}")
                except ValueError:
                    logging.error(f"Response content: {e.response.text}")
            else:
                logging.error("HTTPError occurred with no response attached.")
            raise

        except Exception as e:
            logging.error(f"Unexpected error while fetching license information: {e}")
            raise

    def put_license(self, license_key):
        """
        Add a new license or update an existing one on the Zerto server.

        Args:
            license_key (str): The license key to add or update.

        Returns:
            dict: The response from the Zerto server, or an empty dictionary if no content is returned.
        """
        logging.debug(f'put_license(zvm_address={self.zvm_address}, license_key={license_key})')

        url = f"https://{self.zvm_address}/v1/license"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }
        payload = {
            "licenseKey": license_key
        }

        try:
            logging.info("Adding or updating license...")
            response = requests.put(url, json=payload, headers=headers, verify=verifyCertificate)

            # Handle empty response with 200 status code
            if response.status_code == 200 and not response.content:
                logging.info("License successfully added or updated with no content returned.")
                return {}

            # Raise an error for other non-successful HTTP status codes
            response.raise_for_status()

            # Parse the response JSON
            response_data = response.json()
            logging.info("Successfully added or updated license.")
            return response_data

        except requests.exceptions.RequestException as e:
            if e.response is not None:
                logging.error(f"HTTPError: {e.response.status_code} - {e.response.reason}")
                try:
                    error_details = e.response.json()
                    logging.error(f"Error details: {json.dumps(error_details, indent=2)}")
                except ValueError:
                    logging.error(f"Response content: {e.response.text}")
            else:
                logging.error("HTTPError occurred with no response attached.")
            raise

        except Exception as e:
            logging.error(f"Unexpected error while adding or updating license: {e}")
            raise

    def delete_license(self):
        """
        Delete the current license from the Zerto server.

        Returns:
            dict: The response from the Zerto server.
        """
        logging.debug(f'delete_license(zvm_address={self.zvm_address})')

        url = f"https://{self.zvm_address}/v1/license"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        try:
            logging.info("Deleting license...")
            response = requests.delete(url, headers=headers, verify=verifyCertificate)

            # Raise an error for non-successful HTTP status codes
            response.raise_for_status()

            # Parse the response JSON if available
            if response.content:
                response_data = response.json()
                logging.info("License successfully deleted.")
                return response_data
            else:
                logging.info("License successfully deleted with no content returned.")
                return {}

        except requests.exceptions.RequestException as e:
            logging.error(f"HTTPError: {e.response.status_code} - {e.response.reason}")
            try:
                error_details = e.response.json()
                logging.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except ValueError:
                logging.error(f"Response content: {e.response.text}")
            raise

        except Exception as e:
            logging.error(f"Unexpected error while deleting license: {e}")
            raise
###########################          Recovery & Resources Reports        #######################
#     Get information about recovery operations and resources used by the virtual machines
    def get_recovery_reports(self, recovery_operation_identifier=None, page_number=1, page_size=1000, 
                         vpg_name=None, recovery_type=None, state=None, start_time=None, end_time=None):
        """
        Generate a recovery report and view information about recovery operations.

        Args:
            recovery_operation_identifier (str): The identifier of a specific recovery operation. If provided, no other parameters are used.
            start_time (str): The filtering interval start date-time.
            end_time (str): The filtering interval end date-time.
            page_number (int): The page number to retrieve. Default is 1.
            page_size (int): The number of reports to display in a single page. Max 1000. Default is 1000.
            vpg_name (str): The name of the VPG(s) to filter by. Separate multiple VPGs with commas.
            recovery_type (str): The type of recovery operation. Possible values: Failover, FailoverTest, Move.
            state (str): The recovery operation state. Possible values: Success, Fail.

        Returns:
            dict: The response from the ZVM API containing recovery report details.
        """
        # Determine the URL based on whether recoveryOperationIdentifier is provided
        if recovery_operation_identifier:
            base_url = f"https://{self.zvm_address}/v1/reports/recovery/{recovery_operation_identifier}"
            params = None  # No query parameters for this endpoint
        else:
            base_url = f"https://{self.zvm_address}/v1/reports/recovery"
            # Parameters for the request
            params = {
                "startTime": start_time,
                "endTime": end_time,
                "pageNumber": page_number,
                "pageSize": page_size,
            }

            # Optional parameters
            if vpg_name:
                params["vpgName"] = vpg_name
            if recovery_type:
                params["recoveryType"] = recovery_type
            if state:
                params["state"] = state

        # Headers for the request
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        }

        try:
            if recovery_operation_identifier:
                logging.info(f"Fetching recovery report for operation identifier {recovery_operation_identifier}...")
            else:
                logging.info(f"Fetching recovery reports from {start_time} to {end_time}...")

            response = requests.get(base_url, headers=headers, params=params, verify=False)

            if response.status_code == 200:
                logging.info("Successfully retrieved recovery reports.")
                return response.json()
            else:
                logging.error(f"Failed to fetch recovery reports. Status Code: {response.status_code}, Response: {response.text}")
                response.raise_for_status()

        except requests.exceptions.RequestException as e:
            logging.error(f"Error occurred while fetching recovery reports: {e}")
            raise

    def list_resource_reports(self, start_time=None, end_time=None, page_number=None, page_size=None, zorg_name=None, vpg_name=None, vm_name=None, protected_site_name=None, protected_cluster_name=None, protected_host_name=None, protected_org_vdc=None, protected_vcd_org=None, recovery_site_name=None, recovery_cluster_name=None, recovery_host_name=None, recovery_org_vdc=None, recovery_vcd_org=None):
        """
        Fetch resource reports with optional filters.

        :param start_time: The filtering interval start date-time.
        :param end_time: The filtering interval end date-time.
        :param page_number: The page number to retrieve.
        :param page_size: The number of reports per page (max 1000).
        :param zorg_name: The name of the ZORG in the Zerto Cloud Manager.
        :param vpg_name: The name of the VPG.
        :param vm_name: The name of the virtual machine.
        :param protected_site_name: The name of the protected site.
        :param protected_cluster_name: The name of the protected cluster.
        :param protected_host_name: The name of the protected host.
        :param protected_org_vdc: The name of the protected VDC organization.
        :param protected_vcd_org: The name of the protected VCD organization.
        :param recovery_site_name: The name of the recovery site.
        :param recovery_cluster_name: The name of the recovery cluster.
        :param recovery_host_name: The name of the recovery host.
        :param recovery_org_vdc: The name of the recovery VDC organization.
        :param recovery_vcd_org: The name of the recovery VCD organization.
        :return: A list of resource reports based on the provided filters.
        """
        logging.debug(f"list_resource_reports(start_time={start_time}, end_time={end_time}, page_number={page_number}, "
                    f"page_size={page_size}, zorg_name={zorg_name}, vpg_name={vpg_name}, vm_name={vm_name}, "
                    f"protected_site_name={protected_site_name}, protected_cluster_name={protected_cluster_name}, "
                    f"protected_host_name={protected_host_name}, protected_org_vdc={protected_org_vdc}, "
                    f"protected_vcd_org={protected_vcd_org}, recovery_site_name={recovery_site_name}, "
                    f"recovery_cluster_name={recovery_cluster_name}, recovery_host_name={recovery_host_name}, "
                    f"recovery_org_vdc={recovery_org_vdc}, recovery_vcd_org={recovery_vcd_org})")

        uri = f"https://{self.zvm_address}/v1/reports/resources"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        # Building query parameters
        params = {}
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        if page_number is not None:
            params['pageNumber'] = page_number
        if page_size is not None:
            params['pageSize'] = page_size
        if zorg_name:
            params['zorgName'] = zorg_name
        if vpg_name:
            params['vpgName'] = vpg_name
        if vm_name:
            params['vmName'] = vm_name
        if protected_site_name:
            params['protectedSiteName'] = protected_site_name
        if protected_cluster_name:
            params['protectedClusterName'] = protected_cluster_name
        if protected_host_name:
            params['protectedHostName'] = protected_host_name
        if protected_org_vdc:
            params['protectedOrgVdc'] = protected_org_vdc
        if protected_vcd_org:
            params['protectedVcdOrg'] = protected_vcd_org
        if recovery_site_name:
            params['recoverySiteName'] = recovery_site_name
        if recovery_cluster_name:
            params['recoveryClusterName'] = recovery_cluster_name
        if recovery_host_name:
            params['recoveryHostName'] = recovery_host_name
        if recovery_org_vdc:
            params['recoveryOrgVdc'] = recovery_org_vdc
        if recovery_vcd_org:
            params['recoveryVcdOrg'] = recovery_vcd_org

        try:
            response = requests.get(uri, headers=headers, params=params, verify=verifyCertificate)
            response.raise_for_status()
            reports = response.json()

            if not reports:
                logging.warning("No resource reports found.")
                return []

            return reports

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching resource reports: {e}")
            return None

###########################         Server Date-Time        #######################
#     Get ZVM local date-time
    def get_server_date_time(self, is_utc=False):
        """
        Retrieve the server's local date and time from the Zerto API.
        :param is_utc: If True, returns utc time, if False (default), returns local time

        Returns:
            str: The server's local date and time as a string.
        """
        logging.debug(f"get_server_date_time(is_utc={is_utc})")
                      
        # Base URL for the Zerto API
        url = f"https://{self.zvm_address}/v1/serverDateTime/serverDateTimeLocal"
        if is_utc:
            url = f"https://{self.zvm_address}/v1/serverDateTime/serverDateTimeUtc"

        # Headers for the request
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        }

        try:
            logging.info("Fetching server's local date and time...")
            response = requests.get(url, headers=headers, verify=False)

            if response.status_code == 200:
                logging.info("Successfully retrieved server date and time.")
                return response.json()
            else:
                logging.error(f"Failed to fetch server date and time. Status Code: {response.status_code}, Response: {response.text}")
                response.raise_for_status()

        except requests.exceptions.RequestException as e:
            logging.error(f"Error occurred while fetching server date and time: {e}")
            raise

    def get_date_time_argument(self, date_time_value):
        """
        Checks the system date time casting from the specified parameter.

        Args:
            date_time_value (str): The date-time value to check. It can be in one of the following formats:
                - Milliseconds since epoch (e.g., "12321")
                - UTC format (e.g., "2021-06-07T13:16:00.000Z")
                - Local time format (e.g., "6/7/2021")

        Returns:
            dict: The response from the ZVM API containing the processed date-time information.
        """
        # Base URL for the Zerto API
        url = f"https://{self.zvm_address}/v1/serverDateTime/dateTimeArgument"

        # Parameters for the request
        params = {
            "dateTimeArgument": date_time_value,
        }

        # Headers for the request
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        }

        try:
            logging.info(f"Checking date-time argument: {date_time_value}...")
            response = requests.get(url, headers=headers, params=params, verify=False)

            if response.status_code == 200:
                logging.info("Successfully validated date-time argument.")
                return response.json()
            else:
                logging.error(f"Failed to validate date-time argument. Status Code: {response.status_code}, Response: {response.text}")
                response.raise_for_status()

        except requests.exceptions.RequestException as e:
            logging.error(f"Error occurred while validating date-time argument: {e}")
            raise
