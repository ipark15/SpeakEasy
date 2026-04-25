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
    s = assessment["scores"]
    f = assessment["features"]
    e = assessment["events"]

    pauses_text = ", ".join(
        f"{p['duration']}s after '{p['after_word']}' at {p['start']}s"
        for p in e.get("pauses", [])
    ) or "none"

    low_conf_text = ", ".join(
        f"'{w['word']}' at {w['time']}s (confidence {w['confidence']:.0%})"
        for w in e.get("low_confidence_words", [])
    ) or "none"

    return f"""You are a friendly speech-language pathologist assistant writing a patient-friendly assessment report.

SCORES (0–100, higher is better):
  Overall:       {s['overall']}
  Fluency:       {s['fluency']}
  Clarity:       {s['clarity']}
  Rhythm:        {s['rhythm']}
  Prosody:       {s['prosody']}
  Voice Quality: {s['voice_quality']}

SPEECH FEATURES:
  Word Error Rate:     {f['word_error_rate']} (lower is better; 0 = perfect)
  DDK Rate:            {f['ddk_rate']} syllables/sec (typical: 5–7)
  Rhythm Regularity:   {f['rhythm_regularity']} (1.0 = perfectly regular)
  Speaking Rate:       {f['wpm']} words/min (typical: 120–180)
  Pitch Variation:     {f['pitch_std']} Hz std dev
  Jitter:              {f['jitter']}% (normal <1%)
  Shimmer:             {f['shimmer']}% (normal <3%)
  HNR:                 {f['hnr']} dB (higher is better; normal >20 dB)

NOTABLE EVENTS:
  Pauses:               {pauses_text}
  Low-confidence words: {low_conf_text}

Write a report using EXACTLY these six section headers (keep the brackets):

[SUMMARY]
2–3 warm, plain-English sentences summarising the overall result.

[STRENGTHS]
2–3 bullet points describing what the speaker does well, referencing specific scores/features.

[WEAKNESSES]
2–3 bullet points describing areas for improvement in plain language a patient can understand.

[STRUGGLED_MOMENTS]
1–3 sentences describing specific moments that were difficult, referencing the pauses and low-confidence words by time/word.

[RECOMMENDATIONS]
Exactly 3 numbered practice recommendations that are specific and actionable.

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
