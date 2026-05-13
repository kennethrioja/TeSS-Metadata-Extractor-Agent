import pytest
import yaml
from unittest.mock import patch
from config import ProviderConfig, _load_yaml, get_provider_config, list_providers

SAMPLE_CONFIG = {
    "default_provider": "test_provider",
    "providers": {
        "test_provider": {
            "model": "test-model",
            "base_url": "http://localhost:11434/v1",
            "api_key_env": "TEST_API_KEY",
            "temperature": 0.0,
            "max_concurrency": 2,
        },
        "another_provider": {
            "model": "another-model",
            "base_url": "http://localhost:8080/v1",
            "api_key_env": None,
            "temperature": 0.5,
            "max_concurrency": 1,
        },
    },
}


class TestProviderConfig:
    def test_api_key_reads_from_env(self, monkeypatch):
        monkeypatch.setenv("MY_TEST_KEY", "secret-value")
        cfg = ProviderConfig(
            name="p",
            model="m",
            base_url="http://x",
            temperature=0.0,
            api_key_env="MY_TEST_KEY",
        )
        assert cfg.api_key == "secret-value"

    def test_api_key_none_when_env_missing(self, monkeypatch):
        monkeypatch.delenv("MISSING_KEY_XYZ", raising=False)
        cfg = ProviderConfig(
            name="p",
            model="m",
            base_url="http://x",
            temperature=0.0,
            api_key_env="MISSING_KEY_XYZ",
        )
        assert cfg.api_key is None

    def test_api_key_none_when_no_env_var_configured(self):
        cfg = ProviderConfig(
            name="p",
            model="m",
            base_url="http://x",
            temperature=0.0,
        )
        assert cfg.api_key is None

    def test_default_max_concurrency(self):
        cfg = ProviderConfig(
            name="p",
            model="m",
            base_url="http://x",
            temperature=0.0,
        )
        assert cfg.max_concurrency == 1


class TestLoadYaml:
    def test_raises_file_not_found_for_missing_path(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            _load_yaml(tmp_path / "nonexistent.yaml")

    def test_loads_valid_yaml(self, tmp_path):
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(yaml.dump(SAMPLE_CONFIG))
        result = _load_yaml(cfg_file)
        assert result["default_provider"] == "test_provider"
        assert "providers" in result
        assert "test_provider" in result["providers"]


class TestGetProviderConfig:
    def test_returns_default_provider_when_none_given(self):
        with patch("config._load_yaml", return_value=SAMPLE_CONFIG):
            cfg = get_provider_config()
        assert cfg.name == "test_provider"
        assert cfg.model == "test-model"
        assert cfg.max_concurrency == 2

    def test_returns_named_provider(self):
        with patch("config._load_yaml", return_value=SAMPLE_CONFIG):
            cfg = get_provider_config("another_provider")
        assert cfg.name == "another_provider"
        assert cfg.model == "another-model"
        assert cfg.temperature == 0.5

    def test_raises_value_error_for_unknown_provider(self):
        with patch("config._load_yaml", return_value=SAMPLE_CONFIG):
            with pytest.raises(ValueError, match="Unknown provider"):
                get_provider_config("nonexistent_provider")

    def test_error_message_lists_available_providers(self):
        with patch("config._load_yaml", return_value=SAMPLE_CONFIG):
            with pytest.raises(ValueError) as exc_info:
                get_provider_config("bad")
        assert "test_provider" in str(exc_info.value)


class TestListProviders:
    def test_returns_all_provider_names(self):
        with patch("config._load_yaml", return_value=SAMPLE_CONFIG):
            providers = list_providers()
        assert set(providers) == {"test_provider", "another_provider"}

    def test_returns_list(self):
        with patch("config._load_yaml", return_value=SAMPLE_CONFIG):
            providers = list_providers()
        assert isinstance(providers, list)

    def test_empty_when_no_providers(self):
        with patch("config._load_yaml", return_value={"providers": {}}):
            assert list_providers() == []
