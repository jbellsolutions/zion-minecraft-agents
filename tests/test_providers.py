import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import zion_art
import zion_jev
import zion_provider


class ProviderTests(unittest.TestCase):
    def test_missing_artifact_is_not_success(self):
        with tempfile.TemporaryDirectory() as temp:
            request = Path(temp) / "request.json"
            request.write_text(json.dumps({"schema_version": 1, "request": "rainbow motorcycle"}))
            result = __import__("subprocess").CompletedProcess([], 0, "All done!")
            with patch.object(zion_provider, "executable", return_value="hermes"), \
                 patch.object(zion_provider.subprocess, "run", return_value=result):
                with self.assertRaisesRegex(RuntimeError, "manifest"):
                    zion_provider.run(request, Path(temp) / "output")

    def test_credential_redaction(self):
        self.assertEqual(zion_provider.redact("sk-or-v1-" + "a" * 64), "[redacted]")
        with patch.dict("os.environ", {"SOME_API_KEY": "long_private_value"}):
            self.assertEqual(zion_provider.redact("key long_private_value"), "key [redacted]")

    def test_jev_never_interprets_transport_success_as_supported(self):
        result = zion_jev.evaluate("works", "no game test", caller=lambda _: {"status": "available"})
        self.assertEqual(result["choice"], "unavailable")

    def test_jev_real_gateway_shape_and_cache(self):
        with tempfile.TemporaryDirectory() as temp:
            calls = []
            def caller(payload):
                calls.append(payload)
                return {"status": "available", "judgment": {"choice": "insufficient_evidence"}}
            a = zion_jev.evaluate("works", "no game test", cache=temp, caller=caller)
            b = zion_jev.evaluate("works", "no game test", cache=temp, caller=caller)
            self.assertEqual(a["choice"], "insufficient")
            self.assertEqual(a, b)
            self.assertEqual(len(calls), 1)

    def test_jev_timeout_reuses_request_id(self):
        with tempfile.TemporaryDirectory() as temp:
            calls = []
            def offline(payload):
                calls.append(payload["request_id"])
                raise TimeoutError()
            zion_jev.evaluate("works", "test", "first-id", temp, offline)
            zion_jev.evaluate("works", "test", "different-id", temp, offline)
            self.assertEqual(calls, ["first-id", "first-id"])

    def test_jev_origin_is_pinned(self):
        with patch.dict("os.environ", {"SUPER_BROWSER_URL": "https://unapproved.example", "SUPER_BROWSER_TOKEN": "test"}):
            with self.assertRaises(ValueError):
                zion_jev.connection()

    def test_icon_rejects_opaque_and_blank_outputs(self):
        from PIL import Image
        for color in ((100, 120, 200, 255), (0, 0, 0, 0)):
            raw = io.BytesIO()
            Image.new("RGBA", (64, 64), color).save(raw, format="PNG")
            with self.assertRaises(ValueError):
                zion_art.normalize(raw.getvalue())

    def test_icon_normalizes_real_alpha(self):
        from PIL import Image
        image = Image.new("RGBA", (128, 128))
        for x in range(20, 100):
            for y in range(40, 80):
                image.putpixel((x, y), (x * 2, y * 2, 100, 255))
        raw = io.BytesIO()
        image.save(raw, format="PNG")
        output = Image.open(io.BytesIO(zion_art.normalize(raw.getvalue())))
        self.assertEqual(output.size, (64, 64))
        self.assertEqual(output.mode, "RGBA")
        self.assertEqual(output.getpixel((0, 0))[3], 0)


if __name__ == "__main__":
    unittest.main()
