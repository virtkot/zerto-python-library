import requests
import logging

class VMs:
    def __init__(self, client):
        self.client = client

    def list_vms(self, vpg_name=None, vm_name=None, status=None, sub_status=None, protected_site_type=None, recovery_site_type=None, protected_site_identifier=None, recovery_site_identifier=None, organization_name=None, priority=None, vm_identifier=None, include_backuped_vms=None, include_mounted_vms=True):
        # Implementation of list_vms method
        pass