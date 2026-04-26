import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

_SECTION_TAGS = [
    ("[SUMMARY]",           "overall_summary"),
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
FORMATTING RULES (strictly follow these):
═══════════════════════════════════════════════
The output will be rendered in a PDF that supports a small subset of HTML tags inside paragraphs.
You MUST use these tags — plain text walls are not acceptable:

  <b>text</b>              — bold any metric value, score, or key term
  <font color="#E53935">text</font>   — red: flag problem areas, scores below 50, "needs work"
  <font color="#FB8C00">text</font>   — orange: caution, scores 50–69, "borderline"
  <font color="#43A047">text</font>   — green: good results, scores ≥ 70, "on track"
  • (bullet)               — start each list item with a bullet character

Do NOT use markdown (no **, no ##, no ```). Only the HTML tags above.

═══════════════════════════════════════════════
Now write the report using EXACTLY these six section headers (keep brackets, write nothing outside them):
═══════════════════════════════════════════════

[SUMMARY]
2–3 sentences. Bold the composite score. Color the strongest dimension <font color="#43A047">green</font> and the weakest <font color="#E53935">red</font>. End with one specific observation from the data (e.g. actual WPM, a pause duration, or a low-confidence word).

[STRENGTHS]
2–3 bullet points (• ). Bold every metric value. Color values that beat the benchmark <font color="#43A047">green</font>. Be specific — cite task scores and words they said clearly.

[WEAKNESSES]
2–3 bullet points (• ). Bold every metric value. Color values below benchmark <font color="#E53935">red</font> if severe, <font color="#FB8C00">orange</font> if borderline. State the gap vs the normal range (e.g. "<b>WER 0.22</b> vs normal <0.10").

[STRUGGLED_MOMENTS]
2–4 sentences. Wrap each low-confidence word in <font color="#E53935"><b>word</b></font>. Bold the longest pause duration. Explain in plain language what the pattern suggests (e.g. difficulty with consonant clusters, word-finding hesitation).

[RECOMMENDATIONS]
Exactly 3 bullet points (• ). Bold the target metric and the drill phrase. Color the target range <font color="#43A047">green</font>. Each must name the specific weak metric value and what to aim for.

[NEXT_FOCUS]
1–2 sentences. Bold the dimension name and its score. Color it <font color="#E53935">red</font>. One plain-language reason why it matters most.
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


def _build_data_highlights(assessment: dict) -> str:
    """
    Build a color-coded HTML bullet list of key metrics for the PDF.
    Entirely Python — no LLM needed, always renders cleanly.
    """
    tasks = assessment.get("tasks", [])
    rows = []

    def _status(val, good, warn):
        """Return (color, label) based on thresholds. good/warn are (lo, hi) ranges or None."""
        if good is None:
            return "#757575", "N/A"
        lo_g, hi_g = good
        lo_w, hi_w = warn
        in_good = (lo_g is None or val >= lo_g) and (hi_g is None or val <= hi_g)
        in_warn = (lo_w is None or val >= lo_w) and (hi_w is None or val <= hi_w)
        if in_good:
            return "#43A047", "Good"
        if in_warn:
            return "#FB8C00", "Fair"
        return "#E53935", "Low"

    def row(label, val_str, range_str, color, status):
        return (
            f'• <b>{label}:</b> <font color="{color}"><b>{val_str}</b></font> '
            f'<font color="#757575">(normal: {range_str})</font> '
            f'— <font color="{color}"><b>{status}</b></font>'
        )

    for t in tasks:
        tid = t.get("task_id")
        m = t.get("metrics", {})

        if tid == "read_sentence":
            if m.get("wpm") is not None:
                c, s = _status(m["wpm"], (110, 175), (85, 210))
                rows.append(row("Speaking Rate (read)", f"{m['wpm']:.0f} wpm", "130–160 wpm", c, s))
            if m.get("word_error_rate") is not None:
                wer = m["word_error_rate"]
                c = "#43A047" if wer <= 0.05 else "#FB8C00" if wer <= 0.15 else "#E53935"
                s = "Excellent" if wer <= 0.05 else "Fair" if wer <= 0.15 else "Needs Work"
                rows.append(row("Word Error Rate", f"{wer:.0%}", "<10% errors", c, s))
            if m.get("avg_word_confidence") is not None:
                c, s = _status(m["avg_word_confidence"], (0.85, None), (0.70, None))
                rows.append(row("Pronunciation Clarity (read)", f"{m['avg_word_confidence']:.0%}", ">85%", c, s))

        elif tid == "pataka":
            if m.get("ddk_rate") is not None:
                c, s = _status(m["ddk_rate"], (5.0, 7.5), (4.0, 9.0))
                rows.append(row("DDK Rate (pa-ta-ka)", f"{m['ddk_rate']:.1f} syl/sec", "5–7 syl/sec", c, s))
            if m.get("rhythm_regularity") is not None:
                c, s = _status(m["rhythm_regularity"], (0.75, None), (0.55, None))
                rows.append(row("Rhythm Regularity", f"{m['rhythm_regularity']:.2f}", ">0.75", c, s))

        elif tid == "free_speech":
            if m.get("wpm") is not None:
                c, s = _status(m["wpm"], (110, 175), (85, 210))
                rows.append(row("Speaking Rate (free)", f"{m['wpm']:.0f} wpm", "130–160 wpm", c, s))
            if m.get("filler_count") is not None:
                fc = m["filler_count"]
                c = "#43A047" if fc <= 2 else "#FB8C00" if fc <= 5 else "#E53935"
                s = "Good" if fc <= 2 else "Fair" if fc <= 5 else "High"
                rows.append(row("Filler Words", str(fc), "0–2 per task", c, s))
            if m.get("pitch_std") is not None:
                c, s = _status(m["pitch_std"], (20, 55), (12, 70))
                rows.append(row("Pitch Variation", f"{m['pitch_std']:.1f} Hz", "20–55 Hz", c, s))
            if m.get("avg_word_confidence") is not None:
                c, s = _status(m["avg_word_confidence"], (0.85, None), (0.70, None))
                rows.append(row("Pronunciation Clarity (free)", f"{m['avg_word_confidence']:.0%}", ">85%", c, s))
            if m.get("pause_count") is not None:
                pc = m["pause_count"]
                c = "#43A047" if pc <= 3 else "#FB8C00" if pc <= 6 else "#E53935"
                s = "Normal" if pc <= 3 else "Frequent" if pc <= 6 else "Very frequent"
                max_p = m.get("max_pause_duration")
                val_str = f"{pc} pauses" + (f", longest {max_p:.1f}s" if max_p else "")
                rows.append(row("Hesitation Pauses", val_str, "0–3 pauses", c, s))

    return "<br/>".join(rows) if rows else "No detailed metrics available."


def generate_narrative(assessment: dict) -> dict:
    prompt = _build_prompt(assessment)
    response = client.models.generate_content(
        model="gemma-4-31b-it",
        contents=prompt,
    )
    result = _parse_sections(response.text)
    result["data_highlights"] = _build_data_highlights(assessment)
    return result
