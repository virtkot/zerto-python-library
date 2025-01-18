import requests
import logging

class Organizations:
    def __init__(self, client):
        self.client = client

    def get_organizations(self):
        url = f"https://{self.client.zvm_address}/v1/organizations"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get organizations: {e}")
            raise

    def get_organization(self, organization_identifier):
        url = f"https://{self.client.zvm_address}/v1/organizations/{organization_identifier}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get organization: {e}")
            raise

    def get_organization_types(self):
        url = f"https://{self.client.zvm_address}/v1/organizations/types"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get organization types: {e}")
            raise