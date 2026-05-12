from typing import Literal
from pydantic import BaseModel, Field


class MaterialMetadata(BaseModel):
    """Structured metadata extracted from a training material web page."""

    description: str = Field(
        description="Description of the material"
    )
    resource_type: list[Literal["Blog post", "Case Study", "Course Materials", "Documentation", "E-learning", "Exercise", "Guide", "Handbook", "Lessons", "Podcast", "Poster", "Presentation", "Reference Material", "Slides", "Tutorial", "Video", "Webinar", "Workshop"]] = Field(
        description="Type of the material"
    )
    # scientific_topics: str = Field(
    #     description="Scientific field of the material, following a certain ontology, by default from EDAM"
    # )
    keywords: list[str] = Field(
        description="Keywords that describe the material"
    )
    licence: str = Field(
        description="Licence following SPDX standardized short identifier, e.g. CC-BY-4.0"
    )
    status: Literal["archived", "under Development", "active"] = Field(
        description="Current status of the material"
    )
    contact: str = Field(
        description="Contact email"
    )
    doi: str = Field(
        description="DOI of the material"
    )
    version: str = Field(
        description="Version of the material"
    )
    authors: list[str] = Field(
        description="List of authors"
    )
    contributors: list[str] = Field(
        description="List of contributors"
    )
    target_audience: list[Literal["Data Steward", "Data Manager", "Data Scientist", "Master Student", "PhD Student", "Physicist", "Postdoc", "Project Manager", "Researcher", "Research Software Engineer", "Software Engineer", "Specialist", "Trainer", "Training Designer", "Training Instructor", "Teacher", "Undergraduate Student"]] = Field(
        description="Target audiences of the material"
    )
    prerequisites: list[str] = Field(
        description="Prerequisites before taking the material"
    )
    competency_level: Literal["beginner", "intermediate", "advanced"] = Field(
        description="Expertise level to take the material"
    )
    learning_objectives: str = Field(
        description="Learning objectives of the material"
    )
    dateCreated: str = Field(
        description="Creation date (YYYY-MM-DD)"
    )
    dateModified: str = Field(
        description="Modified date (YYYY-MM-DD)"
    )
    datePublished: str = Field(
        description="Published date (YYYY-MM-DD)"
    )