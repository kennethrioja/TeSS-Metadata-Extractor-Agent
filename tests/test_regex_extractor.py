import re
from collections import Counter
from regex_extractor import (
    build_pattern,
    count_keyword_occurrences,
    split_keywords,
    load_keywords,
)


class TestBuildPattern:
    def test_simple_alphanumeric_word(self):
        pattern = build_pattern("python")
        assert re.search(pattern, "learn python today", re.IGNORECASE)

    def test_no_partial_match_for_alphanumeric(self):
        pattern = build_pattern("git")
        assert not re.search(pattern, "digital")
        assert not re.search(pattern, "forgotten")

    def test_matches_whole_word(self):
        pattern = build_pattern("git")
        assert re.search(pattern, "use git for version control")
        assert re.search(pattern, "git commit -m 'fix'")

    def test_c_plus_plus(self):
        pattern = build_pattern("c++")
        assert re.search(pattern, "programming in c++", re.IGNORECASE)
        assert re.search(pattern, "C++ is fast", re.IGNORECASE)

    def test_dotnet(self):
        pattern = build_pattern(".net")
        assert re.search(pattern, "build with .net framework", re.IGNORECASE)

    def test_multi_word_keyword(self):
        pattern = build_pattern("machine learning")
        assert re.search(pattern, "intro to machine learning", re.IGNORECASE)

    def test_multi_word_keyword_extra_whitespace(self):
        pattern = build_pattern("machine learning")
        assert re.search(pattern, "machine  learning with gaps", re.IGNORECASE)

    def test_empty_keyword_returns_empty_string(self):
        assert build_pattern("") == ""

    def test_underscore_boundary(self):
        pattern = build_pattern("ci_cd")
        assert re.search(pattern, "use ci_cd pipelines", re.IGNORECASE)

    def test_ci_cd_with_slash(self):
        pattern = build_pattern("ci/cd")
        assert re.search(pattern, "setting up ci/cd pipelines")


class TestCountKeywordOccurrences:
    def test_basic_count(self):
        counts = count_keyword_occurrences("python python python", ["python"])
        assert counts["python"] == 3

    def test_case_insensitive_default(self):
        counts = count_keyword_occurrences("Python PYTHON python", ["python"])
        assert counts["python"] == 3

    def test_case_sensitive_mode(self):
        counts = count_keyword_occurrences(
            "Python PYTHON python", ["python"], case_insensitive=False
        )
        assert counts["python"] == 1

    def test_multiple_keywords(self):
        text = "use python and docker for containerized apps"
        counts = count_keyword_occurrences(text, ["python", "docker", "kubernetes"])
        assert counts["python"] == 1
        assert counts["docker"] == 1
        assert "kubernetes" not in counts

    def test_empty_keyword_is_skipped(self):
        counts = count_keyword_occurrences("some text here", ["", "text"])
        assert "" not in counts
        assert counts["text"] == 1

    def test_no_matches_returns_empty_counter(self):
        counts = count_keyword_occurrences("hello world", ["python"])
        assert len(counts) == 0

    def test_returns_counter(self):
        counts = count_keyword_occurrences("python", ["python"])
        assert isinstance(counts, Counter)

    def test_no_partial_match(self):
        counts = count_keyword_occurrences("digital forgotten", ["git"])
        assert "git" not in counts

    def test_multi_word_keyword_count(self):
        text = "machine learning is used in machine learning courses"
        counts = count_keyword_occurrences(text, ["machine learning"])
        assert counts["machine learning"] == 2


class TestSplitKeywords:
    def test_selects_top_k_by_frequency(self):
        counts = Counter({"python": 10, "docker": 5, "git": 3, "r": 1})
        all_kws = ["python", "docker", "git", "r", "kubernetes"]
        selected, remaining = split_keywords(counts, all_kws, k=2)
        assert selected == ["python", "docker"]

    def test_remaining_excludes_selected(self):
        counts = Counter({"python": 10, "docker": 5})
        all_kws = ["python", "docker", "kubernetes"]
        selected, remaining = split_keywords(counts, all_kws, k=2)
        assert "python" not in remaining
        assert "docker" not in remaining
        assert "kubernetes" in remaining

    def test_k_larger_than_matched_count(self):
        counts = Counter({"python": 5})
        all_kws = ["python", "docker"]
        selected, remaining = split_keywords(counts, all_kws, k=10)
        assert selected == ["python"]
        assert remaining == ["docker"]

    def test_empty_counts_returns_all_as_remaining(self):
        counts = Counter()
        all_kws = ["python", "docker"]
        selected, remaining = split_keywords(counts, all_kws, k=5)
        assert selected == []
        assert set(remaining) == {"python", "docker"}

    def test_order_is_descending_by_count(self):
        counts = Counter({"a": 1, "b": 5, "c": 3})
        all_kws = ["a", "b", "c"]
        selected, _ = split_keywords(counts, all_kws, k=3)
        assert selected[0] == "b"
        assert selected[1] == "c"
        assert selected[2] == "a"


class TestLoadKeywords:
    def test_returns_non_empty_list(self):
        kws = load_keywords()
        assert isinstance(kws, list)
        assert len(kws) > 0

    def test_all_entries_are_strings(self):
        kws = load_keywords()
        assert all(isinstance(kw, str) for kw in kws)

    def test_no_empty_strings(self):
        kws = load_keywords()
        assert all(kw.strip() for kw in kws)
