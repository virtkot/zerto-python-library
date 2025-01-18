import requests
import logging

class Events:
    def __init__(self, client):
        self.client = client

    def get_events(self):
        url = f"https://{self.client.zvm_address}/v1/events"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get events: {e}")
            raise

    def get_event(self, event_identifier):
        url = f"https://{self.client.zvm_address}/v1/events/{event_identifier}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get event: {e}")
            raise

    def get_event_types(self):
        url = f"https://{self.client.zvm_address}/v1/events/types"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get event types: {e}")
            raise