import requests
import logging

class EncryptionDetection:
    def __init__(self, client):
        self.client = client

    def get_encryption_detections(self):
        url = f"https://{self.client.zvm_address}/v1/encryptiondetection"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get encryption detections: {e}")
            raise

    def get_encryption_detection(self, detection_identifier):
        url = f"https://{self.client.zvm_address}/v1/encryptiondetection/{detection_identifier}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get encryption detection: {e}")
            raise

    def get_encryption_detection_types(self):
        url = f"https://{self.client.zvm_address}/v1/encryptiondetection/types"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get encryption detection types: {e}")
            raise