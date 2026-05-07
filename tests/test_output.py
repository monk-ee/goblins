"""
tests/test_output.py — Tests for output path generation and results directory handling.
"""

import json
import os
import re


from goblin_test import RESULTS_DIR, default_output_path, resolve_output_path, save_json


# ---------------------------------------------------------------------------
# default_output_path
# ---------------------------------------------------------------------------


def test_default_output_path_under_results():
    path = default_output_path(["gpt-4o"], ["plain"])
    assert path.startswith(RESULTS_DIR + os.sep) or path.startswith(RESULTS_DIR + "/")


def test_default_output_path_is_json():
    path = default_output_path(["gpt-4o"], ["plain"])
    assert path.endswith(".json")


def test_default_output_path_contains_model():
    path = default_output_path(["gpt-4o"], ["plain"])
    assert "gpt-4o" in path


def test_default_output_path_contains_evasion():
    path = default_output_path(["gpt-4o"], ["synonym"])
    assert "synonym" in path


def test_default_output_path_timestamp_format():
    path = default_output_path(["gpt-5"], ["plain"])
    filename = os.path.basename(path)
    # Expect YYYY-MM-DD_HHMM at the start of the filename
    assert re.match(r"\d{4}-\d{2}-\d{2}_\d{4}_", filename)


def test_default_output_path_multiple_models_truncates():
    path = default_output_path(["gpt-4o", "gpt-5", "gpt-5-mini"], ["plain"])
    assert "plus1" in path


def test_default_output_path_two_models_no_truncation():
    path = default_output_path(["gpt-4o", "gpt-5"], ["plain"])
    assert "plus" not in path
    assert "gpt-4o" in path
    assert "gpt-5" in path


def test_default_output_path_multiple_evasions_truncates():
    path = default_output_path(["gpt-4o"], ["plain", "roleplay", "synonym"])
    assert "plus1" in path


# ---------------------------------------------------------------------------
# resolve_output_path
# ---------------------------------------------------------------------------


def test_resolve_none_returns_auto_path():
    path = resolve_output_path(None, ["gpt-4o"], ["plain"])
    assert path.startswith(RESULTS_DIR)


def test_resolve_bare_filename_goes_under_results():
    path = resolve_output_path("myrun.json", ["gpt-4o"], ["plain"])
    assert path == os.path.join(RESULTS_DIR, "myrun.json")


def test_resolve_path_with_directory_passes_through():
    path = resolve_output_path("/tmp/custom/output.json", ["gpt-4o"], ["plain"])
    assert path == "/tmp/custom/output.json"


def test_resolve_relative_path_with_dir_passes_through():
    path = resolve_output_path("custom/output.json", ["gpt-4o"], ["plain"])
    assert path == "custom/output.json"


# ---------------------------------------------------------------------------
# save_json — directory creation
# ---------------------------------------------------------------------------


def test_save_json_creates_parent_dir(tmp_path):
    nested = tmp_path / "nested" / "deep" / "out.json"
    save_json([], str(nested))
    assert nested.exists()
    data = json.loads(nested.read_text())
    assert data == []


def test_save_json_writes_model_results(tmp_path):
    from unittest.mock import MagicMock
    from goblin.runner import ModelResult

    mr = MagicMock(spec=ModelResult)
    mr.model = "gpt-4o"
    mr.evasion = "plain"
    mr.total_score = 42
    mr.level = ("FULL GOBLIN MODE", "red")
    mr.prompt_count = 4
    mr.results = []

    out = tmp_path / "test_out.json"
    save_json([mr], str(out))

    data = json.loads(out.read_text())
    assert len(data) == 1
    assert data[0]["model"] == "gpt-4o"
    assert data[0]["total_score"] == 42
