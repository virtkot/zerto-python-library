import requests
import logging

class Alerts:
    def __init__(self, client):
        self.client = client

    def get_alerts(self):
        url = f"https://{self.client.zvm_address}/v1/alerts"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get alerts: {e}")
            raise

    def get_alert(self, alert_identifier):
        url = f"https://{self.client.zvm_address}/v1/alerts/{alert_identifier}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get alert: {e}")
            raise

    def get_alert_types(self):
        url = f"https://{self.client.zvm_address}/v1/alerts/types"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get alert types: {e}")
            raise