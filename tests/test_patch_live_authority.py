import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location("patch_authority", Path(__file__).parents[1] / "tools/patch_live_authority.py")
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)


class AuthorityTests(unittest.TestCase):
    def test_preserves_learned_patterns_corrects_advice_and_is_idempotent(self):
        original = '''---
name: minecraft-forge-authority
description: Learned Minecraft skill
---
Here is a learned seat implementation.
```java
server.execute(() -> placeSeat());
```
Use pack_format: 48.
```bash
pkill -f forge
rm -f world/session.lock
```
After crashes, kill + rm session.lock.
'''
        patched, counts = p.transform(original)
        self.assertTrue(patched.startswith("---\nname: minecraft-forge-authority"))
        self.assertIn("server.execute(() -> placeSeat());", patched)
        self.assertIn("pack_format: 46", patched)
        self.assertNotIn("pkill -f", patched)
        self.assertNotIn("rm -f", patched)
        self.assertEqual(counts["unsafe_shell_blocks"], 1)
        self.assertEqual(p.transform(patched)[0], patched)


if __name__ == "__main__":
    unittest.main()
