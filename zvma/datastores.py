import requests
import logging

class Datastores:
    def __init__(self, client):
        self.client = client

    def list_datastores(self, datastore_identifier=None):
        if datastore_identifier:
            logging.info(f"Datastores.list_datastores: Fetching datastore information for identifier: {datastore_identifier}...")
            url = f"https://{self.client.zvm_address}/v1/datastores/{datastore_identifier}"
        else:
            logging.info("Datastores.list_datastores: Fetching all datastores information...")
            url = f"https://{self.client.zvm_address}/v1/datastores"
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            if datastore_identifier:
                logging.info(f"Datastores.list_datastores: Successfully retrieved datastore information for identifier: {datastore_identifier}.")
            else:
                logging.info("Datastores.list_datastores: Successfully retrieved all datastores information.")
            return response.json()
        except requests.exceptions.RequestException as e:
            if datastore_identifier:
                logging.error(f"Datastores.list_datastores: Failed to get datastore information for identifier {datastore_identifier}: {e}")
            else:
                logging.error(f"Datastores.list_datastores: Failed to get all datastores information: {e}")
            raise