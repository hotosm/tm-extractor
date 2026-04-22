import json

import pytest

from tm_extractor import (
    ConfigError,
    EnvVarError,
    ProjectProcessor,
    load_packaged_config,
    resolve_config,
    validate_environment,
)


@pytest.fixture
def env_with_token(monkeypatch):
    monkeypatch.setenv("RAWDATA_API_AUTH_TOKEN", "test-token")
    monkeypatch.delenv("TASKING_MANAGER_API_KEY", raising=False)
    return monkeypatch


def test_package_has_entry_point():
    from tm_extractor import main

    assert callable(main)


def test_load_packaged_config_returns_expected_shape():
    config = load_packaged_config()
    assert isinstance(config, dict)
    assert {"geometry", "dataset", "categories"}.issubset(config.keys())


def test_resolve_config_none_falls_back_to_packaged():
    config = resolve_config(None)
    assert isinstance(config, dict)
    assert "categories" in config


def test_resolve_config_missing_path_raises():
    with pytest.raises(ConfigError, match="not found"):
        resolve_config("/nonexistent/path/config.json")


def test_resolve_config_existing_path_returns_path(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"geometry": {}, "dataset": {}, "categories": []}))
    assert resolve_config(str(config_file)) == str(config_file)


def test_validate_environment_missing_token_raises(monkeypatch):
    monkeypatch.delenv("RAWDATA_API_AUTH_TOKEN", raising=False)
    with pytest.raises(EnvVarError, match="RAWDATA_API_AUTH_TOKEN"):
        validate_environment()


def test_validate_environment_applies_defaults(env_with_token):
    env = validate_environment()
    assert env["RAWDATA_API_AUTH_TOKEN"] == "test-token"
    assert env["RAW_DATA_API_BASE_URL"].startswith("https://")
    assert env["API_MAX_RETRIES"] == "3"


def test_project_processor_builds_from_packaged_config(env_with_token):
    processor = ProjectProcessor(load_packaged_config())
    assert processor.max_retries == 3
    assert isinstance(processor.api_timeout, int)
    assert processor.RAW_DATA_SNAPSHOT_URL.endswith("/custom/snapshot/")


def test_project_processor_requires_config():
    with pytest.raises(ValueError, match="Config JSON"):
        ProjectProcessor(None)


@pytest.mark.parametrize(
    "input_value,expected",
    [
        (1, "Roads"),
        (2, "Buildings"),
        (3, "Waterways"),
        (4, "Landuse"),
        (99, None),
        ("ROADS", "Roads"),
        ("buildings", "Buildings"),
        ("UNKNOWN", None),
        (object(), None),
    ],
)
def test_get_mapping_list(env_with_token, input_value, expected):
    processor = ProjectProcessor(load_packaged_config())
    assert processor.get_mapping_list(input_value) == expected


def test_generate_filtered_config_filters_categories(env_with_token):
    processor = ProjectProcessor(load_packaged_config())
    geometry = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}

    payload = json.loads(
        processor.generate_filtered_config(
            project_id=42, mapping_types=["Buildings"], geometry=geometry
        )
    )

    assert payload["dataset"]["dataset_prefix"] == "hotosm_project_42"
    assert payload["geometry"] == geometry
    assert len(payload["categories"]) == 1
    assert "Buildings" in payload["categories"][0]
