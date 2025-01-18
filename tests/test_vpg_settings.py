import unittest
from unittest.mock import patch, MagicMock
from zvma import ZVMAClient

class TestVPGSettings(unittest.TestCase):
    def setUp(self):
        self.client = ZVMAClient(zvm_address="example.com", username="your_username", password="your_password")

    @patch('zvma.vpg_settings.requests.post')
    def test_create_vpg_settings(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "vpg_settings_id"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        vpg_payload = {"Basic": {"Name": "VPG1"}}
        vpg_settings = self.client.vpg_settings.create_vpg_settings(vpg_payload)
        self.assertEqual(vpg_settings["id"], "vpg_settings_id")

    @patch('zvma.vpg_settings.requests.get')
    def test_list_vpg_settings(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = [{"id": "vpg_settings_id1"}, {"id": "vpg_settings_id2"}]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        vpg_settings_list = self.client.vpg_settings.list_vpg_settings()
        self.assertEqual(len(vpg_settings_list), 2)
        self.assertEqual(vpg_settings_list[0]["id"], "vpg_settings_id1")

    @patch('zvma.vpg_settings.requests.get')
    def test_get_vpg_settings_by_id(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "vpg_settings_id"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        vpg_settings = self.client.vpg_settings.get_vpg_settings_by_id("vpg_settings_id")
        self.assertEqual(vpg_settings["id"], "vpg_settings_id")

    @patch('zvma.vpg_settings.requests.put')
    def test_update_vpg_settings(self, mock_put):
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "vpg_settings_id"}
        mock_response.raise_for_status = MagicMock()
        mock_put.return_value = mock_response

        vpg_payload = {"Basic": {"Name": "VPG1"}}
        vpg_settings = self.client.vpg_settings.update_vpg_settings("vpg_settings_id", vpg_payload)
        self.assertEqual(vpg_settings["id"], "vpg_settings_id")

    @patch('zvma.vpg_settings.requests.delete')
    def test_delete_vpg_settings(self, mock_delete):
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "vpg_settings_id"}
        mock_response.raise_for_status = MagicMock()
        mock_delete.return_value = mock_response

        response = self.client.vpg_settings.delete_vpg_settings("vpg_settings_id")
        self.assertEqual(response["id"], "vpg_settings_id")

if __name__ == '__main__':
    unittest.main()