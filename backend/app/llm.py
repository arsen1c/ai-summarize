import json
import logging

import openai
from pydantic import ValidationError

from .schemas import AIOutput

logger = logging.getLogger(__name__)

MODEL = "gpt-4o-mini"
REQUEST_TIMEOUT_SECONDS = 20.0

_client = openai.OpenAI(timeout=REQUEST_TIMEOUT_SECONDS)

_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string", "description": "A concise 1-3 sentence summary of the text."},
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Exactly three short, relevant tags for the text.",
        },
    },
    "required": ["summary", "tags"],
    "additionalProperties": False,
}


class AIGenerationError(Exception):
    """Raised when the LLM call fails or returns output we can't trust."""


def generate_summary_and_tags(text: str) -> AIOutput:
    try:
        response = _client.chat.completions.create(
            model=MODEL,
            max_tokens=1024,
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "summary_and_tags", "schema": _OUTPUT_SCHEMA, "strict": True},
            },
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Summarize the following text in 1-3 sentences and provide "
                        "exactly three relevant, lowercase, hyphenated tags.\n\n"
                        f"Text:\n{text}"
                    ),
                }
            ],
        )
    except openai.APITimeoutError as exc:
        logger.warning("LLM request timed out")
        raise AIGenerationError("The AI service took too long to respond. Please try again.") from exc
    except openai.APIStatusError as exc:
        logger.warning("LLM request failed: %s", exc)
        raise AIGenerationError("The AI service returned an error. Please try again.") from exc
    except openai.APIConnectionError as exc:
        logger.warning("LLM connection error: %s", exc)
        raise AIGenerationError("Could not reach the AI service. Please try again.") from exc

    choice = response.choices[0] if response.choices else None
    if choice is None or choice.message.content is None:
        raise AIGenerationError("The AI did not return a usable response.")

    if choice.finish_reason == "content_filter":
        raise AIGenerationError("The AI declined to process this content.")

    try:
        parsed = json.loads(choice.message.content)
    except json.JSONDecodeError as exc:
        logger.warning("LLM returned invalid JSON: %s", choice.message.content[:200])
        raise AIGenerationError("The AI returned malformed output. Please try again.") from exc

    try:
        output = AIOutput.model_validate(parsed)
    except ValidationError as exc:
        logger.warning("LLM output failed schema validation: %s", exc)
        raise AIGenerationError("The AI output did not match the expected format.") from exc

    if len(output.tags) != 3:
        raise AIGenerationError("The AI did not return exactly three tags.")

    return output
