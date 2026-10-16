import os
import sys
import time
import hmac
import hashlib
import json
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "cloud", "auth")))

import main as auth_main


class TestAuthVerification(unittest.TestCase):
    def setUp(self):
        self.bot_token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
        self.user = {"id": 987654321, "first_name": "Test", "username": "testuser"}
        self.auth_date = int(time.time())

        # Generate valid test signature
        user_json = json.dumps(self.user, separators=(',', ':'))
        raw_items = [
            f"auth_date={self.auth_date}",
            f"query_id=AAHdF6IQAAAAAN0XohDhrOrc",
            f"user={user_json}"
        ]
        raw_items.sort()
        data_check_string = "\n".join(raw_items)

        secret_key = hmac.new(b"WebAppData", self.bot_token.encode("utf-8"), hashlib.sha256).digest()
        self.valid_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

        self.valid_init_data = (
            f"query_id=AAHdF6IQAAAAAN0XohDhrOrc&user={user_json}&auth_date={self.auth_date}&hash={self.valid_hash}"
        )

    def test_valid_init_data(self):
        is_valid, user_data = auth_main.verify_telegram_init_data(self.valid_init_data, self.bot_token)
        self.assertTrue(is_valid)
        self.assertIsNotNone(user_data)
        self.assertEqual(user_data["id"], 987654321)
        self.assertEqual(user_data["username"], "testuser")

    def test_tampered_init_data(self):
        # Tamper with the user id
        tampered_init_data = self.valid_init_data.replace("987654321", "111111111")
        is_valid, user_data = auth_main.verify_telegram_init_data(tampered_init_data, self.bot_token)
        self.assertFalse(is_valid)
        self.assertIsNone(user_data)

    def test_expired_init_data(self):
        old_auth_date = int(time.time()) - 100000
        user_json = json.dumps(self.user, separators=(',', ':'))
        data_check_string = f"auth_date={old_auth_date}\nuser={user_json}"
        secret_key = hmac.new(b"WebAppData", self.bot_token.encode("utf-8"), hashlib.sha256).digest()
        old_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
        expired_init_data = f"user={user_json}&auth_date={old_auth_date}&hash={old_hash}"

        is_valid, _ = auth_main.verify_telegram_init_data(expired_init_data, self.bot_token, max_age_seconds=86400)
        self.assertFalse(is_valid)

    @patch("main.create_token_for_telegram_user", return_value="mock_jwt_token_123")
    def test_handler_success(self, mock_create_token):
        res = auth_main.handler({"initData": self.valid_init_data}, self.bot_token)
        self.assertEqual(res["statusCode"], 200)
        self.assertEqual(res["token"], "mock_jwt_token_123")
        self.assertEqual(res["user"]["id"], 987654321)


if __name__ == "__main__":
    unittest.main()
