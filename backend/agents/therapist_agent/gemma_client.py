import os
from dotenv import load_dotenv

load_dotenv()


def _build_meta_prompt(assessment: dict, history: dict) -> str:
    composite = assessment.get("composite_score", "N/A")
    scores = assessment.get("scores_summary", {})
    sessions = history.get("sessions", [])
    best_score = history.get("best_score", "N/A")
    improvement = history.get("improvement", 0)

    # Identify weakest dimensions from current assessment
    dim_lines = "\n".join(
        f"  {k.capitalize()}: {v}/100" for k, v in scores.items()
    ) if scores else "  No dimension scores available"

    # Summarize history
    if sessions:
        recent = sessions[:5]
        history_lines = "\n".join(
            f"  {s.get('created_at', 'Unknown date')}: overall {s.get('overall_score', '?')}, "
            f"fluency {s.get('fluency', '?')}, clarity {s.get('clarity', '?')}, "
            f"rhythm {s.get('rhythm', '?')}, prosody {s.get('prosody', '?')}"
            for s in recent
        )
        history_block = f"Recent sessions (newest first):\n{history_lines}\nBest score: {best_score}, improvement over history: {improvement:+} points"
    else:
        history_block = "No previous sessions — this is the user's first assessment."

    # Identify weakest areas
    if scores:
        sorted_dims = sorted(scores.items(), key=lambda x: x[1] if x[1] is not None else 100)
        weakest = [f"{k} ({v}/100)" for k, v in sorted_dims[:2] if v is not None]
        weakest_str = " and ".join(weakest) if weakest else "no clear weak areas yet"
    else:
        weakest_str = "unknown areas"

    return f"""You are an expert speech-language pathologist. Your task is to write a system prompt that will configure a conversational AI therapist named Alex.

The user you are writing this prompt for has just completed a speech assessment. Here is their data:

CURRENT ASSESSMENT
Composite score: {composite}/100
Dimension scores:
{dim_lines}

HISTORY
{history_block}

WEAKEST AREAS (what to focus on): {weakest_str}

Write a system prompt for Alex that:
1. Establishes Alex as a warm, calm, empathetic speech therapist — conversational, never clinical or robotic
2. Embeds the user's specific scores and weak areas so Alex can reference them naturally in conversation
3. Instructs Alex to RESPOND to what the user says rather than lecturing — ask open questions, follow up on what they share
4. Instructs Alex to recommend targeted exercises for the weakest dimensions when appropriate (see EXERCISE PLACEHOLDER below)
5. Instructs Alex to NEVER read out numerical scores directly — instead say things like "you're doing really well with your rhythm" or "let's work a bit more on your clarity"
6. Keeps responses concise since this is a real-time voice conversation (no long paragraphs)
7. Instructs Alex to start with a warm, brief greeting that acknowledges the user just completed an assessment

EXERCISE PLACEHOLDER: For now, use general evidence-based speech therapy exercises such as:
- For fluency: slow reading practice, easy onset techniques, "stretched speech" on longer words
- For clarity: minimal pairs practice, over-articulation drills on tongue twisters
- For rhythm: metronome-paced speech (tapping along to a beat), pa-ta-ka repetitions
- For prosody: reading aloud with exaggerated intonation, sentence stress exercises
- For pronunciation: tongue twisters, word repetition focusing on specific phonemes

Output ONLY the system prompt text — nothing else, no explanation, no meta-commentary. Start directly with Alex's persona definition.
"""


def build_system_prompt(assessment: dict, history: dict) -> str:
    meta_prompt = _build_meta_prompt(assessment, history)
    try:
        from google import genai
        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        response = client.models.generate_content(
            model="gemma-4-31b-it",
            contents=meta_prompt,
        )
        return response.text.strip()
    except Exception as e:
        # Fallback to a generic but functional system prompt
        scores = assessment.get("scores_summary", {})
        if scores:
            sorted_dims = sorted(scores.items(), key=lambda x: x[1] if x[1] is not None else 100)
            weakest = [k for k, v in sorted_dims[:2] if v is not None]
            focus = " and ".join(weakest) if weakest else "overall speech quality"
        else:
            focus = "overall speech quality"

        return (
            f"You are Alex, a warm and supportive speech therapist. "
            f"The user has just completed a speech assessment. Their main areas to work on are {focus}. "
            f"Start by warmly welcoming them and asking how they found the assessment. "
            f"Respond naturally to what they tell you. Ask follow-up questions. "
            f"When appropriate, recommend specific exercises for their weak areas — "
            f"for example, slow reading practice for fluency, tongue twisters for clarity, "
            f"or pa-ta-ka repetitions for rhythm. "
            f"Never read out numerical scores. Keep responses brief and conversational."
        )
