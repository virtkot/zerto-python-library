import unittest
from unittest.mock import patch, MagicMock
from zvma import ZVMAClient

class TestTasks(unittest.TestCase):
    def setUp(self):
        self.client = ZVMAClient(zvm_address="example.com", username="your_username", password="your_password")

    @patch('zvma.tasks.requests.get')
    def test_wait_for_task_completion(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"Status": {"State": 0, "Progress": 100}}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        task_info = self.client.tasks.wait_for_task_completion(task_identifier="task_id")
        self.assertEqual(task_info["Status"]["State"], 0)
        self.assertEqual(task_info["Status"]["Progress"], 100)

if __name__ == '__main__':
    unittest.main()