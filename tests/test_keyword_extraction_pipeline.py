import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from keyword_extraction_pipeline import _classify_batch, llm_inspect
from config import ProviderConfig

_TEST_PROVIDER = ProviderConfig(
    name="test",
    model="test-model",
    base_url="http://localhost:11434/v1",
    api_key_env=None,
    temperature=0.0,
    max_concurrency=1,
)


def _make_mock_client(response_payload: dict) -> AsyncMock:
    mock_resp = MagicMock()
    mock_resp.choices[0].message.content = json.dumps(response_payload)
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(return_value=mock_resp)
    return client


class TestClassifyBatch:
    async def test_returns_verdict_for_each_keyword(self):
        payload = {
            "verdicts": [
                {"keyword": "python", "reasoning": "core topic", "is_core": True},
                {
                    "keyword": "docker",
                    "reasoning": "barely mentioned",
                    "is_core": False,
                },
            ]
        }
        client = _make_mock_client(payload)
        semaphore = asyncio.Semaphore(1)
        batch = [("python", 10), ("docker", 2)]

        result = await _classify_batch(
            client, _TEST_PROVIDER, "doc text", batch, semaphore
        )

        assert len(result) == 2
        py_verdict = next(r for r in result if r["keyword"] == "python")
        docker_verdict = next(r for r in result if r["keyword"] == "docker")
        assert py_verdict["is_core"] is True
        assert docker_verdict["is_core"] is False

    async def test_preserves_count_in_output(self):
        payload = {
            "verdicts": [
                {"keyword": "python", "reasoning": "main topic", "is_core": True},
            ]
        }
        client = _make_mock_client(payload)
        semaphore = asyncio.Semaphore(1)

        result = await _classify_batch(
            client, _TEST_PROVIDER, "doc", [("python", 15)], semaphore
        )

        assert result[0]["count"] == 15

    async def test_missing_keyword_in_response_defaults_to_not_core(self):
        # LLM drops "docker" from response
        payload = {
            "verdicts": [
                {"keyword": "python", "reasoning": "used", "is_core": True},
            ]
        }
        client = _make_mock_client(payload)
        semaphore = asyncio.Semaphore(1)
        batch = [("python", 5), ("docker", 3)]

        result = await _classify_batch(client, _TEST_PROVIDER, "doc", batch, semaphore)

        assert len(result) == 2
        docker_result = next(r for r in result if r["keyword"] == "docker")
        assert docker_result["is_core"] is False

    async def test_all_false_on_llm_exception(self):
        client = AsyncMock()
        client.chat.completions.create = AsyncMock(side_effect=Exception("timeout"))
        semaphore = asyncio.Semaphore(1)
        batch = [("python", 5), ("docker", 3)]

        result = await _classify_batch(client, _TEST_PROVIDER, "doc", batch, semaphore)

        assert len(result) == 2
        assert all(r["is_core"] is False for r in result)

    async def test_all_false_on_invalid_json_response(self):
        mock_resp = MagicMock()
        mock_resp.choices[0].message.content = "not valid json {"
        client = AsyncMock()
        client.chat.completions.create = AsyncMock(return_value=mock_resp)
        semaphore = asyncio.Semaphore(1)
        batch = [("python", 5)]

        result = await _classify_batch(client, _TEST_PROVIDER, "doc", batch, semaphore)

        assert len(result) == 1
        assert result[0]["is_core"] is False

    async def test_empty_verdicts_array_defaults_all_to_false(self):
        payload = {"verdicts": []}
        client = _make_mock_client(payload)
        semaphore = asyncio.Semaphore(1)
        batch = [("python", 5), ("docker", 2)]

        result = await _classify_batch(client, _TEST_PROVIDER, "doc", batch, semaphore)

        assert all(r["is_core"] is False for r in result)


class TestLlmInspect:
    async def test_returns_verdicts_for_all_keywords(self):
        payload = {
            "verdicts": [
                {"keyword": "python", "reasoning": "core", "is_core": True},
                {"keyword": "docker", "reasoning": "used throughout", "is_core": True},
            ]
        }
        client = _make_mock_client(payload)

        with patch("keyword_extraction_pipeline.AsyncOpenAI", return_value=client):
            result = await llm_inspect(
                document="Python and Docker are used extensively",
                keyword_counts={"python": 10, "docker": 5},
                provider=_TEST_PROVIDER,
                batch_size=8,
            )

        assert len(result) == 2
        keywords = {r["keyword"] for r in result}
        assert keywords == {"python", "docker"}

    async def test_batches_are_split_by_batch_size(self):
        # 4 keywords with batch_size=2 should produce 2 LLM calls
        verdicts_batch1 = {
            "verdicts": [
                {"keyword": "a", "reasoning": "x", "is_core": True},
                {"keyword": "b", "reasoning": "x", "is_core": False},
            ]
        }
        verdicts_batch2 = {
            "verdicts": [
                {"keyword": "c", "reasoning": "x", "is_core": True},
                {"keyword": "d", "reasoning": "x", "is_core": False},
            ]
        }

        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            payload = verdicts_batch1 if call_count == 0 else verdicts_batch2
            call_count += 1
            mock_resp = MagicMock()
            mock_resp.choices[0].message.content = json.dumps(payload)
            return mock_resp

        client = AsyncMock()
        client.chat.completions.create = side_effect

        with patch("keyword_extraction_pipeline.AsyncOpenAI", return_value=client):
            result = await llm_inspect(
                document="doc",
                keyword_counts={"a": 4, "b": 3, "c": 2, "d": 1},
                provider=_TEST_PROVIDER,
                batch_size=2,
            )

        assert call_count == 2
        assert len(result) == 4

    async def test_is_core_true_for_kept_keywords(self):
        payload = {
            "verdicts": [
                {"keyword": "python", "reasoning": "main language", "is_core": True},
            ]
        }
        client = _make_mock_client(payload)

        with patch("keyword_extraction_pipeline.AsyncOpenAI", return_value=client):
            result = await llm_inspect(
                document="Python is the main language",
                keyword_counts={"python": 8},
                provider=_TEST_PROVIDER,
            )

        assert result[0]["is_core"] is True
        kept = [r["keyword"] for r in result if r["is_core"]]
        assert "python" in kept
