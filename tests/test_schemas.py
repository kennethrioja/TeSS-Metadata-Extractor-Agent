import pytest
from pydantic import ValidationError
from schemas import MaterialMetadata

VALID_DATA = {
    "description": "A Python testing tutorial",
    "resource_type": ["Tutorial"],
    "licence": "CC-BY-4.0",
    "status": "active",
    "contact": "test@example.com",
    "doi": "10.1234/test",
    "version": "1.0",
    "authors": ["Alice", "Bob"],
    "contributors": [],
    "target_audience": ["Researcher"],
    "prerequisites": "Basic Python",
    "competency_level": "beginner",
    "learning_objectives": "Learn pytest",
    "date_created": "2024-01-01",
    "date_modified": "",
    "date_published": "",
}


class TestMaterialMetadataConstruction:
    def test_valid_minimal_construction(self):
        m = MaterialMetadata(**VALID_DATA)
        assert m.description == "A Python testing tutorial"
        assert m.status == "active"
        assert m.competency_level == "beginner"
        assert m.licence == "CC-BY-4.0"

    def test_list_fields_are_lists(self):
        m = MaterialMetadata(**VALID_DATA)
        assert isinstance(m.resource_type, list)
        assert isinstance(m.authors, list)
        assert isinstance(m.contributors, list)
        assert isinstance(m.target_audience, list)

    def test_empty_lists_are_valid(self):
        data = {**VALID_DATA, "authors": [], "contributors": [], "target_audience": []}
        m = MaterialMetadata(**data)
        assert m.authors == []

    def test_multiple_resource_types(self):
        data = {**VALID_DATA, "resource_type": ["Tutorial", "Video", "Slides"]}
        m = MaterialMetadata(**data)
        assert len(m.resource_type) == 3

    def test_multiple_target_audiences(self):
        data = {
            **VALID_DATA,
            "target_audience": ["Researcher", "PhD Student", "Data Scientist"],
        }
        m = MaterialMetadata(**data)
        assert len(m.target_audience) == 3

    def test_all_valid_statuses(self):
        for status in ("archived", "under Development", "active"):
            m = MaterialMetadata(**{**VALID_DATA, "status": status})
            assert m.status == status

    def test_all_valid_competency_levels(self):
        for level in ("beginner", "intermediate", "advanced"):
            m = MaterialMetadata(**{**VALID_DATA, "competency_level": level})
            assert m.competency_level == level

    def test_empty_date_strings_are_valid(self):
        data = {
            **VALID_DATA,
            "date_created": "",
            "date_modified": "",
            "date_published": "",
        }
        m = MaterialMetadata(**data)
        assert m.date_created == ""


class TestMaterialMetadataValidation:
    def test_invalid_resource_type_raises(self):
        with pytest.raises(ValidationError):
            MaterialMetadata(**{**VALID_DATA, "resource_type": ["InvalidType"]})

    def test_invalid_status_raises(self):
        with pytest.raises(ValidationError):
            MaterialMetadata(**{**VALID_DATA, "status": "published"})

    def test_invalid_competency_level_raises(self):
        with pytest.raises(ValidationError):
            MaterialMetadata(**{**VALID_DATA, "competency_level": "expert"})

    def test_invalid_target_audience_raises(self):
        with pytest.raises(ValidationError):
            MaterialMetadata(**{**VALID_DATA, "target_audience": ["Astronaut"]})

    def test_one_invalid_in_list_raises(self):
        data = {**VALID_DATA, "resource_type": ["Tutorial", "NotARealType"]}
        with pytest.raises(ValidationError):
            MaterialMetadata(**data)
