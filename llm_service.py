"""Groq service for qualifying leads from Telegram conversations."""

import json
import logging
from typing import Any, TypedDict

from groq import Groq

from config import get_settings

logger = logging.getLogger(__name__)
MODEL_NAME = "llama-3.1-8b-instant"
DEFAULT_REASON = (
    "Razón no especificada por el modelo debido a una respuesta inesperada."
)


class LeadAnalysis(TypedDict):
    """Structured lead qualification result returned by the LLM."""

    qualified: bool
    reason: str


QUALIFICATION_PROMPT = """
You are an expert B2B lead qualification analyst.

Ideal Customer Profile:
- Service or consulting company.
- Has 5 or more employees.
- Located in Spain or LATAM.
- Has a clear need for automation, AI, efficiency, or process optimization.

Qualification rule:
- Return qualified=true only when the lead clearly matches the Ideal Customer Profile.
- Return qualified=false when the lead does not match the ICP.
- Return qualified=false when evidence is missing, the lead is outside the
  geography, the company is too small, or there is no automation or AI fit.

Output requirements:
- Return only one valid JSON object.
- The JSON object must contain exactly two keys: "qualified" and "reason".
- "qualified" must be a boolean.
- "reason" must be a 2-3 line explanation of the decision written strictly in Spanish.
""".strip()


def analyze_lead(lead_text: str) -> LeadAnalysis:
    """Analyze lead text and return the structured qualification decision."""
    settings = get_settings()
    client = Groq(api_key=settings.groq_api_key)

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": QUALIFICATION_PROMPT},
                {"role": "user", "content": lead_text},
            ],
            response_format={"type": "json_object"},
        )
    except Exception:
        logger.exception("Failed to request lead analysis from Groq.")
        raise

    return _parse_analysis_response(response.choices[0].message.content)


def _parse_analysis_response(content: str | None) -> LeadAnalysis:
    """Parse and validate the JSON response from the LLM."""
    if not content:
        raise ValueError("The model returned an empty response.")

    result: dict[str, Any] = json.loads(content)
    qualified = result.get("qualified")
    reason_value = result.get("reason", DEFAULT_REASON)

    if not isinstance(qualified, bool):
        raise ValueError('The model response is missing a boolean "qualified" value.')
    if not isinstance(reason_value, str) or not reason_value.strip():
        reason_value = DEFAULT_REASON

    return {
        "qualified": qualified,
        "reason": reason_value.strip(),
    }
