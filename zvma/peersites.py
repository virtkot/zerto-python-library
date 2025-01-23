# Legal Disclaimer
# This script is an example script and is not supported under any Zerto support program or service. 
# The author and Zerto further disclaim all implied warranties including, without limitation, 
# any implied warranties of merchantability or of fitness for a particular purpose.
# In no event shall Zerto, its authors or anyone else involved in the creation, 
# production or delivery of the scripts be liable for any damages whatsoever (including, 
# without limitation, damages for loss of business profits, business interruption, loss of business 
# information, or other pecuniary loss) arising out of the use of or the inability to use the sample 
# scripts or documentation, even if the author or Zerto has been advised of the possibility of such damages. 
# The entire risk arising out of the use or performance of the sample scripts and documentation remains with you.

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