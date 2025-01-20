import requests
import logging
import time
import json
from .tasks import Tasks
from .common import ZertoVPGStatus
class VPGs:
    def __init__(self, client):
        self.client = client
        self.tasks = Tasks(client)

    def list_vpgs(self, vpg_name=None, vpg_identifier=None):
        logging.info(f'VPGs.list_vpgs(vpg_name={vpg_name}, vpg_identifier={vpg_identifier})')
        if vpg_identifier:
            url = f"https://{self.client.zvm_address}/v1/vpgs/{vpg_identifier}"
        else:
            url = f"https://{self.client.zvm_address}/v1/vpgs"
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            vpgs = response.json()
            if vpg_name:
                matching_vpg = next((vpg for vpg in vpgs if vpg.get("VpgName") == vpg_name), None)
                if not matching_vpg:
                    logging.warning(f"No VPG found with the name '{vpg_name}'")
                    return {}
                return matching_vpg
            if vpg_identifier:
                matching_vpg = next((vpg for vpg in vpgs if vpg.get("VpgIdentifier") == vpg_identifier), None)
                if not matching_vpg:
                    logging.warning(f"No VPG found with the ID '{vpg_identifier}'")
                    return {}
                return matching_vpg
            return vpgs
        except requests.exceptions.RequestException as e:
            if e.response is not None:
                logging.error(f"HTTPError: {e.response.status_code} - {e.response.reason}")
                try:
                    error_details = e.response.json()
                    logging.error(f"Error Message: {error_details.get('Message', 'No detailed error message available')}")
                except ValueError:
                    logging.error(f"Response content: {e.response.text}")
            else:
                logging.error("HTTPError occurred with no response attached.")
            raise

        except Exception as e:
            logging.error(f"Unexpected error while generating peer site pairing token: {e}")
            raise

    def commit_vpg(self, vpg_settings_id, vpg_name, sync=False, expected_status=ZertoVPGStatus.Initializing):
        logging.info(f'VPGs.commit_vpg(zvm_address={self.client.zvm_address}, vpg_settings_id={vpg_settings_id}, vpg_name={vpg_name}, sync={sync})')
        commit_uri = f"https://{self.client.zvm_address}/v1/vpgSettings/{vpg_settings_id}/commit"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }

        try:
            response = requests.post(commit_uri, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            task_id = response.json()
            logging.info(f"VPGSettings {vpg_settings_id} successfully committed, {vpg_name} is created, task_id={task_id}")

            if sync:
                # Wait for task completion
                self.tasks.wait_for_task_completion(task_id, timeout=30, interval=5)
                logging.debug('sleeping 5 seconds ...')
                self.wait_for_vpg_ready(vpg_name=vpg_name, timeout=30, interval=5, expected_status=expected_status)
                return task_id
            return task_id

        except requests.exceptions.RequestException as e:
            if e.response is not None:
                logging.error(f"HTTPError: {e.response.status_code} - {e.response.reason}")
                try:
                    error_details = e.response.json()
                    logging.error(f"Error Message: {error_details.get('Message', 'No detailed error message available')}")
                except ValueError:
                    logging.error(f"Response content: {e.response.text}")
            else:
                logging.error("HTTPError occurred with no response attached.")
            raise

        except Exception as e:
            logging.error(f"Unexpected error while generating peer site pairing token: {e}")
            raise

    def create_vpg(self, basic, journal, recovery, networks, sync=True):
        vpg_name = basic.get("Name")
        logging.info(f'VPGs.create_vpg(zvm_address={self.client.zvm_address}, vpg_name={vpg_name}, sync={sync})')
        vpg_settings_id = self.create_vpg_settings(basic, journal, recovery, networks, vpg_identifier=None)
        return self.commit_vpg(vpg_settings_id, vpg_name, sync, expected_status=ZertoVPGStatus.NotMeetingSLA)

    def wait_for_vpg_ready(self, vpg_name, timeout=180, interval=5, expected_status=ZertoVPGStatus.Initializing):
        logging.debug(f'VPGs.wait_for_vpg_ready(zvm_address={self.client.zvm_address}, vpg_name={vpg_name}, timeout={timeout}, interval={interval}, expected_status={ZertoVPGStatus.get_name_by_value(expected_status.value)})')
        start_time = time.time()

        while True:
            time.sleep(interval)
            vpg_info = self.list_vpgs(vpg_name=vpg_name)
            vpg_status = vpg_info.get("Status")
            status_name = ZertoVPGStatus.get_name_by_value(vpg_status)
            logging.debug(f"Checking VPG status for {vpg_name}: Current status = {status_name}")

            if vpg_status == expected_status.value:
                logging.info(f"VPG {vpg_name} is now in the expected state: {status_name}")
                return vpg_info

            # Check if the timeout has been reached
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                raise TimeoutError(f"VPG {vpg_name} did not reach the ready state within the allotted time. Current status: {status_name}")

    def add_vm_to_vpg(self, vpg_name, vm_list_payload):
        logging.info(f'VPGs.add_vm_to_vpg(zvm_address={self.client.zvm_address}, vpg_name={vpg_name})')
        vpg = self.list_vpgs(vpg_name=vpg_name)
        
        if not vpg:
            logging.error(f"VPG with name '{vpg_name}' not found.")
            return

        vpg_identifier = vpg['VpgIdentifier']
        logging.info(f"Found VPG '{vpg_name}' with Identifier: {vpg_identifier}")

        new_vpg_settings_id = self.create_vpg_settings(basic=None, journal=None, recovery=None, networks=None, vpg_identifier=vpg_identifier)

        logging.info(f"Adding VMs to VPGSettings ID: {new_vpg_settings_id}")
        #logging.debug(f"VM List Payload: {json.dumps(vm_list_payload, indent=4)}")
        vms_uri = f"https://{self.client.zvm_address}/v1/vpgSettings/{new_vpg_settings_id}/vms"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }

        try:
            response = requests.post(vms_uri, headers=headers, json=vm_list_payload, verify=self.client.verify_certificate)
            response.raise_for_status()
            logging.info(f"Successfully added VMs to VPG {new_vpg_settings_id}.")
            self.commit_vpg(new_vpg_settings_id, vpg_name, sync=True, expected_status=ZertoVPGStatus.Initializing)
            return 

        except requests.exceptions.RequestException as e:
            if e.response is not None:
                logging.error(f"HTTPError: {e.response.status_code} - {e.response.reason}")
                try:
                    error_details = e.response.json()
                    logging.error(f"Error Message: {error_details.get('Message', 'No detailed error message available')}")
                except ValueError:
                    logging.error(f"Response content: {e.response.text}")
            else:
                logging.error("HTTPError occurred with no response attached.")
            raise

        except Exception as e:
            logging.error(f"Unexpected error while generating peer site pairing token: {e}")
            raise

    def remove_vm_from_vpg(self, vpg_name, vm_identifier):
        logging.info(f'VPGs.remove_vm_from_vpg(zvm_address={self.client.zvm_address}, vpg_name={vpg_name}, vm_identifier={vm_identifier})')
        vpg = self.list_vpgs(vpg_name=vpg_name)

        if not vpg:
            logging.error(f"VPG with name '{vpg_name}' not found.")
            return

        vpg_id = vpg['VpgIdentifier']
        logging.info(f"Found VPG '{vpg_name}' with Identifier: {vpg_id}")

        new_vpg_settings_id = self.create_vpg_settings(basic=None, journal=None, recovery=None, networks=None, vpg_identifier=vpg_id)
        remove_vm_uri = f"https://{self.client.zvm_address}/v1/vpgSettings/{new_vpg_settings_id}/vms/{vm_identifier}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }

        try:
            response = requests.delete(remove_vm_uri, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            logging.info(f"VM {vm_identifier} successfully removed from VPG '{vpg_name}' (ID: {new_vpg_settings_id}).")
            self.commit_vpg(new_vpg_settings_id, vpg_name, sync=True, expected_status=ZertoVPGStatus.Initializing)

        except requests.exceptions.RequestException as e:
            if e.response is not None:
                logging.error(f"HTTPError: {e.response.status_code} - {e.response.reason}")
                try:
                    error_details = e.response.json()
                    logging.error(f"Error Message: {error_details.get('Message', 'No detailed error message available')}")
                except ValueError:
                    logging.error(f"Response content: {e.response.text}")
            else:
                logging.error("HTTPError occurred with no response attached.")
            raise

        except Exception as e:
            logging.error(f"Unexpected error while generating peer site pairing token: {e}")
            raise

    def failover_test(self, vpg_name, checkpoint_identifier=None, vm_name_list=None, sync=None):
        """
        Initiate a failover test for a given VPG by its name.

        :param vpg_name: The name of the VPG.
        :param checkpoint_identifier: checkpoint_identifier can be recived by list_checkpoint, if not provided uses the latest checkpoint.
        :param vm_name_list: List of 
        :param options: Optional parameters for the failover test.
        :return: Response from the Zerto API.
        """
        logging.info(f'VPGs.failover_test(zvm_address={self.client.zvm_address}, vpg_name={vpg_name}, checkpoint_identifier={checkpoint_identifier}, vm_name_list={vm_name_list}, sync={sync})')

        # Retrieve the VPG identifier using the VPG name
        vpg_info = self.list_vpgs(vpg_name=vpg_name)
        vpg_identifier = vpg_info['VpgIdentifier']
        logging.debug(f"Found VPG '{vpg_name}' with Identifier: {vpg_identifier}")

        url = f"https://{self.client.zvm_address}/v1/vpgs/{vpg_identifier}/FailoverTest"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
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
            response = requests.post(url, headers=headers, json=payload, verify=self.client.verify_certificate)
            response.raise_for_status()
            task_id = response.json()

            logging.info(f"Failover test initiated for VPG {vpg_name}, task_id = {task_id}")

            if sync:
                # Wait for task completion
                self.wait_for_task_completion(task_id, timeout=30, interval=5)
            return response.json()

        except requests.exceptions.RequestException as e:
            if e.response is not None:
                logging.error(f"HTTPError: {e.response.status_code} - {e.response.reason}")
                try:
                    error_details = e.response.json()
                    logging.error(f"Error Message: {error_details.get('Message', 'No detailed error message available')}")
                except ValueError:
                    logging.error(f"Response content: {e.response.text}")
            else:
                logging.error("HTTPError occurred with no response attached.")
            raise

        except Exception as e:
            logging.error(f"Unexpected error while generating peer site pairing token: {e}")
            raise

    def stop_failover_test(self, vpg_name, sync=None):
        """
        Stop a failover test for a given VPG by its name.

        :param vpg_name: The name of the VPG.
        :param sync: wait until task is completed.

        """
        logging.info(f'VPGs.stop_failover_test(zvm_address={self.client.zvm_address}, vpg_name={vpg_name}, sync={sync})')

        # Retrieve the VPG identifier using the VPG name
        vpg_info = self.list_vpgs(vpg_name=vpg_name)
        vpg_identifier = vpg_info['VpgIdentifier']
        logging.info(f"Found VPG '{vpg_name}' with Identifier: {vpg_identifier}")

        url = f"https://{self.client.zvm_address}/v1/vpgs/{vpg_identifier}/FailoverTestStop"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }

        try:
            logging.info(f"Stopping failover test for VPG '{vpg_name}'...")
            response = requests.post(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            task_id = response.json()

            logging.info(f"Failover test stopping for VPG {vpg_name}, task_id = {task_id}")

            if sync:
                # Wait for task completion
                self.wait_for_task_completion(task_id, timeout=30, interval=5)
            return response.json()

        except requests.exceptions.RequestException as e:
            if e.response is not None:
                logging.error(f"HTTPError: {e.response.status_code} - {e.response.reason}")
                try:
                    error_details = e.response.json()
                    logging.error(f"Error Message: {error_details.get('Message', 'No detailed error message available')}")
                except ValueError:
                    logging.error(f"Response content: {e.response.text}")
            else:
                logging.error("HTTPError occurred with no response attached.")
            raise

        except Exception as e:
            logging.error(f"Unexpected error while generating peer site pairing token: {e}")
            raise

    def rollback_failover(self, vpg_name, sync=True):
        """
        Rollback failover for a given VPG by its name.

        :param vpg_name: The name of the VPG.
        :param sync: wait until task is completed.

        """
        logging.info(f'VPGs.rollback_failover(zvm_address={self.client.zvm_address}, vpg_name={vpg_name}, sync={sync})')

        # Retrieve the VPG identifier using the VPG name
        vpg_info = self.list_vpgs(vpg_name=vpg_name)
        vpg_identifier = vpg_info['VpgIdentifier']
        logging.info(f"Found VPG '{vpg_name}' with Identifier: {vpg_identifier}")

        url = f"https://{self.client.zvm_address}/v1/vpgs/{vpg_identifier}/FailoverRollback"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }

        try:
            logging.info(f"Rollback failover for VPG '{vpg_name}'...")
            response = requests.post(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            task_id = response.json()

            logging.info(f"Rollback faolover for VPG {vpg_name}, task_id = {task_id}")

            if sync:
                # Wait for task completion
                self.wait_for_task_completion(task_id, timeout=30, interval=5)
            return response.json()

        except requests.exceptions.RequestException as e:
            if e.response is not None:
                logging.error(f"HTTPError: {e.response.status_code} - {e.response.reason}")
                try:
                    error_details = e.response.json()
                    logging.error(f"Error Message: {error_details.get('Message', 'No detailed error message available')}")
                except ValueError:
                    logging.error(f"Response content: {e.response.text}")
            else:
                logging.error("HTTPError occurred with no response attached.")
            raise

        except Exception as e:
            logging.error(f"Unexpected error while generating peer site pairing token: {e}")
            raise

    def delete_vpg(self, vpg_name, force=False, keep_recovery_volumes=True):
        """
        Deletes a VPG by its name.

        :param vpg_name: The name of the VPG to delete.
        :return: Success message if deleted, else an error message.
        """
        logging.info(f"VPGs.delete_vpg(zvm_address={self.client.zvm_address}, vpg_name={vpg_name}, force={force}, keep_recovery_volumes={keep_recovery_volumes})")

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
        delete_vpg_uri = f"https://{self.client.zvm_address}/v1/vpgs/{vpg_identifier}"

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }

        payload = {
            "keepRecoveryVolumes": force,
            "force": keep_recovery_volumes
        }

        try:
            # Step 3: Send DELETE request
            response = requests.delete(delete_vpg_uri, headers=headers, json=payload, verify=self.client.verify_certificate)

            response.raise_for_status()  # Ensure the request was successful
            logging.info(f"Successfully deleted VPG '{vpg_name}' (ID: {vpg_identifier}).")
            return f"VPG '{vpg_name}' deleted successfully."

        except requests.exceptions.RequestException as e:
            if e.response is not None:
                logging.error(f"HTTPError: {e.response.status_code} - {e.response.reason}")
                try:
                    error_details = e.response.json()
                    logging.error(f"Error Message: {error_details.get('Message', 'No detailed error message available')}")
                except ValueError:
                    logging.error(f"Response content: {e.response.text}")
            else:
                logging.error("HTTPError occurred with no response attached.")
            raise

        except Exception as e:
            logging.error(f"Unexpected error while generating peer site pairing token: {e}")
            raise

    # Added methods from VPGSettings
    def list_vpg_settings(self):
        url = f"https://{self.client.zvm_address}/v1/vpgs/settings"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to list VPG settings: {e}")
            raise

    def get_vpg_settings_by_id(self, vpg_settings_id):
        url = f"https://{self.client.zvm_address}/v1/vpgs/settings/{vpg_settings_id}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get VPG settings by ID: {e}")
            raise

    def update_vpg_settings(self, vpg_settings_id, payload):
        url = f"https://{self.client.zvm_address}/v1/vpgs/settings/{vpg_settings_id}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.put(url, json=payload, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to update VPG settings: {e}")
            raise

    def delete_vpg_settings(self, vpg_settings_id):
        url = f"https://{self.client.zvm_address}/v1/vpgs/settings/{vpg_settings_id}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.delete(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to delete VPG settings: {e}")
            raise

    def create_vpg_settings(self, basic, journal, recovery, networks, vpg_identifier=None):
        logging.info(f'VPGs.create_vpg_settings(zvm_address={self.client.zvm_address}, vpg_identifier={vpg_identifier})')
        vpg_settings_uri = f"https://{self.client.zvm_address}/v1/vpgSettings"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }

        payload = {}
        if vpg_identifier:
            payload["vpgIdentifier"] = vpg_identifier
        if basic: 
            payload["Basic"] = basic
        if journal:
            payload["Journal"] = journal
        if recovery:
            payload["Recovery"] = recovery
        if networks:
            payload["Networks"] = networks

        try:
            response = requests.post(vpg_settings_uri, headers=headers, json=payload, verify=self.client.verify_certificate)
            response.raise_for_status()
            vpg_settings_id = response.json()
            logging.info(f"VPG Settings ID: {vpg_settings_id} created")
            return vpg_settings_id
        except requests.exceptions.RequestException as e:
            if e.response is not None:
                logging.error(f"HTTPError: {e.response.status_code} - {e.response.reason}")
                try:
                    error_details = e.response.json()
                    logging.error(f"Error Message: {error_details.get('Message', 'No detailed error message available')}")
                except ValueError:
                    logging.error(f"Response content: {e.response.text}")
            else:
                logging.error("HTTPError occurred with no response attached.")
            raise
        except Exception as e:
            logging.error(f"Unexpected error while generating peer site pairing token: {e}")
            raise
