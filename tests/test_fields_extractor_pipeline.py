import pytest
from unittest.mock import AsyncMock, patch
from schemas import MaterialMetadata
from fields_extractor_pipeline import (
    chunk_text,
    _merge_scalar,
    _dedup_preserve_order,
    _merge_list_field,
    merge_chunk_results,
    analyze_chunks_async,
    extract_page_metadata,
    PageExtractionReport,
)
from config import ProviderConfig

_TEST_PROVIDER = ProviderConfig(
    name="test",
    model="test-model",
    base_url="http://localhost:11434/v1",
    api_key_env=None,
    temperature=0.0,
    max_concurrency=2,
)


def make_metadata(**overrides):
    defaults = {
        "description": "Not found",
        # resource_type is a list but is NOT in _LIST_FIELDS, so merge_chunk_results
        # runs _merge_scalar on it. An empty list is falsy → treated as missing →
        # merged value becomes "Not found" → Pydantic rejects it.
        # Provide a real value so the scalar path returns a valid list.
        "resource_type": ["Tutorial"],
        "licence": "Not found",
        "status": "active",
        "contact": "Not found",
        "doi": "Not found",
        "version": "Not found",
        "authors": [],
        "contributors": [],
        "target_audience": [],
        "prerequisites": "Not found",
        "competency_level": "beginner",
        "learning_objectives": "Not found",
        "date_created": "",
        "date_modified": "",
        "date_published": "",
    }
    defaults.update(overrides)
    return MaterialMetadata(**defaults)


class TestChunkText:
    def test_empty_string_returns_empty_list(self):
        assert chunk_text("") == []

    def test_n_chunks_one_returns_full_text(self):
        assert chunk_text("hello world", n_chunks=1) == ["hello world"]

    def test_three_chunks_cover_full_text(self):
        text = "a" * 90
        chunks = chunk_text(text, n_chunks=3)
        assert "".join(chunks) == text

    def test_three_chunks_returns_roughly_three_pieces(self):
        text = "a" * 90
        chunks = chunk_text(text, n_chunks=3)
        assert len(chunks) == 3

    def test_two_chunks_cover_full_text(self):
        text = "hello world"
        chunks = chunk_text(text, n_chunks=2)
        assert "".join(chunks) == text

    def test_n_chunks_exceeds_text_length(self):
        text = "ab"
        chunks = chunk_text(text, n_chunks=10)
        assert "".join(chunks) == text

    def test_single_char_text(self):
        chunks = chunk_text("x", n_chunks=3)
        assert "".join(chunks) == "x"


class TestMergeScalar:
    def test_first_strategy_returns_first_value(self):
        assert _merge_scalar(["first", "second"], "first") == "first"

    def test_first_strategy_skips_not_found(self):
        assert _merge_scalar(["Not found", "actual"], "first") == "actual"

    def test_first_strategy_skips_empty_string(self):
        assert _merge_scalar(["", "actual"], "first") == "actual"

    def test_longest_strategy_returns_longest(self):
        result = _merge_scalar(["short", "a much longer value"], "longest")
        assert result == "a much longer value"

    def test_all_not_found_returns_not_found(self):
        assert _merge_scalar(["Not found", "Not found"], "first") == "Not found"

    def test_empty_list_returns_not_found(self):
        assert _merge_scalar([], "first") == "Not found"

    def test_longest_skips_not_found(self):
        result = _merge_scalar(["Not found", "actual value"], "longest")
        assert result == "actual value"


class TestDedupPreserveOrder:
    def test_removes_duplicates(self):
        assert _dedup_preserve_order(["a", "b", "a", "c"]) == ["a", "b", "c"]

    def test_removes_not_found(self):
        result = _dedup_preserve_order(["a", "Not found", "b"])
        assert result == ["a", "b"]

    def test_removes_empty_string(self):
        result = _dedup_preserve_order(["a", "", "b"])
        assert result == ["a", "b"]

    def test_preserves_insertion_order(self):
        assert _dedup_preserve_order(["c", "a", "b"]) == ["c", "a", "b"]

    def test_empty_input(self):
        assert _dedup_preserve_order([]) == []


class TestMergeListField:
    def test_union_of_two_lists(self):
        result = _merge_list_field([["a", "b"], ["b", "c"]])
        assert result == ["a", "b", "c"]

    def test_empty_lists(self):
        assert _merge_list_field([[], []]) == []

    def test_one_empty_one_non_empty(self):
        result = _merge_list_field([["a"], []])
        assert result == ["a"]

    def test_deduplication_across_chunks(self):
        result = _merge_list_field([["Alice", "Bob"], ["Bob", "Carol"]])
        assert result.count("Bob") == 1

    def test_preserves_order_from_first_chunk(self):
        result = _merge_list_field([["z", "a"], ["b"]])
        assert result[0] == "z"
        assert result[1] == "a"


class TestMergeChunkResults:
    def test_raises_on_empty_list(self):
        with pytest.raises(ValueError):
            merge_chunk_results([])

    def test_single_chunk_returns_its_values(self):
        m = make_metadata(description="hello", licence="MIT", authors=["Alice"])
        merged = merge_chunk_results([m])
        assert merged.description == "hello"
        assert merged.licence == "MIT"
        assert merged.authors == ["Alice"]

    def test_scalar_first_wins(self):
        m1 = make_metadata(licence="CC-BY-4.0")
        m2 = make_metadata(licence="MIT")
        assert merge_chunk_results([m1, m2]).licence == "CC-BY-4.0"

    def test_not_found_scalar_falls_through_to_second(self):
        m1 = make_metadata(licence="Not found")
        m2 = make_metadata(licence="MIT")
        assert merge_chunk_results([m1, m2]).licence == "MIT"

    def test_list_field_union_across_chunks(self):
        m1 = make_metadata(authors=["Alice"])
        m2 = make_metadata(authors=["Bob"])
        merged = merge_chunk_results([m1, m2])
        assert set(merged.authors) == {"Alice", "Bob"}

    def test_description_longest_wins(self):
        m1 = make_metadata(description="Short desc")
        m2 = make_metadata(description="A much longer description with more detail")
        merged = merge_chunk_results([m1, m2])
        assert merged.description == "A much longer description with more detail"

    def test_learning_objectives_longest_wins(self):
        m1 = make_metadata(learning_objectives="Learn A")
        m2 = make_metadata(learning_objectives="Learn A, B, and C in depth")
        merged = merge_chunk_results([m1, m2])
        assert merged.learning_objectives == "Learn A, B, and C in depth"

    def test_target_audience_deduplicated(self):
        m1 = make_metadata(target_audience=["Researcher", "PhD Student"])
        m2 = make_metadata(target_audience=["Researcher", "Data Scientist"])
        merged = merge_chunk_results([m1, m2])
        assert merged.target_audience.count("Researcher") == 1

    def test_returns_material_metadata_instance(self):
        m = make_metadata()
        result = merge_chunk_results([m])
        assert isinstance(result, MaterialMetadata)


class TestAnalyzeChunksAsync:
    async def test_empty_input_returns_empty_list(self):
        result = await analyze_chunks_async([])
        assert result == []

    async def test_returns_list_of_material_metadata(self):
        m = make_metadata(description="chunk result")

        with patch(
            "fields_extractor_pipeline.get_provider_config", return_value=_TEST_PROVIDER
        ):
            with patch("fields_extractor_pipeline.AsyncOpenAI") as MockOAI:
                MockOAI.return_value = AsyncMock()
                MockOAI.return_value.close = AsyncMock()
                with patch(
                    "fields_extractor_pipeline.analyze_content_with_llm_async",
                    new=AsyncMock(return_value=m),
                ):
                    result = await analyze_chunks_async(["chunk1", "chunk2"])

        assert len(result) == 2
        assert all(isinstance(r, MaterialMetadata) for r in result)

    async def test_raises_when_all_chunks_fail(self):
        with patch(
            "fields_extractor_pipeline.get_provider_config", return_value=_TEST_PROVIDER
        ):
            with patch("fields_extractor_pipeline.AsyncOpenAI") as MockOAI:
                MockOAI.return_value = AsyncMock()
                MockOAI.return_value.close = AsyncMock()
                with patch(
                    "fields_extractor_pipeline.analyze_content_with_llm_async",
                    new=AsyncMock(side_effect=RuntimeError("LLM unavailable")),
                ):
                    with pytest.raises(RuntimeError, match="All chunks failed"):
                        await analyze_chunks_async(["chunk1"], provider="test")

    async def test_partial_failures_are_tolerated(self):
        m = make_metadata(description="ok chunk")
        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("first chunk failed")
            return m

        with patch(
            "fields_extractor_pipeline.get_provider_config", return_value=_TEST_PROVIDER
        ):
            with patch("fields_extractor_pipeline.AsyncOpenAI") as MockOAI:
                MockOAI.return_value = AsyncMock()
                MockOAI.return_value.close = AsyncMock()
                with patch(
                    "fields_extractor_pipeline.analyze_content_with_llm_async",
                    new=side_effect,
                ):
                    result = await analyze_chunks_async(["chunk1", "chunk2"])

        assert len(result) == 1
        assert result[0].description == "ok chunk"


class TestExtractPageMetadata:
    async def test_returns_page_extraction_report(self):
        m = make_metadata(description="extracted metadata", resource_type=["Tutorial"])

        with patch(
            "fields_extractor_pipeline.analyze_chunks_async",
            new=AsyncMock(return_value=[m, m]),
        ):
            report = await extract_page_metadata("test page content", n_chunks=2)

        assert isinstance(report, PageExtractionReport)
        assert report.merged.description == "extracted metadata"
        assert len(report.chunks) == 2

    async def test_extraction_seconds_is_non_negative(self):
        m = make_metadata()

        with patch(
            "fields_extractor_pipeline.analyze_chunks_async",
            new=AsyncMock(return_value=[m]),
        ):
            report = await extract_page_metadata("content", n_chunks=1)

        assert report.extraction_seconds >= 0

    async def test_chunks_field_contains_per_chunk_results(self):
        m1 = make_metadata(description="chunk 1 result")
        m2 = make_metadata(description="chunk 2 result - longer for longest strategy")

        with patch(
            "fields_extractor_pipeline.analyze_chunks_async",
            new=AsyncMock(return_value=[m1, m2]),
        ):
            report = await extract_page_metadata("long content here", n_chunks=2)

        assert len(report.chunks) == 2
