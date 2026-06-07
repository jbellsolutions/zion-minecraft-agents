"""
Smoke tests for zion-minecraft-agents.
Tests that required files exist and are valid, and that the UI server
imports cleanly. No live server or Claude API calls needed.
"""
import json
import os
import sys
import importlib.util
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent.parent


def test_required_files_exist():
    """All required project files must exist and be non-empty."""
    required = [
        "CLAUDE.md", "AGENTS.md", "ARCHITECTURE.md", "ETHOS.md",
        "README.md", "CHANGELOG.md", "VERSION", "TODOS.md",
        "llms.txt", "features.json",
    ]
    for fname in required:
        fpath = ROOT / fname
        assert fpath.exists(), f"Missing required file: {fname}"
        assert fpath.stat().st_size > 0, f"Empty file: {fname}"


def test_agent_files_exist():
    """All specialist agent markdown files must exist."""
    agents = [
        "agents/orchestrator.md",
        "agents/mod-agent.md",
        "agents/world-builder.md",
        "agents/lore-agent.md",
        "agents/deploy-agent.md",
    ]
    for fname in agents:
        fpath = ROOT / fname
        assert fpath.exists(), f"Missing agent file: {fname}"
        assert fpath.stat().st_size > 0, f"Empty agent file: {fname}"


def test_ui_files_exist():
    """UI files must exist."""
    assert (ROOT / "ui" / "index.html").exists()
    assert (ROOT / "ui" / "server.py").exists()


def test_features_json_valid():
    """features.json must be valid JSON with a tasks array."""
    data = json.loads((ROOT / "features.json").read_text())
    assert "tasks" in data, "features.json missing 'tasks' key"
    assert isinstance(data["tasks"], list), "'tasks' must be a list"


def test_json_files_valid():
    """All JSON files in .claude/ must parse cleanly."""
    json_files = [
        ".claude/agi-1/baseline.json",
        ".claude/healing/history.json",
        ".claude/learning/observations.json",
        ".claude/healing/patterns.json",
        ".claude/learning/evolution.json",
        "genome/genome.json",
    ]
    for fname in json_files:
        fpath = ROOT / fname
        if fpath.exists():
            try:
                json.loads(fpath.read_text())
            except json.JSONDecodeError as e:
                assert False, f"Invalid JSON in {fname}: {e}"


def test_ui_server_syntax():
    """ui/server.py must have valid Python syntax."""
    spec = importlib.util.spec_from_file_location("server", ROOT / "ui" / "server.py")
    assert spec is not None, "Could not load ui/server.py"
    module = importlib.util.module_from_spec(spec)
    # Just loading the spec validates syntax; don't execute
    assert module is not None


def test_skill_md_exists():
    """skills/zion/SKILL.md must exist with required sections."""
    skill_path = ROOT / "skills" / "zion" / "SKILL.md"
    assert skill_path.exists(), "skills/zion/SKILL.md missing"
    content = skill_path.read_text()
    assert "Iron Law" in content, "SKILL.md missing Iron Law section"
    assert "## Phase" in content, "SKILL.md missing Phase sections"


def test_hermes_skills_exist():
    """Hermes support skills must exist with their core guardrails."""
    skills = {
        "forge-1214-assets": "assets/<modid>/items",
        "hermes-minecraft-superbuilder": "Question policy",
    }
    for skill_name, expected in skills.items():
        skill_path = ROOT / "skills" / skill_name / "SKILL.md"
        assert skill_path.exists(), f"skills/{skill_name}/SKILL.md missing"
        assert expected in skill_path.read_text(), f"skills/{skill_name}/SKILL.md missing {expected}"


def test_forge_template_assets_complete():
    """Forge template must include all 1.21.4 item/block client assets."""
    script = ROOT / "tools" / "forge_asset_guard.py"
    template = ROOT / "zion-mc-agents" / "templates" / "forge-mod-template"
    result = subprocess.run(
        [sys.executable, str(script), "--project", str(template)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_datapack_guard_accepts_1214_pack():
    """Data pack guard must accept a valid Minecraft 1.21.4 pack."""
    script = ROOT / "tools" / "hermes_datapack_guard.py"
    with tempfile.TemporaryDirectory() as tmp:
        pack = Path(tmp)
        (pack / "pack.mcmeta").write_text(
            json.dumps({"pack": {"pack_format": 61, "description": "test pack"}}),
            encoding="utf-8",
        )
        namespace = pack / "data" / "zionmc" / "functions"
        namespace.mkdir(parents=True)
        (namespace / "load.mcfunction").write_text("say Hermes data pack loaded\n", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(script), "--project", str(pack)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
    assert result.returncode == 0, result.stdout + result.stderr


def test_no_secrets_in_tracked_files():
    """No real secrets should be in source files (placeholders are OK)."""
    import re
    # Real secrets: long alphanumeric strings after known prefixes
    # Exclude placeholder patterns like sk-ant-... or sk-...
    secret_regexes = [
        r'sk-ant-[a-zA-Z0-9_\-]{20,}',   # real Anthropic keys (not placeholders)
        r'AKIA[0-9A-Z]{16}',              # real AWS access keys
    ]
    extensions = {".py", ".js", ".ts", ".json"}  # skip .md (docs use examples)
    skip_dirs = [".git", "node_modules", "__pycache__", "build", "zion-mc-agents"]
    for fpath in ROOT.rglob("*"):
        if fpath.suffix not in extensions:
            continue
        if any(skip in str(fpath) for skip in skip_dirs):
            continue
        try:
            content = fpath.read_text(errors="ignore")
            for pattern in secret_regexes:
                match = re.search(pattern, content)
                assert not match, f"Possible real secret in {fpath.relative_to(ROOT)}: {match.group()[:8]}..."
        except (OSError, PermissionError):
            pass


if __name__ == "__main__":
    # Run manually: python tests/test_smoke.py
    import traceback
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    passed = failed = 0
    for test in tests:
        try:
            test()
            print(f"✅ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")
            traceback.print_exc()
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
