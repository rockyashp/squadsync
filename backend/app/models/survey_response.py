"""
Backwards-compatibility re-export module for SurveyAnswer.
"""

from app.models.survey_answer import SurveyAnswer, SurveyResponse

__all__ = ["SurveyAnswer", "SurveyResponse"]
