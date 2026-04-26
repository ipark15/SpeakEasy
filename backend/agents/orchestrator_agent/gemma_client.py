import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

_SECTION_TAGS = [
    ("[SUMMARY]",           "overall_summary"),
    ("[DATA_HIGHLIGHTS]",   "data_highlights"),
    ("[STRENGTHS]",         "strengths"),
    ("[WEAKNESSES]",        "weaknesses"),
    ("[STRUGGLED_MOMENTS]", "struggled_moments"),
    ("[RECOMMENDATIONS]",   "recommendations"),
    ("[NEXT_FOCUS]",        "next_focus"),
]

# Clinical benchmarks shown to Gemma so it can interpret raw numbers
_BENCHMARKS = """
CLINICAL BENCHMARKS (use these to interpret the raw numbers):
  WPM (words per minute):       normal conversational = 130–160 wpm; below 100 = slow, above 200 = rushed
  WER (word error rate):        0.00 = perfect; >0.10 = notable errors; >0.25 = significant difficulty
  DDK rate (pa-ta-ka):          normal = 5–7 syllables/sec; below 4 = motor concern
  Rhythm regularity:            1.0 = perfectly even; below 0.7 = irregular timing
  Pitch std (F0 variation):     normal conversational = 20–55 Hz; below 15 Hz = monotone; above 70 Hz = erratic
  Pause count:                  1–3 pauses per task = normal; >5 = frequent hesitation
  Max pause duration:           under 1.0s = normal; 1–2s = notable; above 2s = significant gap
  Avg word confidence:          above 0.85 = clear; 0.70–0.85 = some unclear words; below 0.70 = poor clarity
  Filler count:                 0–2 per task = fine; 3–5 = moderate; above 5 = high filler rate
  Speech rate CV:               below 0.20 = steady rate; above 0.35 = highly variable pacing
"""


def _build_prompt(assessment: dict) -> str:
    composite = assessment.get("composite_score", "N/A")
    scores_summary = assessment.get("scores_summary", {})
    tasks = assessment.get("tasks", [])

    task_lines = []
    all_pauses = []
    all_low_conf = []
    transcripts = []

    # Aggregate key metrics across tasks for cross-task analysis
    agg: dict = {}

    for t in tasks:
        tid = t.get("task_id", "unknown")
        scores = t.get("scores", {})
        metrics = t.get("metrics", {})

        label = {
            "read_sentence": "Task 1 — Read Aloud (scripted sentence)",
            "pataka":        "Task 2 — Pa-ta-ka Rhythm Test",
            "free_speech":   "Task 3 — Free Speech (unscripted)",
        }.get(tid, tid)

        score_str = "  |  ".join(f"{k}: {v}/100" for k, v in scores.items())

        # Build annotated metrics block with units and benchmarks inline
        metric_parts = []
        _METRIC_FORMAT = {
            "wpm":                 ("WPM", "normal 130–160"),
            "word_error_rate":     ("WER", "0.00=perfect, >0.10=notable"),
            "pause_count":         ("pauses", "0–3=normal, >5=frequent"),
            "max_pause_duration":  ("max pause", "sec; <1.0=normal"),
            "avg_pause_duration":  ("avg pause", "sec"),
            "filler_count":        ("fillers", "0–2=fine, >5=high"),
            "speech_rate_cv":      ("rate CV", "<0.20=steady, >0.35=variable"),
            "ddk_rate":            ("DDK rate", "syl/sec; normal 5–7"),
            "rhythm_regularity":   ("rhythm regularity", "0–1; 1.0=perfect"),
            "pitch_mean":          ("pitch mean", "Hz"),
            "pitch_std":           ("pitch variation", "Hz std; normal 20–55"),
            "avg_word_confidence": ("word confidence", "0–1; >0.85=clear"),
            "audio_duration":      ("duration", "sec"),
        }
        for k, (label_m, note) in _METRIC_FORMAT.items():
            v = metrics.get(k)
            if v is not None:
                if isinstance(v, float):
                    metric_parts.append(f"{label_m}: {v:.2f} ({note})")
                else:
                    metric_parts.append(f"{label_m}: {v} ({note})")
                agg.setdefault(k, []).append(v)

        metric_str = "\n    ".join(metric_parts) if metric_parts else "no numeric metrics"
        task_lines.append(f"{label}\n  Scores: {score_str}\n  Metrics:\n    {metric_str}")

        # Transcripts
        if metrics.get("transcript") and tid != "pataka":
            transcripts.append(f'{label}:\n  "{metrics["transcript"]}"')

        # Pauses
        if metrics.get("pause_count"):
            all_pauses.append(
                f"{tid}: {metrics['pause_count']} pause(s), longest {metrics.get('max_pause_duration', '?'):.2f}s"
                if isinstance(metrics.get("max_pause_duration"), float)
                else f"{tid}: {metrics['pause_count']} pause(s)"
            )

        # Low-confidence words with scores
        for w in metrics.get("low_confidence_words", []):
            all_low_conf.append(f"'{w['word']}' ({w['confidence']:.0%})")

    tasks_block = "\n\n".join(task_lines)
    pauses_text = "; ".join(all_pauses) or "none detected"
    low_conf_text = ", ".join(all_low_conf[:12]) or "none"
    transcript_block = "\n\n".join(transcripts) or "not available"

    dim_scores = "\n".join(
        f"  {k.capitalize():15s}: {v}/100" for k, v in scores_summary.items()
    )

    # Cross-task observations for Gemma
    cross_task = []
    if "wpm" in agg and len(agg["wpm"]) >= 2:
        wpm_vals = [f"{v:.0f}" for v in agg["wpm"]]
        cross_task.append(f"WPM across tasks: {' → '.join(wpm_vals)} (read_sentence → free_speech)")
    if "pitch_std" in agg and len(agg["pitch_std"]) >= 2:
        p_vals = [f"{v:.1f}Hz" for v in agg["pitch_std"]]
        cross_task.append(f"Pitch variation: {' → '.join(p_vals)} (scripted → unscripted)")
    if "avg_word_confidence" in agg and len(agg["avg_word_confidence"]) >= 2:
        c_vals = [f"{v:.0%}" for v in agg["avg_word_confidence"]]
        cross_task.append(f"Word confidence: {' → '.join(c_vals)} (scripted → unscripted)")
    cross_task_block = "\n  ".join(cross_task) if cross_task else "insufficient data for cross-task comparison"

    return f"""You are a skilled speech-language pathologist writing a data-driven, patient-friendly assessment report for SpeakEasy, an AI speech coaching app. Your report must be grounded in the specific numbers below — do not give generic advice. Quote actual metric values, name specific low-confidence words, and reference exact pause durations.

{_BENCHMARKS}

═══════════════════════════════════════════════
ASSESSMENT RESULTS
═══════════════════════════════════════════════

COMPOSITE SCORE: {composite} / 100

DIMENSION SCORES:
{dim_scores}

───────────────────────────────────────────────
TASK-BY-TASK BREAKDOWN
───────────────────────────────────────────────
{tasks_block}

───────────────────────────────────────────────
WHAT THE PATIENT ACTUALLY SAID
───────────────────────────────────────────────
{transcript_block}

───────────────────────────────────────────────
CROSS-TASK PATTERNS
───────────────────────────────────────────────
  {cross_task_block}

───────────────────────────────────────────────
NOTABLE EVENTS
───────────────────────────────────────────────
  Pauses:              {pauses_text}
  Low-confidence words (words Whisper struggled to recognize — likely mispronounced or unclear):
    {low_conf_text}

═══════════════════════════════════════════════
Now write the report using EXACTLY these seven section headers (keep brackets, write nothing outside them):
═══════════════════════════════════════════════

[SUMMARY]
2–3 warm, plain-English sentences. State the composite score, name the strongest and weakest dimension by score, and reference one specific observation from the transcripts or metrics (e.g. actual WPM value or a pause duration).

[DATA_HIGHLIGHTS]
A concise data table or bullet list of the 4–6 most clinically meaningful numbers from this session. For each, state: the metric name, the patient's value, the normal range, and a one-word interpretation (e.g. Normal / Slow / Strong / Irregular). Example format:
• DDK Rate: 4.2 syl/sec (normal 5–7) — Slow
• Pitch Variation: 38 Hz std (normal 20–55) — Normal
• Word Confidence: 72% (target >85%) — Below target
Focus on the numbers that best explain the dimension scores.

[STRENGTHS]
2–3 bullet points. Cite specific metric values or task scores. Name words from the transcript they pronounced well if confidence was high on them.

[WEAKNESSES]
2–3 bullet points. Be specific — reference actual metric values vs benchmarks. Mention the exact dimension score and why it's low (e.g. "WER of 0.18 on the read-aloud task indicates...").

[STRUGGLED_MOMENTS]
2–4 sentences. Name specific low-confidence words (from the list above) and explain what that likely means phonetically. Reference the longest pause with its exact duration and where it likely fell in the transcript.

[RECOMMENDATIONS]
Exactly 3 numbered, specific, actionable exercises. Each must target a specific weak metric by name. Include the exact phrase or syllable sequence to practice. Example: "1. Pa-ta-ka drill: repeat 'pa-ta-ka' 10 times at a steady beat, targeting your DDK rate of 4.2 syl/sec up toward 5–7."

[NEXT_FOCUS]
1–2 sentences. Name the single lowest-scoring dimension, state its score, and explain in plain language why improving it will have the most impact based on the data.
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
