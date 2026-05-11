from typing import Literal
from pydantic import BaseModel, Field


class MaterialMetadata(BaseModel):
    """Structured metadata extracted from a training material web page."""

    name: str = Field(description="Title of the material")
    url: str = Field(description="URL of the material")
    description: str = Field(description="Description of the material")
    keywords: list[str] = Field(description="Key words that describe the material")
    contact: str = Field(description="Contact email")
    license: str = Field(
        description="License following SPDX standardized short identifier, e.g. CC-BY-4.0"
    )
    creativeWorkStatus: Literal["Archived", "Under Development", "Active", "Not found"] = Field(
        description="Current status of the material"
    )
    identifier: str = Field(description="DOI of the material")
    version: str = Field(description="Version of the material")
    dateCreated: str = Field(description="Creation date (YYYY-MM-DD)")
    dateModified: str = Field(description="Modified date (YYYY-MM-DD)")
    datePublished: str = Field(description="Published date (YYYY-MM-DD)")
    author: list[str] = Field(description="List of authors")
    contributor: list[str] = Field(description="List of contributors")
    field: str = Field(description="Scientific field of the material")
    audience: str = Field(description="Target audience of the material")
    learningResourceType: str = Field(description="Type of the material, e.g. Course")
    teaches: str = Field(description="Learning objectives of the material")
    competencyRequired: list[str] = Field(
        description="Prerequisites before taking the material"
    )