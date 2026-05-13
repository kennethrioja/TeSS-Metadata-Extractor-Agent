import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from schemas import MaterialMetadata
from llm_extractor import (
    build_user_message,
    _parse_or_raise,
    analyze_content_with_llm,
    analyze_content_with_llm_async,
)
from prompt_templates import FIELDS_PROMPT_TEMPLATE

_VALID_META = MaterialMetadata(
    description="A Python testing tutorial",
    resource_type=["Tutorial"],
    licence="CC-BY-4.0",
    status="active",
    contact="test@example.com",
    doi="Not found",
    version="1.0",
    authors=["Alice"],
    contributors=[],
    target_audience=["Researcher"],
    prerequisites="None",
    competency_level="beginner",
    learning_objectives="Learn how to test",
    date_created="",
    date_modified="",
    date_published="",
)

_MOCK_PROVIDER = MagicMock()
_MOCK_PROVIDER.name = "test"
_MOCK_PROVIDER.model = "test-model"
_MOCK_PROVIDER.temperature = 0.0
_MOCK_PROVIDER.api_key = "fake-key"
_MOCK_PROVIDER.base_url = "http://localhost:11434/v1"


class TestBuildUserMessage:
    def test_injects_content_into_template(self):
        content = "Python testing with pytest"
        result = build_user_message(content)
        assert content in result

    def test_matches_template_format(self):
        content = "test content"
        result = build_user_message(content)
        expected = FIELDS_PROMPT_TEMPLATE.format(scraped_text=content)
        assert result == expected

    def test_returns_string(self):
        assert isinstance(build_user_message("anything"), str)


class TestParseOrRaise:
    def test_returns_parsed_metadata(self):
        mock_completion = MagicMock()
        mock_completion.choices[0].message.parsed = _VALID_META
        assert _parse_or_raise(mock_completion) is _VALID_META

    def test_raises_value_error_on_none_parsed(self):
        mock_completion = MagicMock()
        mock_completion.choices[0].message.parsed = None
        mock_completion.choices[0].message.refusal = "Content policy violation"
        with pytest.raises(ValueError, match="no parsable output"):
            _parse_or_raise(mock_completion)

    def test_error_includes_refusal_message(self):
        mock_completion = MagicMock()
        mock_completion.choices[0].message.parsed = None
        mock_completion.choices[0].message.refusal = "I cannot help with that"
        with pytest.raises(ValueError, match="I cannot help with that"):
            _parse_or_raise(mock_completion)


class TestAnalyzeContentWithLlm:
    def test_returns_material_metadata(self):
        mock_completion = MagicMock()
        mock_completion.choices[0].message.parsed = _VALID_META
        mock_completion.choices[0].message.refusal = None

        mock_client = MagicMock()
        mock_client.beta.chat.completions.parse.return_value = mock_completion

        with patch("llm_extractor.get_provider_config", return_value=_MOCK_PROVIDER):
            with patch("llm_extractor.OpenAI", return_value=mock_client):
                result = analyze_content_with_llm("some scraped text")

        assert result is _VALID_META

    def test_passes_content_to_llm(self):
        mock_completion = MagicMock()
        mock_completion.choices[0].message.parsed = _VALID_META
        mock_completion.choices[0].message.refusal = None

        mock_client = MagicMock()
        mock_client.beta.chat.completions.parse.return_value = mock_completion

        with patch("llm_extractor.get_provider_config", return_value=_MOCK_PROVIDER):
            with patch("llm_extractor.OpenAI", return_value=mock_client):
                analyze_content_with_llm("unique test content xyz")

        messages = mock_client.beta.chat.completions.parse.call_args.kwargs["messages"]
        user_message = next(m for m in messages if m["role"] == "user")
        assert "unique test content xyz" in user_message["content"]


class TestAnalyzeContentWithLlmAsync:
    async def test_returns_metadata_with_provided_client(self):
        mock_completion = MagicMock()
        mock_completion.choices[0].message.parsed = _VALID_META
        mock_completion.choices[0].message.refusal = None

        mock_client = AsyncMock()
        mock_client.beta.chat.completions.parse = AsyncMock(
            return_value=mock_completion
        )

        with patch("llm_extractor.get_provider_config", return_value=_MOCK_PROVIDER):
            result = await analyze_content_with_llm_async(
                "test content", client=mock_client
            )

        assert result is _VALID_META

    async def test_does_not_close_external_client(self):
        mock_completion = MagicMock()
        mock_completion.choices[0].message.parsed = _VALID_META

        mock_client = AsyncMock()
        mock_client.beta.chat.completions.parse = AsyncMock(
            return_value=mock_completion
        )
        mock_client.close = AsyncMock()

        with patch("llm_extractor.get_provider_config", return_value=_MOCK_PROVIDER):
            await analyze_content_with_llm_async("test", client=mock_client)

        mock_client.close.assert_not_called()

    async def test_closes_own_client_after_call(self):
        mock_completion = MagicMock()
        mock_completion.choices[0].message.parsed = _VALID_META

        mock_client = AsyncMock()
        mock_client.beta.chat.completions.parse = AsyncMock(
            return_value=mock_completion
        )
        mock_client.close = AsyncMock()

        with patch("llm_extractor.get_provider_config", return_value=_MOCK_PROVIDER):
            with patch("llm_extractor.AsyncOpenAI", return_value=mock_client):
                await analyze_content_with_llm_async("test")

        mock_client.close.assert_called_once()

    async def test_closes_own_client_even_on_error(self):
        mock_client = AsyncMock()
        mock_client.beta.chat.completions.parse = AsyncMock(
            side_effect=RuntimeError("API down")
        )
        mock_client.close = AsyncMock()

        with patch("llm_extractor.get_provider_config", return_value=_MOCK_PROVIDER):
            with patch("llm_extractor.AsyncOpenAI", return_value=mock_client):
                with pytest.raises(RuntimeError, match="API down"):
                    await analyze_content_with_llm_async("test")

        mock_client.close.assert_called_once()
