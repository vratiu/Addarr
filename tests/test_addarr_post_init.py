import os
import sys
import unittest
import asyncio
from unittest.mock import patch, AsyncMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

class TestAddarrBridgeIntegration(unittest.TestCase):
    def setUp(self):
        import config as app_config
        self.orig_miniapp = dict(app_config.config.get("miniapp", {}))

    def tearDown(self):
        import config as app_config
        app_config.config["miniapp"] = self.orig_miniapp

    @patch("bridge.start_bridge_listener", new_callable=AsyncMock)
    def test_post_init_starts_bridge_when_enabled(self, mock_listener):
        from addarr import on_post_init
        import config as app_config

        app_config.config["miniapp"] = {"enable": True}

        async def run_test():
            await on_post_init(None)
            # Give created tasks a chance to execute in loop
            await asyncio.sleep(0.01)

        asyncio.run(run_test())
        self.assertTrue(mock_listener.called)

    @patch("bridge.start_bridge_listener", new_callable=AsyncMock)
    def test_post_init_skips_when_disabled(self, mock_listener):
        from addarr import on_post_init
        import config as app_config

        app_config.config["miniapp"] = {"enable": False}
        async def run_test():
            await on_post_init(None)
            await asyncio.sleep(0.01)

        asyncio.run(run_test())
        self.assertFalse(mock_listener.called)


if __name__ == "__main__":
    unittest.main()
