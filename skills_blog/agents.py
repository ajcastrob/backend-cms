from pydantic import BaseModel, Field
from django_ai_core.contrib.agents import registry
from wagtail_ai.agents.content_feedback import ContentFeedbackAgent, SpecificImprovement


class GeminiContentFeedbackSchema(BaseModel):
    quality_score: int = Field(
        description="Quality score between 1 and 3 (1=needs major improvement, 2=adequate, 3=excellent)",
        ge=1,
        le=3,
    )
    qualitative_feedback: list[str] = Field(
        description="3-5 bullet points of qualitative feedback highlighting strengths and areas for improvement",
        min_length=3,
        max_length=5,
    )
    specific_improvements: list[SpecificImprovement] = Field(
        description="Specific text improvements with original text, suggested revised text, and a brief explanation",
        min_length=1,
    )


@registry.register()
class GeminiContentFeedbackAgent(ContentFeedbackAgent):
    slug = "wai_content_feedback"
    _response_format = GeminiContentFeedbackSchema

    def _get_result(self, messages):
        if messages and all(m.get("role") == "system" for m in messages):
            messages = list(messages)
            messages[-1] = {"role": "user", "content": messages[-1]["content"]}
        return super()._get_result(messages)
