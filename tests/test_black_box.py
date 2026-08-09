import json
import logging
from pathlib import Path
import tempfile
import unittest

from E_Helper.E_BlackBox import get_black_box, subscribe, unsubscribe


class BlackBoxTests(unittest.TestCase):
    def test_writes_json_next_to_feature_and_redacts_secret(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            script = Path(temp_dir) / "E_demo_feature.py"
            script.write_text("# test feature", encoding="utf-8")

            black_box = get_black_box(script, run_id="run-test", level=logging.DEBUG)
            black_box.info("Đã gọi Bearer private-token", symbol="VNM", api_key="private-key")

            for handler in black_box._logger.handlers:
                handler.flush()

            self.assertEqual(black_box.log_path, Path(temp_dir) / "E_demo_feature.log")
            event = json.loads(black_box.log_path.read_text(encoding="utf-8").splitlines()[-1])
            self.assertEqual(event["feature"], "E_demo_feature")
            self.assertEqual(event["run_id"], "run-test")
            self.assertEqual(event["context"]["symbol"], "VNM")
            self.assertEqual(event["context"]["api_key"], "***REDACTED***")
            self.assertNotIn("private-token", event["message"])
            black_box.close()

    def test_publishes_event_to_ui_subscriber(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            script = Path(temp_dir) / "E_ui_source.py"
            script.write_text("# test feature", encoding="utf-8")
            received = []
            callback = received.append

            subscribe(callback)
            try:
                black_box = get_black_box(script)
                black_box.warning("Kết quả thiếu một nguồn", source="RSS")
            finally:
                unsubscribe(callback)

            self.assertEqual(received[-1]["level"], "WARNING")
            self.assertEqual(received[-1]["feature"], "E_ui_source")
            self.assertEqual(received[-1]["context"]["source"], "RSS")
            black_box.close()

    def test_rejects_non_python_owner(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_owner = Path(temp_dir) / "feature.txt"
            with self.assertRaisesRegex(ValueError, "file Python"):
                get_black_box(invalid_owner)


if __name__ == "__main__":
    unittest.main()
