import unittest
from zvma import ZVMAClient

class TestZVMAClient(unittest.TestCase):
    def setUp(self):
        self.client = ZVMAClient(zvm_address="example.com", username="your_username", password="your_password")

    def test_authenticate(self):
        self.assertIsNotNone(self.client.token)

if __name__ == '__main__':
    unittest.main()