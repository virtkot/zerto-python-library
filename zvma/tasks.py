import requests
import logging
import time
from enum import Enum

class ZertoTaskStates(Enum):
    FirstUnusedValue = 0
    InProgress = 1
    WaitingForUserInput = 2
    Paused = 3
    Failed = 4
    Stopped = 5
    Completed = 6
    Cancelling = 7
    @classmethod
    def get_name_by_value(cls, value):
        """
        Get the name of the enum member given its value.

        Args:
            value (int): The value of the enum member.

        Returns:
            str: The name of the enum member.
            None: If the value does not match any enum member.
        """
        for member in cls:
            if member.value == value:
                return member.name
        return None
    
class Tasks:
    def __init__(self, client):
        self.client = client

    def wait_for_task_completion(self, task_identifier, timeout=600, interval=5, expected_task_state: ZertoTaskStates = ZertoTaskStates.Completed):
        logging.debug(f'wait_for_task_completion(zvm_address={self.client.zvm_address}, task_identifier={task_identifier}, timeout={timeout}, interval={interval})')
        start_time = time.time()
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client.token}'
        }

        while True:
            url = f"https://{self.client.zvm_address}/v1/tasks/{task_identifier}"
            try:
                response = requests.get(url, headers=headers, verify=self.client.verify_certificate)
                response.raise_for_status()
                task_info = response.json()

                state = task_info.get("Status", {}).get("State", -1)
                progress = task_info.get("Status", {}).get("Progress", 0)
                logging.debug(f'Task response: status={ZertoTaskStates.get_name_by_value(state)}, progress={progress}')

                if state == expected_task_state.value and progress == 100:
                    logging.info("Task completed successfully.")
                    time.sleep(interval)
                    return task_info
                elif state == ZertoTaskStates.InProgress.value:
                    time.sleep(interval)
                    continue
                else:
                    logging.error(f'Task ID={task_identifier} failed. task state={ZertoTaskStates.get_name_by_value(state)}')
                    raise Exception(f"Task failed: {task_info.get('CompleteReason', 'No reason provided')}")
            except requests.exceptions.RequestException as e:
                logging.error(f"Request failed: {e}")
                raise