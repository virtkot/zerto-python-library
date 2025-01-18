import requests
import logging
import time
import json
from .tasks import Tasks

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

    def commit_vpg(self, vpg_settings_id, vpg_name, sync=False, expected_status=0):
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

    def create_vpg_settings(self, basic, journal, recovery, networks, vpg_identifier=None):
        logging.info(f'VPGs.create_vpg_settings(zvm_address={self.client.zvm_address}, vpg_identifier={vpg_identifier})')
        vpg_settings_uri = f"https://{self.client.zvm_address}/v1/vpgSettings"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }

        # Construct payload
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

        logging.debug(f"VPGs.create_vpg_settings Creating VPG settings with payload: {json.dumps(payload, indent=4)}")

        try:
            response = requests.post(vpg_settings_uri, headers=headers, json=payload, verify=self.client.verify_certificate)
            response.raise_for_status()
            vpg_settings_id = response.json()
            logging.info(f"VPGSettings ID: {vpg_settings_id} created")
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

    def create_vpg(self, basic, journal, recovery, networks, sync=True):
        vpg_name = basic.get("Name")
        logging.info(f'VPGs.create_vpg(zvm_address={self.client.zvm_address}, vpg_name={vpg_name}, sync={sync})')
        vpg_settings_id = self.create_vpg_settings(basic, journal, recovery, networks, vpg_identifier=None)
        return self.commit_vpg(vpg_settings_id, vpg_name, sync, expected_status=2)

    def wait_for_vpg_ready(self, vpg_name, timeout=180, interval=5, expected_status=0):
        logging.debug(f'VPGs.wait_for_vpg_ready(zvm_address={self.client.zvm_address}, vpg_name={vpg_name}, timeout={timeout}, interval={interval})')
        start_time = time.time()

        while True:
            time.sleep(interval)
            vpg_info = self.list_vpgs(vpg_name=vpg_name)
            vpg_status = vpg_info.get("Status")
            logging.debug(f"Checking VPG status for {vpg_name}: Current status = {vpg_status}")

            if vpg_status == expected_status: 
                logging.info(f"VPG {vpg_name} is now in the expected state.")
                return vpg_info

            # Check if the timeout has been reached
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                raise TimeoutError(f"VPG {vpg_name} did not reach the ready state within the allotted time.")

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
        logging.debug(f"VM List Payload: {json.dumps(vm_list_payload, indent=4)}")
        vms_uri = f"https://{self.client.zvm_address}/v1/vpgSettings/{new_vpg_settings_id}/vms"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }

        try:
            response = requests.post(vms_uri, headers=headers, json=vm_list_payload, verify=self.client.verify_certificate)
            response.raise_for_status()
            logging.info(f"Successfully added VMs to VPG {new_vpg_settings_id}.")
            self.commit_vpg(new_vpg_settings_id, vpg_name, sync=True, expected_status=0)
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

        vpg_settings_payload = {
            "vpgIdentifier": vpg_id,
            "Basic": {
                "Name": vpg_name
            }
        }
        new_vpg_settings_id = self.create_vpg_settings(vpg_settings_payload)
        remove_vm_uri = f"https://{self.client.zvm_address}/v1/vpgSettings/{new_vpg_settings_id}/vms/{vm_identifier}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }

        try:
            response = requests.delete(remove_vm_uri, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            logging.info(f"VM {vm_identifier} successfully removed from VPG '{vpg_name}' (ID: {new_vpg_settings_id}).")
            self.commit_vpg(new_vpg_settings_id, vpg_name, sync=True, expected_status=0)

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
