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

    # Build per-task sections
    task_lines = []
    all_pauses = []
    all_low_conf = []

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
        metric_str = "  ".join(
            f"{k}: {v}" for k, v in metrics.items()
            if k not in ("transcript", "low_confidence_words")
        )
        task_lines.append(f"{label}\n  Scores: {score_str}\n  Metrics: {metric_str}")

        if metrics.get("pause_count"):
            all_pauses.append(
                f"{tid}: {metrics['pause_count']} pause(s), longest {metrics.get('max_pause_duration', '?')}s"
            )
        for w in metrics.get("low_confidence_words", []):
            all_low_conf.append(f"'{w['word']}' ({w['confidence']:.0%})")

    tasks_block = "\n\n".join(task_lines)
    pauses_text = "; ".join(all_pauses) or "none"
    low_conf_text = ", ".join(all_low_conf) or "none"

    dim_scores = "\n".join(
        f"  {k.capitalize()}: {v}" for k, v in scores_summary.items()
    )

    return f"""You are a friendly speech-language pathologist assistant writing a patient-friendly assessment report.

COMPOSITE SCORE: {composite} / 100

DIMENSION AVERAGES (0–100, higher is better):
{dim_scores}

TASK BREAKDOWN:
{tasks_block}

NOTABLE EVENTS:
  Pauses:               {pauses_text}
  Low-confidence words: {low_conf_text}

Write a report using EXACTLY these six section headers (keep the brackets):

[SUMMARY]
2–3 warm, plain-English sentences summarising the overall result across all 3 tasks.

[STRENGTHS]
2–3 bullet points describing what the speaker does well, referencing specific scores or tasks.

[WEAKNESSES]
2–3 bullet points describing areas for improvement in plain language a patient can understand.

[STRUGGLED_MOMENTS]
1–3 sentences describing specific moments that were difficult, referencing pauses and low-confidence words.

[RECOMMENDATIONS]
Exactly 3 numbered practice recommendations that are specific and actionable, targeting the weakest dimensions.

[NEXT_FOCUS]
1–2 sentences naming the single most important area to work on first and why.
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
