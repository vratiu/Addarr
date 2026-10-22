import asyncio
import os
import sys
import threading
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import bridge


class TestBridgeResilience(unittest.TestCase):
    def setUp(self):
        bridge._rate_limit_buckets.clear()
        bridge._listener = None
        bridge._app = None

    def tearDown(self):
        bridge.stop_bridge_listener()
        bridge._listener = None
        bridge._app = None

    def test_safe_close_listener_handles_none_and_exceptions(self):
        # Must not raise on None
        bridge._safe_close_listener(None)

        # Must close resp and session, join thread
        mock_listener = MagicMock()
        mock_sse = MagicMock()
        mock_resp = MagicMock()
        mock_session = MagicMock()
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True

        mock_listener._sse = mock_sse
        mock_sse.resp = mock_resp
        mock_sse.session = mock_session
        mock_listener._thread = mock_thread

        bridge._safe_close_listener(mock_listener)

        self.assertFalse(mock_sse.should_connect)
        self.assertEqual(mock_sse.retry, 0)
        mock_resp.close.assert_called_once()
        mock_session.close.assert_called_once()
        mock_thread.join.assert_called_once_with(timeout=2.0)

    def test_patch_firebase_listener_catches_ssl_error(self):
        bridge._patch_firebase_listener_if_needed()

        from firebase_admin import db
        self.assertTrue(getattr(db.ListenerRegistration, "_addarr_patched", False))

        # Create a mock ListenerRegistration
        fake_reg = db.ListenerRegistration.__new__(db.ListenerRegistration)
        fake_sse = MagicMock()
        fake_sse.should_connect = True

        import requests
        ssl_err = requests.exceptions.SSLError("UNEXPECTED_EOF_WHILE_READING")

        def failing_generator():
            raise ssl_err
            yield None

        fake_sse.__iter__.side_effect = failing_generator
        fake_reg._sse = fake_sse
        fake_reg._callback = MagicMock()

        thread = threading.Thread(target=fake_reg._start_listen)
        with patch.object(bridge.logger, "warning") as mock_warn:
            thread.start()
            thread.join(timeout=2.0)
            self.assertFalse(thread.is_alive())
            mock_warn.assert_called()
            self.assertIn("Bridge listener SSE stream disconnected", mock_warn.call_args[0][0])

    def test_patch_firebase_listener_ignores_intentional_shutdown(self):
        bridge._patch_firebase_listener_if_needed()

        from firebase_admin import db
        fake_reg = db.ListenerRegistration.__new__(db.ListenerRegistration)
        fake_sse = MagicMock()
        fake_sse.should_connect = False  # Intentionally closed

        def closing_generator():
            raise Exception("Socket closed")
            yield None

        fake_sse.__iter__.side_effect = closing_generator
        fake_reg._sse = fake_sse
        fake_reg._callback = MagicMock()

        thread = threading.Thread(target=fake_reg._start_listen)
        with patch.object(bridge.logger, "warning") as mock_warn:
            thread.start()
            thread.join(timeout=2.0)
            self.assertFalse(thread.is_alive())
            mock_warn.assert_not_called()

    def test_supervisor_reconnects_when_thread_dies(self):
        mock_db = MagicMock()
        mock_ref = MagicMock()
        mock_db.reference.return_value = mock_ref

        # First listener thread is dead (simulating SSL crash)
        dead_thread = MagicMock()
        dead_thread.is_alive.return_value = False
        listener_1 = MagicMock()
        listener_1._thread = dead_thread

        # Second listener thread is alive
        alive_thread = MagicMock()
        alive_thread.is_alive.return_value = True
        listener_2 = MagicMock()
        listener_2._thread = alive_thread

        mock_ref.listen.return_value = listener_2
        bridge._listener = listener_1

        with patch.dict(bridge.config, {"miniapp": {"enable": True}}):
            with patch("bridge.init_firebase_app", return_value=MagicMock()):
                with patch("firebase_admin.db", mock_db):
                    async def run_supervisor():
                        await bridge.start_bridge_listener(poll_interval=0.01, run_once=True)

                    asyncio.run(run_supervisor())

        # listener_1 was closed and listener_2 was started
        listener_1._thread.join.assert_called()
        self.assertEqual(bridge._listener, listener_2)
        mock_ref.listen.assert_called_once()

    def test_supervisor_handles_listen_exception_with_retry(self):
        mock_db = MagicMock()
        mock_ref = MagicMock()
        mock_db.reference.return_value = mock_ref

        alive_thread = MagicMock()
        alive_thread.is_alive.return_value = True
        good_listener = MagicMock()
        good_listener._thread = alive_thread

        import requests
        mock_ref.listen.side_effect = [
            requests.exceptions.SSLError("Connection reset"),
            good_listener,
        ]

        async def run_supervisor():
            with patch.dict(bridge.config, {"miniapp": {"enable": True}}):
                with patch("bridge.init_firebase_app", return_value=MagicMock()):
                    with patch("firebase_admin.db", mock_db):
                        # With poll_interval=0.01, run 2 iterations
                        task = asyncio.create_task(bridge.start_bridge_listener(poll_interval=0.01))
                        # Wait for first failed call (backoff sleep) and cancel task
                        await asyncio.sleep(0.02)
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass

        asyncio.run(run_supervisor())
        self.assertGreaterEqual(mock_ref.listen.call_count, 1)

    def test_init_firebase_app_reuses_existing_app(self):
        mock_existing_app = MagicMock()
        with patch("firebase_admin.get_app", return_value=mock_existing_app):
            app = bridge.init_firebase_app()
            self.assertEqual(app, mock_existing_app)


if __name__ == "__main__":
    unittest.main()
