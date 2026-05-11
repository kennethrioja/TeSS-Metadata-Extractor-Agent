import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

load_dotenv()

CONFIG_PATH = Path(__file__).parent / "config.yaml"


@dataclass
class ProviderConfig:
    name: str
    model: str
    base_url: str
    temperature: float
    api_key_env: Optional[str] = None

    @property
    def api_key(self) -> Optional[str]:
        """Read the API key from the environment variable defined in the config."""
        if not self.api_key_env:
            return None
        return os.environ.get(self.api_key_env)


def _load_yaml(path: Path = CONFIG_PATH) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_provider_config(provider_name: Optional[str] = None) -> ProviderConfig:
    """
    Return the configuration for a given provider.
    If no provider is given, the default one from config.yaml is used.
    """
    config = _load_yaml()
    providers = config.get("providers", {})

    if provider_name is None:
        provider_name = config.get("default_provider")

    if provider_name not in providers:
        available = ", ".join(providers.keys())
        raise ValueError(
            f"Unknown provider '{provider_name}'. Available: {available}"
        )

    return ProviderConfig(name=provider_name, **providers[provider_name])


def list_providers() -> list[str]:
    """Return the list of provider names available in the config."""
    return list(_load_yaml().get("providers", {}).keys())

