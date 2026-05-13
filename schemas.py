from typing import Literal
from pydantic import BaseModel, Field


class MaterialMetadata(BaseModel):
    """Structured metadata extracted from a training material web page."""

    description: str = Field(description="Description of the material")
    resource_type: list[
        Literal[
            "Blog post",
            "Case Study",
            "Course Materials",
            "Documentation",
            "E-learning",
            "Exercise",
            "Guide",
            "Handbook",
            "Lessons",
            "Podcast",
            "Poster",
            "Presentation",
            "Reference Material",
            "Slides",
            "Tutorial",
            "Video",
            "Webinar",
            "Workshop",
        ]
    ] = Field(description="Type of the material, MAY be more than one")
    # scientific_topics: str = Field(
    #     description="Scientific field of the material, following a certain ontology, by default from EDAM"
    # )
    
    licence: str = Field(
        description="Licence MUST follow SPDX standardized short identifier AND NOT the human readable format, e.g. it must be CC-BY-4.0 AND NOT Creative Commons ..."
    )
    status: Literal["archived", "under Development", "active"] = Field(
        description="Current status of the material"
    )
    contact: str = Field(description="Contact email")
    doi: str = Field(description="DOI of the material")
    version: str = Field(description="Version of the material")
    authors: list[str] = Field(description="List of authors")
    contributors: list[str] = Field(description="List of contributors")
    target_audience: list[
        Literal[
            "Data Steward",
            "Data Manager",
            "Data Scientist",
            "Master Student",
            "PhD Student",
            "Physicist",
            "Postdoc",
            "Project Manager",
            "Researcher",
            "Research Software Engineer",
            "Software Engineer",
            "Specialist",
            "Trainer",
            "Training Designer",
            "Training Instructor",
            "Teacher",
            "Undergraduate Student",
        ]
    ] = Field(description="Target audiences of the material")
    prerequisites: str = Field(
        description="Prerequisites before taking the material, MUST be written in Markdown"
    )
    competency_level: Literal["beginner", "intermediate", "advanced"] = Field(
        description="Expertise level to take the material"
    )
    learning_objectives: str = Field(description="Learning objectives of the material")
    date_created: str = Field(
        description="Creation date (YYYY-MM-DD), set to an empty string if not found in text"
    )
    date_modified: str = Field(
        description="Modified date (YYYY-MM-DD), set to an empty string if not found in text"
    )
    date_published: str = Field(
        description="Published date (YYYY-MM-DD), set to an empty string if not found in text"
    )
