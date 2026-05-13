from unittest.mock import AsyncMock, MagicMock, patch
from collections import Counter
from schemas import MaterialMetadata
from fields_extractor_pipeline import PageExtractionReport
from full_metadata_pipeline import get_all_metadata

_MERGED = MaterialMetadata(
    description="A tutorial on Python",
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
    learning_objectives="Learn Python testing",
    date_created="",
    date_modified="",
    date_published="",
)

_REPORT = PageExtractionReport(
    merged=_MERGED,
    chunks=[_MERGED],
    extraction_seconds=0.1,
)

_SCRAPED = {"https://example.com": "Python is the primary language used throughout."}


def _patch_all(
    scraped=_SCRAPED,
    keywords=["python", "docker", "git"],
    counts=Counter({"python": 10, "docker": 3}),
    verdicts=None,
    report=_REPORT,
    sleep=True,
):
    """Return a context manager stack that patches every external call."""
    if verdicts is None:
        verdicts = [
            {"keyword": "python", "is_core": True},
            {"keyword": "docker", "is_core": False},
        ]

    patches = [
        patch(
            "full_metadata_pipeline.scrape_site_to_dict",
            new=AsyncMock(return_value=scraped),
        ),
        patch("full_metadata_pipeline.load_keywords", return_value=keywords),
        patch("full_metadata_pipeline.count_keyword_occurrences", return_value=counts),
        patch(
            "full_metadata_pipeline.split_keywords",
            return_value=(list(counts.keys()), []),
        ),
        patch(
            "full_metadata_pipeline.llm_inspect", new=AsyncMock(return_value=verdicts)
        ),
        patch(
            "full_metadata_pipeline.extract_page_metadata",
            new=AsyncMock(return_value=report),
        ),
        patch("full_metadata_pipeline.get_provider_config", return_value=MagicMock()),
    ]
    if sleep:
        patches.append(patch("full_metadata_pipeline.asyncio.sleep", new=AsyncMock()))
    return patches


class TestGetAllMetadata:
    async def test_returns_dict_with_fields_and_keywords(self):
        async with _apply(*_patch_all()):
            result = await get_all_metadata("https://example.com", sleep_seconds=0)

        assert isinstance(result, dict)
        assert "description" in result
        assert "keywords" in result

    async def test_llm_activated_attaches_kept_keywords(self):
        async with _apply(
            *_patch_all(
                verdicts=[
                    {"keyword": "python", "is_core": True},
                    {"keyword": "docker", "is_core": False},
                ]
            )
        ):
            result = await get_all_metadata(
                "https://example.com", llm_activated=True, sleep_seconds=0
            )

        assert "python" in result["keywords"]
        assert "docker" not in result["keywords"]

    async def test_llm_disabled_keeps_regex_top_k_as_keywords(self):
        counts = Counter({"python": 10, "docker": 3})
        async with _apply(*_patch_all(counts=counts)):
            result = await get_all_metadata(
                "https://example.com",
                llm_activated=False,
                sleep_seconds=0,
            )

        # When LLM is off, selected = list(counts.keys()) from our split_keywords mock
        assert set(result["keywords"]) == set(counts.keys())

    async def test_llm_inspect_not_called_when_disabled(self):
        mock_llm_inspect = AsyncMock()
        patches = _patch_all()
        # Replace the llm_inspect patch with a spy
        async with _apply(*patches):
            with patch("full_metadata_pipeline.llm_inspect", new=mock_llm_inspect):
                await get_all_metadata(
                    "https://example.com", llm_activated=False, sleep_seconds=0
                )

        mock_llm_inspect.assert_not_called()

    async def test_sleep_is_skipped_when_zero(self):
        mock_sleep = AsyncMock()
        async with _apply(*_patch_all(sleep=False)):
            with patch("full_metadata_pipeline.asyncio.sleep", new=mock_sleep):
                await get_all_metadata("https://example.com", sleep_seconds=0)

        mock_sleep.assert_not_called()

    async def test_sleep_is_called_when_positive(self):
        mock_sleep = AsyncMock()
        async with _apply(*_patch_all(sleep=False)):
            with patch("full_metadata_pipeline.asyncio.sleep", new=mock_sleep):
                await get_all_metadata("https://example.com", sleep_seconds=2.5)

        mock_sleep.assert_called_once_with(2.5)

    async def test_merged_metadata_fields_present_in_result(self):
        async with _apply(*_patch_all()):
            result = await get_all_metadata("https://example.com", sleep_seconds=0)

        for field in ("description", "licence", "status", "authors"):
            assert field in result


# ---------------------------------------------------------------------------
# Minimal async context-manager helper (avoids adding contextlib2 dependency)
# ---------------------------------------------------------------------------


class _apply:
    """Stack multiple unittest.mock.patch context managers."""

    def __init__(self, *patches):
        self._patches = patches
        self._started = []

    async def __aenter__(self):
        for p in self._patches:
            self._started.append(p.__enter__())
        return self

    async def __aexit__(self, *exc):
        for p in reversed(self._patches):
            p.__exit__(*exc)
