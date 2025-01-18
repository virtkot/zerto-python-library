import requests
import logging

class RecoveryScripts:
    def __init__(self, client):
        self.client = client

    def get_recovery_scripts(self):
        url = f"https://{self.client.zvm_address}/v1/recoveryscripts"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get recovery scripts: {e}")
            raise

    def get_recovery_script(self, script_identifier):
        url = f"https://{self.client.zvm_address}/v1/recoveryscripts/{script_identifier}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get recovery script: {e}")
            raise

    def get_recovery_script_types(self):
        url = f"https://{self.client.zvm_address}/v1/recoveryscripts/types"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get recovery script types: {e}")
            raise