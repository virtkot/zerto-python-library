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
import logging

class VRA:
    def __init__(self, client):
        self.client = client

    def list_vras(self):
        logging.info("VRA.list_vras: Fetching all VRAs information...")
        url = f"https://{self.client.zvm_address}/v1/vras"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            logging.info("VRA.list_vras: Successfully retrieved all VRAs information.")
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"VRA.list_vras: Failed to get all VRAs information: {e}")
            raise

    def create_vra(self, payload):
        logging.info("VRA.create_vra: Creating a new VRA...")
        url = f"https://{self.client.zvm_address}/v1/vras"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.post(url, headers=headers, json=payload, verify=self.client.verify_certificate)
            response.raise_for_status()
            logging.info("VRA.create_vra: Successfully created a new VRA.")
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"VRA.create_vra: Failed to create a new VRA: {e}")
            raise

    def get_vra(self, vra_identifier):
        logging.info(f"VRA.get_vra: Fetching VRA information for identifier: {vra_identifier}...")
        url = f"https://{self.client.zvm_address}/v1/vras/{vra_identifier}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            logging.info(f"VRA.get_vra: Successfully retrieved VRA information for identifier: {vra_identifier}.")
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"VRA.get_vra: Failed to get VRA information for identifier {vra_identifier}: {e}")
            raise

    def delete_vra(self, vra_identifier):
        logging.info(f"VRA.delete_vra: Deleting VRA for identifier: {vra_identifier}...")
        url = f"https://{self.client.zvm_address}/v1/vras/{vra_identifier}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.delete(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            logging.info(f"VRA.delete_vra: Successfully deleted VRA for identifier: {vra_identifier}.")
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"VRA.delete_vra: Failed to delete VRA for identifier {vra_identifier}: {e}")
            raise

    def update_vra(self, vra_identifier, payload):
        logging.info(f"VRA.update_vra: Updating VRA for identifier: {vra_identifier}...")
        url = f"https://{self.client.zvm_address}/v1/vras/{vra_identifier}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.put(url, headers=headers, json=payload, verify=self.client.verify_certificate)
            response.raise_for_status()
            logging.info(f"VRA.update_vra: Successfully updated VRA for identifier: {vra_identifier}.")
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"VRA.update_vra: Failed to update VRA for identifier {vra_identifier}: {e}")
            raise

    def create_vra_cluster(self, payload):
        logging.info("VRA.create_vra_cluster: Creating a new VRA cluster...")
        url = f"https://{self.client.zvm_address}/v1/vras/clusters"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.post(url, headers=headers, json=payload, verify=self.client.verify_certificate)
            response.raise_for_status()
            logging.info("VRA.create_vra_cluster: Successfully created a new VRA cluster.")
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"VRA.create_vra_cluster: Failed to create a new VRA cluster: {e}")
            raise

    def delete_vra_cluster(self, cluster_identifier):
        logging.info(f"VRA.delete_vra_cluster: Deleting VRA cluster for identifier: {cluster_identifier}...")
        url = f"https://{self.client.zvm_address}/v1/vras/clusters/{cluster_identifier}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.delete(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            logging.info(f"VRA.delete_vra_cluster: Successfully deleted VRA cluster for identifier: {cluster_identifier}.")
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"VRA.delete_vra_cluster: Failed to delete VRA cluster for identifier {cluster_identifier}: {e}")
            raise

    def update_vra_cluster(self, cluster_identifier, payload):
        logging.info(f"VRA.update_vra_cluster: Updating VRA cluster for identifier: {cluster_identifier}...")
        url = f"https://{self.client.zvm_address}/v1/vras/clusters/{cluster_identifier}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.put(url, headers=headers, json=payload, verify=self.client.verify_certificate)
            response.raise_for_status()
            logging.info(f"VRA.update_vra_cluster: Successfully updated VRA cluster for identifier: {cluster_identifier}.")
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"VRA.update_vra_cluster: Failed to update VRA cluster for identifier {cluster_identifier}: {e}")
            raise

    def cleanup_vras(self):
        logging.info("VRA.cleanup_vras: Cleaning up VRAs...")
        url = f"https://{self.client.zvm_address}/v1/vras/cleanup"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.delete(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            logging.info("VRA.cleanup_vras: Successfully cleaned up VRAs.")
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"VRA.cleanup_vras: Failed to clean up VRAs: {e}")
            raise

    def upgrade_vra(self, vra_identifier):
        logging.info(f"VRA.upgrade_vra: Upgrading VRA for identifier: {vra_identifier}...")
        url = f"https://{self.client.zvm_address}/v1/vras/{vra_identifier}/upgrade"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.post(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            logging.info(f"VRA.upgrade_vra: Successfully upgraded VRA for identifier: {vra_identifier}.")
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"VRA.upgrade_vra: Failed to upgrade VRA for identifier {vra_identifier}: {e}")
            raise

    def get_vra_cluster_settings(self, cluster_identifier):
        logging.info(f"VRA.get_vra_cluster_settings: Fetching VRA cluster settings for identifier: {cluster_identifier}...")
        url = f"https://{self.client.zvm_address}/v1/vras/clusters/{cluster_identifier}/settings"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            logging.info(f"VRA.get_vra_cluster_settings: Successfully retrieved VRA cluster settings for identifier: {cluster_identifier}.")
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"VRA.get_vra_cluster_settings: Failed to get VRA cluster settings for identifier {cluster_identifier}: {e}")
            raise

    def create_vra_cluster_settings(self, cluster_identifier, payload):
        logging.info(f"VRA.create_vra_cluster_settings: Creating VRA cluster settings for identifier: {cluster_identifier}...")
        url = f"https://{self.client.zvm_address}/v1/vras/clusters/{cluster_identifier}/settings"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.post(url, headers=headers, json=payload, verify=self.client.verify_certificate)
            response.raise_for_status()
            logging.info(f"VRA.create_vra_cluster_settings: Successfully created VRA cluster settings for identifier: {cluster_identifier}.")
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"VRA.create_vra_cluster_settings: Failed to create VRA cluster settings for identifier {cluster_identifier}: {e}")
            raise

    def list_vra_statuses(self):
        logging.info("VRA.list_vra_statuses: Fetching VRA statuses...")
        url = f"https://{self.client.zvm_address}/v1/vras/statuses"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            logging.info("VRA.list_vra_statuses: Successfully retrieved VRA statuses.")
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"VRA.list_vra_statuses: Failed to get VRA statuses: {e}")
            raise

    def list_ip_configuration_types(self):
        logging.info("VRA.list_ip_configuration_types: Fetching IP configuration types...")
        url = f"https://{self.client.zvm_address}/v1/vras/ipconfigurationtypes"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            logging.info("VRA.list_ip_configuration_types: Successfully retrieved IP configuration types.")
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"VRA.list_ip_configuration_types: Failed to get IP configuration types: {e}")
            raise

    def list_potential_recovery_vras(self, vra_identifier):
        logging.info(f"VRA.list_potential_recovery_vras: Fetching potential recovery VRAs for identifier: {vra_identifier}...")
        url = f"https://{self.client.zvm_address}/v1/vras/{vra_identifier}/changerecoveryvra/potentials"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            logging.info(f"VRA.list_potential_recovery_vras: Successfully retrieved potential recovery VRAs for identifier: {vra_identifier}.")
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"VRA.list_potential_recovery_vras: Failed to get potential recovery VRAs for identifier {vra_identifier}: {e}")
            raise

    def execute_recovery_vra_change(self, vra_identifier, payload):
        logging.info(f"VRA.execute_recovery_vra_change: Executing recovery VRA change for identifier: {vra_identifier}...")
        url = f"https://{self.client.zvm_address}/v1/vras/{vra_identifier}/changerecoveryvra/execute"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.post(url, headers=headers, json=payload, verify=self.client.verify_certificate)
            response.raise_for_status()
            logging.info(f"VRA.execute_recovery_vra_change: Successfully executed recovery VRA change for identifier: {vra_identifier}.")
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"VRA.execute_recovery_vra_change: Failed to execute recovery VRA change for identifier {vra_identifier}: {e}")
            raise

    def validate_recovery_vra_change(self, vra_identifier, payload):
        logging.info(f"VRA.validate_recovery_vra_change: Validating recovery VRA change for identifier: {vra_identifier}...")
        url = f"https://{self.client.zvm_address}/v1/vras/{vra_identifier}/changerecoveryvra/validate"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.post(url, headers=headers, json=payload, verify=self.client.verify_certificate)
            response.raise_for_status()
            logging.info(f"VRA.validate_recovery_vra_change: Successfully validated recovery VRA change for identifier: {vra_identifier}.")
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"VRA.validate_recovery_vra_change: Failed to validate recovery VRA change for identifier {vra_identifier}: {e}")
            raise

    def recommend_recovery_vra_change(self, vra_identifier, payload):
        logging.info(f"VRA.recommend_recovery_vra_change: Recommending recovery VRA change for identifier: {vra_identifier}...")
        url = f"https://{self.client.zvm_address}/v1/vras/{vra_identifier}/changerecoveryvra/recommendation"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.post(url, headers=headers, json=payload, verify=self.client.verify_certificate)
            response.raise_for_status()
            logging.info(f"VRA.recommend_recovery_vra_change: Successfully recommended recovery VRA change for identifier: {vra_identifier}.")
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"VRA.recommend_recovery_vra_change: Failed to recommend recovery VRA change for identifier {vra_identifier}: {e}")
            raise