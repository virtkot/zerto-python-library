import requests
import logging

class Sessions:
    def __init__(self, client):
        self.client = client

    def get_sessions(self):
        url = f"https://{self.client.zvm_address}/v1/sessions"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get sessions: {e}")
            raise

    def get_session(self, session_identifier):
        url = f"https://{self.client.zvm_address}/v1/sessions/{session_identifier}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get session: {e}")
            raise

    def get_session_types(self):
        url = f"https://{self.client.zvm_address}/v1/sessions/types"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get session types: {e}")
            raise