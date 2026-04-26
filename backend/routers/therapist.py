from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.agents.therapist_agent.prompt_builder import build_system_prompt, build_first_message

router = APIRouter()


class TherapistPromptRequest(BaseModel):
    current_assessment: dict   # payload from _build_assessment_payload()
    history: dict              # payload from progress_tracker _fetch_history()


class TherapistPromptResponse(BaseModel):
    system_prompt: str
    first_message: str


@router.post("/therapist/prompt", response_model=TherapistPromptResponse)
def get_therapist_prompt(body: TherapistPromptRequest):
    """
    Returns the ElevenLabs system prompt and opening line for Maya.
    Call this after assessment completes + progress_tracker has run.

    Your teammate can pass system_prompt as the ElevenLabs agent system prompt
    and first_message as the agent's first utterance.
    """
    if not body.current_assessment:
        raise HTTPException(status_code=400, detail="current_assessment is required")

    system_prompt = build_system_prompt(body.current_assessment, body.history)
    first_message = build_first_message(body.current_assessment)

    return TherapistPromptResponse(
        system_prompt=system_prompt,
        first_message=first_message,
    )
