import requests
import logging

class PeerSites:
    def __init__(self, client):
        self.client = client

    def get_peer_sites(self):
        logging.info("PeerSites.get_peer_sites: Fetching peer sites information...")
        url = f"https://{self.client.zvm_address}/v1/peersites"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            logging.info("PeerSites.get_peer_sites: Successfully retrieved peer sites information.")
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"PeerSites.get_peer_sites: Failed to get peer sites: {e}")
            raise

    def get_peer_site(self, site_identifier):
        logging.info(f"PeerSites.get_peer_site: Fetching peer site information for site identifier: {site_identifier}...")
        url = f"https://{self.client.zvm_address}/v1/peersites/{site_identifier}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            logging.info(f"PeerSites.get_peer_site: Successfully retrieved peer site information for site identifier: {site_identifier}.")
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"PeerSites.get_peer_site: Failed to get peer site for site identifier {site_identifier}: {e}")
            raise

    def get_peer_site_types(self):
        logging.info("PeerSites.get_peer_site_types: Fetching peer site information for site types...")
        url = f"https://{self.client.zvm_address}/v1/peersites/types"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }
        try:
            response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
            response.raise_for_status()
            logging.info("PeerSites.get_peer_site_types: Successfully retrieved peer site types information.")
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"PeerSites.get_peer_site_types: Failed to get peer site types: {e}")
            raise