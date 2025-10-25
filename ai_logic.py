"""AI integration helpers.

Contains analyze_response_gpt4o which calls gpt-4o and returns an
AnalysisFeedback instance parsed from the model's JSON output.
"""
from typing import Optional
import json
import traceback

from openai import OpenAI

from analysis_schema import AnalysisFeedback, ClarityFeedback
import db_manager
from system_prompts import (
    ANALYZE_RESPONSE_SYSTEM_PROMPT,
    CAREER_COACH_SYSTEM_PROMPT,
    ADAPTIVE_QUESTION_SYSTEM_PROMPT_TEMPLATE,
    STAFF_ENGINEER_SYSTEM_PROMPT,
    SEVEN_DAY_STRATEGY_SYSTEM_PROMPT,
    PANEL_ALEX_PROMPT,
    PANEL_SARAH_PROMPT,
    PANEL_DAVID_PROMPT,
    CLARITY_COACH_PROMPT,
)


def _extract_text_from_response(resp) -> str:
    """Robustly extract textual content from a Responses API object."""
    # The SDK may return structured output in different shapes. Try common paths.
    parts = []
    try:
        # new Responses API: resp.output -> list of {"content": [{"type":"output_text","text":...}, ...]}
        for item in getattr(resp, "output", []) or []:
            for content in item.get("content", []) or []:
                # content can be dict-like with 'text'
                if isinstance(content, dict):
                    text = content.get("text") or content.get("payload") or None
                    if text:
                        parts.append(text)
                else:
                    # fallback: string
                    parts.append(str(content))
    except Exception:
        # fallback - try older chat completion shape
        try:
            choices = getattr(resp, "choices", []) or []
            if choices:
                msg = choices[0].get("message") or choices[0].get("message", {})
                # message.content may be a string or list
                content = msg.get("content") if isinstance(msg, dict) else None
                if isinstance(content, str):
                    parts.append(content)
        except Exception:
            parts.append(str(resp))

    return "\n".join(parts).strip()


def analyze_response_gpt4o(user_transcript: str, avg_wpm: int) -> Optional[AnalysisFeedback]:
    """Call gpt-4o (JSON mode) to analyze a user transcript.

    Returns an AnalysisFeedback instance on success, or None on error.

    The AI is instructed (via the system prompt) to return only JSON that
    adheres to the AnalysisFeedback schema saved in analysis_schema.AnalysisFeedback.
    We parse the model output as JSON and validate it with Pydantic.
    """
    client = OpenAI()

    # Format the analysis prompt with average WPM so the model can populate wpm_feedback
    system_prompt = ANALYZE_RESPONSE_SYSTEM_PROMPT.format(avg_wpm=avg_wpm)

    user_prompt = (
        "Analyze the following transcript and produce the JSON described in the system prompt:\n\n"
        f"{user_transcript}"
    )

    try:
        resp = client.responses.create(
            model="gpt-4o",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
        )

        text = _extract_text_from_response(resp)

        if not text:
            raise ValueError("Empty response from model")

        # The model was instructed to return pure JSON. Load it.
        payload = json.loads(text)

        # Validate/parse with Pydantic
        feedback = AnalysisFeedback.parse_obj(payload)
        return feedback

    except Exception as exc:  # pragma: no cover - runtime error handling
        # Print debug info; caller can inspect logs as needed.
        print("Error in analyze_response_gpt4o:")
        traceback.print_exc()
        print("Model/raw text was:\n", locals().get("text", "<no text>"))
        print("Exception:", exc)
        return None


def generate_perfect_answer(question: str) -> Optional[str]:
    """Generate a concise, helpful answer to question using gpt-4o.

    Returns the text answer or None on error.
    """
    client = OpenAI()

    system_prompt = CAREER_COACH_SYSTEM_PROMPT

    user_prompt = f"Answer this career question concisely:\n\n{question}"

    try:
        resp = client.responses.create(
            model="gpt-4o",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )

        text = _extract_text_from_response(resp)
        if not text:
            raise ValueError("Empty response from model")

        return text

    except Exception:  # pragma: no cover - runtime error handling
        print("Error in generate_perfect_answer:")
        traceback.print_exc()
        return None


def analyze_clarity_response_gpt4o(user_transcript: str) -> Optional[ClarityFeedback]:
    """Call gpt-4o (JSON mode) to analyze a user transcript for delivery/clarity.

    Returns a ClarityFeedback instance on success, or None on error.
    The AI is instructed to return only JSON that matches the ClarityFeedback schema.
    """
    client = OpenAI()

    system_prompt = CLARITY_COACH_PROMPT

    user_prompt = (
        "Analyze the following transcript and produce the JSON described in the system prompt (focus ONLY on delivery/clarity):\n\n"
        f"{user_transcript}"
    )

    try:
        resp = client.responses.create(
            model="gpt-4o",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
        )

        text = _extract_text_from_response(resp)

        if not text:
            raise ValueError("Empty response from model")

        # The model was instructed to return pure JSON. Load it.
        payload = json.loads(text)

        # Validate/parse with Pydantic
        feedback = ClarityFeedback.parse_obj(payload)
        return feedback

    except Exception as exc:  # pragma: no cover - runtime error handling
        # Print debug info; caller can inspect logs as needed.
        print("Error in analyze_clarity_response_gpt4o:")
        traceback.print_exc()
        print("Model/raw text was:\n", locals().get("text", "<no text>"))
        print("Exception:", exc)
        return None


def generate_adaptive_question(current_question: str, user_answer: str, user_id: str) -> Optional[str]:
    """Generate the next logical interview question using RAG + gpt-4o.

    Steps:
    - Fetch a personalized conversation context for the user via db_manager.get_personalized_context(user_id).
    - Fetch the user's resume context via db_manager.get_resume_context(user_id).
    - Combine both into a single combined_context with conversation history and resume data.
    - Call gpt-4o with a system prompt that includes the combined context, current question, and the user's answer.
    - Return the next logical interview question as plain text, or None on error.
    """

    client = OpenAI()

    try:
        # Retrieve conversation RAG context and resume context for this user (functions provided by P3's db_manager)
        conv_context = db_manager.get_personalized_context(user_id)
        resume_context = db_manager.get_resume_context(user_id)

        combined_context = f"CONVERSATION HISTORY:\n{conv_context}\n\nRESUME DATA:\n{resume_context}"

        # System prompt includes the combined context (conversation + resume) and the conversation state per requirements.
        system_prompt = ADAPTIVE_QUESTION_SYSTEM_PROMPT_TEMPLATE.format(
            combined_context=combined_context,
            current_question=current_question,
            user_answer=user_answer,
        )

        user_prompt = "Please provide the next interview question."

        resp = client.responses.create(
            model="gpt-4o",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.25,
        )

        text = _extract_text_from_response(resp)
        if not text:
            raise ValueError("Empty response from model")

        # Return the first non-empty line as the question, trimmed.
        question_lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        next_question = question_lines[0] if question_lines else text.strip()
        return next_question

    except Exception:  # pragma: no cover - runtime error handling
        print("Error in generate_adaptive_question:")
        traceback.print_exc()
        # Debugging hints
        try:
            print("combined_context:", combined_context)
        except Exception:
            print("combined_context: <unavailable>")
        try:
            print("Model/raw text was:\n", locals().get("text", "<no text>"))
        except Exception:
            pass
        return None


def generate_panel_question(persona_name: str, current_question: str, user_answer: str, user_id: str) -> Optional[str]:
    """Generate the next interview question from a panel persona.

    persona_name selects the persona: 'alex', 'sarah', or 'david'. Uses RAG via db_manager.get_personalized_context(user_id).
    Returns a single follow-up question (plain text) or None on error.
    """
    client = OpenAI()

    try:
        rag_context = db_manager.get_personalized_context(user_id)

        # select persona prompt template
        name = (persona_name or "").strip().lower()
        if name == "alex":
            template = PANEL_ALEX_PROMPT
        elif name == "sarah":
            template = PANEL_SARAH_PROMPT
        elif name == "david":
            template = PANEL_DAVID_PROMPT
        else:
            # default to Alex (hiring manager) if unknown
            template = PANEL_ALEX_PROMPT

        system_prompt = template.format(
            rag_context=rag_context,
            current_question=current_question,
            user_answer=user_answer,
        )

        user_prompt = "Please provide the follow-up question (single line)."

        resp = client.responses.create(
            model="gpt-4o",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.25,
        )

        text = _extract_text_from_response(resp)
        if not text:
            raise ValueError("Empty response from model")

        question_lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        next_question = question_lines[0] if question_lines else text.strip()
        return next_question

    except Exception:  # pragma: no cover - runtime error handling
        print("Error in generate_panel_question:")
        traceback.print_exc()
        try:
            print("rag_context:", rag_context)
        except Exception:
            print("rag_context: <unavailable>")
        try:
            print("Model/raw text was:\n", locals().get("text", "<no text>"))
        except Exception:
            pass
        return None


def generate_code_structure(technical_question: str) -> Optional[str]:
    """Produce a high-level plan or pseudocode for a technical question.

    Uses gpt-4o with a system prompt that frames the model as a '10x Staff Engineer'.
    Returns the model's response (pseudocode or plan) as plain text, or None on error.
    """
    client = OpenAI()

    system_prompt = STAFF_ENGINEER_SYSTEM_PROMPT

    user_prompt = f"Technical question:\n\n{technical_question}\n\nProvide a high-level plan and pseudocode/sketch."

    try:
        resp = client.responses.create(
            model="gpt-4o",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.18,
        )

        text = _extract_text_from_response(resp)
        if not text:
            raise ValueError("Empty response from model")

        return text

    except Exception:  # pragma: no cover - runtime error handling
        print("Error in generate_code_structure:")
        traceback.print_exc()
        return None


def generate_7_day_strategy(user_id: str) -> Optional[str]:
    """Generate a 7-day improvement plan (Markdown) using the user's full personalized history.

    - Calls: db_manager.get_personalized_context(user_id, retrieve_all=True)
    - Sends the full history to gpt-4o and requests a 7-day plan formatted in Markdown.
    - Returns the Markdown string or None on error.
    """
    client = OpenAI()

    try:
        # Fetch full personalized history for the user
        full_history = db_manager.get_personalized_context(user_id, retrieve_all=True)

        system_prompt = SEVEN_DAY_STRATEGY_SYSTEM_PROMPT

        user_prompt = (
            "Here is the user's full personalized history (use this to personalize the plan):\n\n"
            f"{full_history}\n\n"
            "Generate a concise 7-day improvement plan in Markdown as described in the system prompt."
        )

        resp = client.responses.create(
            model="gpt-4o",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )

        text = _extract_text_from_response(resp)
        if not text:
            raise ValueError("Empty response from model")

        # Return returned markdown directly
        return text

    except Exception:  # pragma: no cover - runtime error handling
        print("Error in generate_7_day_strategy:")
        traceback.print_exc()
        try:
            print("full_history:", full_history)
        except Exception:
            print("full_history: <unavailable>")
        try:
            print("Model/raw text was:\n", locals().get("text", "<no text>"))
        except Exception:
            pass
        return None