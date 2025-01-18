import requests
import logging

class VPGSettings:
    def __init__(self, client):
        self.client = client

    def create_vpg_settings(self, payload):
        url = f"https://{self.client.zvm_address}/v1/vpgs/settings"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.post(url, json=payload, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to create VPG settings: {e}")
            raise

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