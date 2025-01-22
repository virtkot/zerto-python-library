import requests
import logging

class ServiceProfiles:
    def __init__(self, client):
        self.client = client

    def get_service_profiles(self, site_identifier=None):
        """
        Get the list of all service profiles for the site.

        Args:
            site_identifier (str, optional): The identifier of the site for which service profiles 
                                           should be returned.

        Returns:
            list: List of service profiles with their details including:
                - serviceProfileName: Name of the service profile
                - rpo: Recovery Point Objective
                - history: Journal history length
                - maxJournalSizeInPercent: Maximum journal size as percentage
                - testInterval: Test interval period
                - description: Service profile description
        """
        logging.info(f"ServiceProfiles.get_service_profiles: Fetching service profiles...")
        
        url = f"https://{self.client.zvm_address}/v1/serviceprofiles"
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }

        params = {}
        if site_identifier:
            params['siteIdentifier'] = site_identifier
            logging.info(f"Filtering service profiles for site: {site_identifier}")

        try:
            response = requests.get(url, headers=headers, params=params, verify=self.client.verify_certificate)
            response.raise_for_status()
            profiles = response.json()
            logging.info(f"Successfully retrieved {len(profiles)} service profiles")
            return profiles

        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get service profiles: {e}")
            if hasattr(e.response, 'text'):
                logging.error(f"Error response: {e.response.text}")
            raise 