import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

_SECTION_TAGS = [
    ("[SUMMARY]",            "overall_summary"),
    ("[STRENGTHS]",          "strengths"),
    ("[WEAKNESSES]",         "weaknesses"),
    ("[STRUGGLED_MOMENTS]",  "struggled_moments"),
    ("[RECOMMENDATIONS]",    "recommendations"),
    ("[NEXT_FOCUS]",         "next_focus"),
]


def _build_prompt(assessment: dict) -> str:
    composite = assessment.get("composite_score", "N/A")
    scores_summary = assessment.get("scores_summary", {})
    tasks = assessment.get("tasks", [])

    task_lines = []
    all_pauses = []
    all_low_conf = []
    transcripts = []

    for t in tasks:
        tid = t.get("task_id", "unknown")
        scores = t.get("scores", {})
        metrics = t.get("metrics", {})

        label = {
            "read_sentence": "Task 1 — Read Aloud",
            "pataka":        "Task 2 — Pa-ta-ka Rhythm",
            "free_speech":   "Task 3 — Free Speech",
        }.get(tid, tid)

        score_str = "  ".join(f"{k}: {v}" for k, v in scores.items())

        # Include key acoustic metrics
        metric_parts = []
        for k, v in metrics.items():
            if k in ("transcript", "low_confidence_words", "pauses"):
                continue
            metric_parts.append(f"{k}: {v}")
        metric_str = "  ".join(metric_parts)

        task_lines.append(f"{label}\n  Scores: {score_str}\n  Metrics: {metric_str}")

        # Collect transcripts for qualitative analysis
        if metrics.get("transcript") and tid != "pataka":
            transcripts.append(f"{label}: \"{metrics['transcript']}\"")

        # Collect pause events
        if metrics.get("pause_count"):
            all_pauses.append(
                f"{tid}: {metrics['pause_count']} pause(s), longest {metrics.get('max_pause_duration', '?')}s"
            )

        # Collect low-confidence words
        for w in metrics.get("low_confidence_words", []):
            all_low_conf.append(f"'{w['word']}' ({w['confidence']:.0%})")

    tasks_block = "\n\n".join(task_lines)
    pauses_text = "; ".join(all_pauses) or "none detected"
    low_conf_text = ", ".join(all_low_conf[:10]) or "none"
    transcript_block = "\n".join(transcripts) or "not available"

    dim_scores = "\n".join(
        f"  {k.capitalize()}: {v}" for k, v in scores_summary.items()
    )

    return f"""You are a warm, encouraging speech-language pathologist assistant writing a patient-friendly assessment report for SpeakEasy, an AI speech coaching app.

COMPOSITE SCORE: {composite} / 100

DIMENSION SCORES (0–100, higher is better):
{dim_scores}

TASK BREAKDOWN:
{tasks_block}

WHAT THE PATIENT ACTUALLY SAID:
{transcript_block}

NOTABLE EVENTS:
  Pauses detected:      {pauses_text}
  Low-confidence words: {low_conf_text}

Using the transcripts and acoustic data above, write a report using EXACTLY these six section headers (keep the brackets):

[SUMMARY]
2–3 warm, plain-English sentences summarising the overall result. Reference the composite score and 1-2 specific observations from the transcripts or metrics.

[STRENGTHS]
2–3 bullet points describing what the speaker does well. Reference specific scores, tasks, or words they pronounced clearly.

[WEAKNESSES]
2–3 bullet points describing areas for improvement in plain language. Be specific — mention actual words, pauses, or metrics where possible.

[STRUGGLED_MOMENTS]
1–3 sentences describing specific moments that were difficult. Reference low-confidence words by name and any long pauses with their timing.

[RECOMMENDATIONS]
Exactly 3 numbered, specific and actionable practice recommendations targeting the weakest dimensions. Suggest real exercises (e.g. "practice the th- sound in 'these' and 'things'").

[NEXT_FOCUS]
1–2 sentences naming the single most important area to work on first and why, based on the scores and what was heard in the transcripts.
"""


def _parse_sections(text: str) -> dict:
    sections = {key: "" for _, key in _SECTION_TAGS}
    tags = [tag for tag, _ in _SECTION_TAGS]

    for i, (tag, key) in enumerate(_SECTION_TAGS):
        start = text.find(tag)
        if start == -1:
            continue
        start += len(tag)
        end = len(text)
        for next_tag in tags[i + 1:]:
            pos = text.find(next_tag, start)
            if pos != -1:
                end = pos
                break
        sections[key] = text[start:end].strip()

    return sections


def generate_narrative(assessment: dict) -> dict:
    prompt = _build_prompt(assessment)
    response = client.models.generate_content(
        model="gemma-4-31b-it",
        contents=prompt,
    )
    return _parse_sections(response.text)
