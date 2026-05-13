import pytest
from config import ProviderConfig
from schemas import MaterialMetadata

SAMPLE_YAML_CONFIG = {
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

TEST_PROVIDER_CONFIG = ProviderConfig(
    name="test_provider",
    model="test-model",
    base_url="http://localhost:11434/v1",
    api_key_env=None,
    temperature=0.0,
    max_concurrency=1,
)

VALID_METADATA_KWARGS = {
    "description": "A tutorial on Python testing",
    "resource_type": ["Tutorial"],
    "licence": "CC-BY-4.0",
    "status": "active",
    "contact": "test@example.com",
    "doi": "10.1234/test",
    "version": "1.0",
    "authors": ["Alice"],
    "contributors": [],
    "target_audience": ["Researcher"],
    "prerequisites": "Basic Python knowledge",
    "competency_level": "beginner",
    "learning_objectives": "Learn how to write tests",
    "date_created": "2024-01-01",
    "date_modified": "",
    "date_published": "",
}


@pytest.fixture
def sample_yaml_config():
    return SAMPLE_YAML_CONFIG


@pytest.fixture
def provider_config():
    return TEST_PROVIDER_CONFIG


@pytest.fixture
def minimal_metadata():
    return MaterialMetadata(**VALID_METADATA_KWARGS)
