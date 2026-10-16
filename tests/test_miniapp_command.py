import os
import sys
import unittest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

class TestMiniAppCommand(unittest.TestCase):
    @patch("addarr.checkId", return_value=True)
    def test_open_miniapp_sends_webapp_button(self, mock_check_id):
        from addarr import open_miniapp
        import config as app_config

        app_config.config["miniapp"] = {"url": "https://my-addarr.web.app"}

        update = MagicMock()
        update.effective_message.chat_id = 12345
        context = MagicMock()
        context.bot.send_message = AsyncMock()

        asyncio.run(open_miniapp(update, context))

        self.assertTrue(context.bot.send_message.called)
        call_kwargs = context.bot.send_message.call_args[1]
        self.assertEqual(call_kwargs["chat_id"], 12345)
        markup = call_kwargs["reply_markup"]
        self.assertIsNotNone(markup)
        button = markup.inline_keyboard[0][0]
        self.assertEqual(button.text, "🚀 Open Addarr Mini App")
        self.assertEqual(button.web_app.url, "https://my-addarr.web.app")


if __name__ == "__main__":
    unittest.main()
