import requests
import logging
import ssl

# Configure logging with timestamp format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Import all necessary classes
from .tasks import Tasks
from .vpgs import VPGs
# from .vpg_settings import VPGSettings
from .vms import VMs
from .checkpoints import Checkpoints
from .failover import Failover
from .alerts import Alerts
from .peersites import PeerSites
from .events import Events
from .repositories import Repositories
from .sessions import Sessions
from .recoveryscripts import RecoveryScripts
from .organizations import Organizations
from .encryptiondetection import EncryptionDetection
from .localsite import LocalSite
from .datastores import Datastores
from .vras import VRA
from .recovery_reports import RecoveryReports
from .license import License
from .service_profiles import ServiceProfiles
from .server_date_time import ServerDateTime

# Disable SSL warnings for self-signed certificates
context = ssl._create_unverified_context()

class ZVMAClient:
    def __init__(self, zvm_address, client_id, client_secret, verify_certificate=True):
        self.zvm_address = zvm_address
        self.client_id = client_id
        self.client_secret = client_secret
        self.verify_certificate = verify_certificate
        self.token = None
        self.token_expiry = None
        self.__get_keycloak_token()
        self.tasks = Tasks(self)
        self.vpgs = VPGs(self)
        # self.vpg_settings = VPGSettings(self)
        self.vms = VMs(self)
        self.checkpoints = Checkpoints(self)
        self.failover = Failover(self)
        self.alerts = Alerts(self)
        self.peersites = PeerSites(self)
        self.events = Events(self)
        self.repositories = Repositories(self)
        self.sessions = Sessions(self)
        self.recoveryscripts = RecoveryScripts(self)
        self.organizations = Organizations(self)
        self.encryptiondetection = EncryptionDetection(self)
        self.localsite = LocalSite(self.zvm_address, self.token)
        self.datastores = Datastores(self)
        self.vras = VRA(self)
        self.recovery_reports = RecoveryReports(self)
        self.license = License(self)
        self.service_profiles = ServiceProfiles(self)
        self.server_date_time = ServerDateTime(self)
    def __get_keycloak_token(self):
        logging.debug(f'__get_keycloak_token(zvm_address={self.zvm_address})')
        keycloak_uri = f"https://{self.zvm_address}/auth/realms/zerto/protocol/openid-connect/token"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        body = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials',
            'expires_in': 3600  # Request token expiration in seconds (e.g., 1 hour)
        }

        try:
            logging.info("Connecting to Keycloak to get token...")
            response = requests.post(keycloak_uri, headers=headers, data=body, verify=self.verify_certificate)
            response.raise_for_status()
            token_data = response.json()
            self.token = token_data.get('access_token')
            self.token_expiry = token_data.get('expires_in')  # Store expiration time
            logging.info(f"Successfully retrieved token.")
            logging.info(f"Token expiration details:")
            logging.info(f"- Expires in: {self.token_expiry} seconds")
            logging.info(f"- Requested expiration: {body['expires_in']} seconds")
            if self.token_expiry != body['expires_in']:
                logging.warning(f"Server provided different expiration time than requested!")
            return self.token
        except requests.exceptions.RequestException as e:
            logging.error(f"Error retrieving token: {e}")
            raise