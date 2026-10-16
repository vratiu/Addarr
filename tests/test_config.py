import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
import config as app_config


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.orig_miniapp = dict(app_config.config.get("miniapp", {}))

    def tearDown(self):
        app_config.config["miniapp"] = self.orig_miniapp

    def test_default_miniapp_settings(self):
        app_config.config["miniapp"] = {"enable": False}
        self.assertFalse(app_config.config["miniapp"].get("enable"))

    def test_miniapp_validation_when_disabled(self):
        app_config.config["miniapp"] = {"enable": False}
        missing = app_config.checkConfig()
        # Should not flag miniapp keys as missing when disabled
        self.assertNotIn("miniapp/databaseURL", missing)

    def test_miniapp_validation_when_enabled(self):
        app_config.config["miniapp"] = {"enable": True, "databaseURL": ""}
        missing = app_config.checkConfig()
        self.assertIn("miniapp/databaseURL", missing)



if __name__ == "__main__":
    unittest.main()
