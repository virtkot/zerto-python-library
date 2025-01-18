import requests
import logging

class Checkpoints:
    def __init__(self, client):
        self.client = client

    def list_checkpoints(self, vpg_name, start_date=None, end_date=None, checkpoint_date_str=None, latest=None):
        # Implementation of list_checkpoints method
        pass