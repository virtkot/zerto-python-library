import requests
import logging

class LocalSite:
    def __init__(self, zvm_address, token):
        self.zvm_address = zvm_address
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def get_local_site(self):
        logging.info("LocalSite.get_local_site: Fetching local site information...")
        url = f"https://{self.zvm_address}/v1/localsite"
        try:
            response = requests.get(url, headers=self.headers, verify=False)
            response.raise_for_status()
            logging.info("LocalSite.get_local_site: Successfully retrieved local site information.")
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"LocalSite.get_local_site: Error occurred while fetching local site information: {e}")
            raise

    def get_pairing_statuses(self):
        logging.info("LocalSite.get_pairing_statuses: Fetching pairing statuses...")
        url = f"https://{self.zvm_address}/v1/localsite/pairingstatuses"
        try:
            response = requests.get(url, headers=self.headers, verify=False)
            response.raise_for_status()
            logging.info("LocalSite.get_pairing_statuses: Successfully retrieved pairing statuses.")
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"LocalSite.get_pairing_statuses: Error occurred while fetching pairing statuses: {e}")
            raise

    def send_usage(self):
        logging.info("LocalSite.send_usage: Sending local site billing usage...")
        url = f"https://{self.zvm_address}/v1/localsite/billing/sendUsage"
        try:
            response = requests.post(url, headers=self.headers, verify=False)
            response.raise_for_status()
            if response.content.strip():
                logging.info("LocalSite.send_usage: Successfully sent billing usage data.")
                return response.json()
            else:
                logging.info("LocalSite.send_usage: Successfully sent billing usage data. No content returned.")
                return None
        except requests.exceptions.RequestException as e:
            logging.error(f"LocalSite.send_usage: Error occurred while sending billing usage: {e}")
            raise

    def get_login_banner(self):
        logging.info("LocalSite.get_login_banner: Fetching login banner settings...")
        url = f"https://{self.zvm_address}/v1/localsite/settings/loginBanner"
        try:
            response = requests.get(url, headers=self.headers, verify=False)
            response.raise_for_status()
            logging.info("LocalSite.get_login_banner: Successfully retrieved login banner settings.")
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"LocalSite.get_login_banner: Error occurred while fetching login banner settings: {e}")
            raise

    def set_login_banner(self, is_enabled, banner_text):
        logging.info("LocalSite.set_login_banner: Setting login banner settings...")
        url = f"https://{self.zvm_address}/v1/localsite/settings/loginBanner"
        payload = {
            "isLoginBannerEnabled": is_enabled,
            "loginBanner": banner_text
        }
        try:
            response = requests.put(url, headers=self.headers, json=payload, verify=False)
            response.raise_for_status()
            logging.info("LocalSite.set_login_banner: Successfully set login banner settings.")
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"LocalSite.set_login_banner: Error occurred while setting login banner settings: {e}")
            raise