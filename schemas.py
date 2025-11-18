"""
Database Schemas for AI RFP App

Each Pydantic model represents a collection in MongoDB.
Collection name is the lowercase of the class name.
"""

from pydantic import BaseModel, Field
from typing import Optional, List

class Rfp(BaseModel):
    """
    RFP collection schema
    Collection name: "rfp"
    """
    title: str = Field(..., description="RFP title")
    description: Optional[str] = Field(None, description="Short description of the RFP")
    status: str = Field("draft", description="draft | published | archived")

class Rfpsection(BaseModel):
    """
    RFP Section collection schema
    Collection name: "rfpsection"
    """
    rfp_id: str = Field(..., description="Reference to RFP _id as string")
    heading: str = Field(..., description="Section heading/title")
    content: str = Field("", description="Rich text/markdown content for the section")
    order: int = Field(0, description="Display order within the RFP")

class Aigeneration(BaseModel):
    """
    History of AI generations (optional, for auditing)
    Collection name: "aigeneration"
    """
    rfp_id: str = Field(..., description="RFP id")
    section_id: Optional[str] = Field(None, description="Section id if applicable")
    prompt: str = Field(..., description="Prompt used for generation")
    output: str = Field(..., description="Generated text")
