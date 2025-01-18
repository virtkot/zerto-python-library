import requests
import logging

class Repositories:
    def __init__(self, client):
        self.client = client

    def get_repositories(self):
        url = f"https://{self.client.zvm_address}/v1/repositories"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get repositories: {e}")
            raise

    def get_repository(self, repository_identifier):
        url = f"https://{self.client.zvm_address}/v1/repositories/{repository_identifier}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get repository: {e}")
            raise

    def get_repository_types(self):
        url = f"https://{self.client.zvm_address}/v1/repositories/types"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get repository types: {e}")
            raise