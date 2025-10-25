"""Pydantic schema for analysis feedback.

This module defines AnalysisFeedback, a simple Pydantic model
used to carry feedback from a speech/analysis pipeline.
"""
from typing import List

from pydantic import BaseModel, Field


class AnalysisFeedback(BaseModel):
    """Model representing feedback generated from an analysis.

    Fields
    - confidence_score: float between 0.0 and 1.0 inclusive
    - filler_word_count: non-negative integer
    - filler_words_list: list of detected filler words (strings)
    - sentiment: textual sentiment label (e.g., 'positive', 'neutral', 'negative')
    - concise_summary: short summary of findings
    - feedback_tip: a short actionable tip
    """

    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    filler_word_count: int = Field(..., ge=0, description="Number of filler words detected (non-negative)")
    filler_words_list: List[str] = Field(..., description="List of detected filler words")
    sentiment: str = Field(..., description="Detected sentiment, e.g. 'positive'|'neutral'|'negative'")
    concise_summary: str = Field(..., description="Concise summary of the analysis")
    feedback_tip: str = Field(..., description="Actionable tip to improve")

    class Config:
        anystr_strip_whitespace = True
        min_anystr_length = 0

    # Added in Clarity Coach / WPM support
    wpm_feedback: str = Field(
        "",
        description="Feedback on the user's pace based on their WPM.",
    )


class ClarityFeedback(BaseModel):
    """Feedback focused on speech clarity for non-native speakers.

    Fields:
    - clarity_score: float between 0.0 and 1.0
    - pace_assessment: string like 'Good', 'Too Fast', 'Too Slow'
    - filler_word_count: non-negative integer
    - delivery_tip: a single actionable tip to improve clarity
    """

    clarity_score: float = Field(..., ge=0.0, le=1.0, description="Clarity score between 0.0 and 1.0")
    pace_assessment: str = Field(..., description="Pace assessment, e.g., 'Good', 'Too Fast', 'Too Slow'")
    filler_word_count: int = Field(..., ge=0, description="Number of filler words detected (non-negative)")
    delivery_tip: str = Field(..., description="Single actionable tip to improve delivery/clarity")

    class Config:
        anystr_strip_whitespace = True
        min_anystr_length = 0
