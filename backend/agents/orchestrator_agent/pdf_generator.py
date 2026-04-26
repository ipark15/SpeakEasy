import io
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable, Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

# ── palette ───────────────────────────────────────────────────────────────────
C_NAVY   = "#1A237E"
C_BLUE   = "#1565C0"
C_GREEN  = "#43A047"
C_ORANGE = "#FB8C00"
C_RED    = "#E53935"
C_GREY   = "#757575"
C_BG     = "#F8F9FA"
C_WHITE  = "#FFFFFF"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
})


# ── helpers ───────────────────────────────────────────────────────────────────

def _score_color(val: float) -> str:
    if val >= 70: return C_GREEN
    if val >= 50: return C_ORANGE
    return C_RED


def _conf_color(conf: float) -> str:
    if conf >= 0.85: return C_GREEN
    if conf >= 0.65: return C_ORANGE
    return C_RED


# ── chart: score bar ──────────────────────────────────────────────────────────

def _bar_chart(scores: dict) -> bytes:
    cats = ["Fluency", "Clarity", "Rhythm", "Prosody", "Pronunciation"]
    vals = [
        scores.get("fluency", 0), scores.get("clarity", 0), scores.get("rhythm", 0),
        scores.get("prosody", 0), scores.get("pronunciation", scores.get("voice_quality", 0)),
    ]
    bar_colors = [_score_color(v) for v in vals]

    fig, ax = plt.subplots(figsize=(5.8, 3.0))
    fig.patch.set_facecolor("white")
    bars = ax.barh(cats, vals, color=bar_colors, edgecolor="white", height=0.5)
    ax.set_xlim(0, 115)
    ax.set_xlabel("Score / 100", fontsize=8, color=C_GREY)
    ax.set_title("Score Breakdown", fontweight="bold", fontsize=11, color=C_NAVY, pad=10)
    ax.axvline(x=70, color=C_GREEN, linestyle="--", alpha=0.4, linewidth=0.9)
    ax.tick_params(labelsize=9)
    for bar, val in zip(bars, vals):
        ax.text(val + 1.5, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", fontsize=9, color=C_NAVY, fontweight="bold")
    plt.tight_layout(pad=0.5)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ── chart: radar ──────────────────────────────────────────────────────────────

def _radar_chart(scores: dict) -> bytes:
    cats = ["Fluency", "Clarity", "Rhythm", "Prosody", "Pronunciation"]
    vals = [
        scores.get("fluency", 0), scores.get("clarity", 0), scores.get("rhythm", 0),
        scores.get("prosody", 0), scores.get("pronunciation", scores.get("voice_quality", 0)),
    ]
    N = len(cats)
    angles = [n / N * 2 * np.pi for n in range(N)] + [0]
    vals_plot = vals + vals[:1]

    fig, ax = plt.subplots(figsize=(3.5, 3.5), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor("white")
    ax.plot(angles, vals_plot, "o-", linewidth=2, color=C_BLUE)
    ax.fill(angles, vals_plot, alpha=0.15, color=C_BLUE)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(cats, fontsize=8)
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(["25", "50", "75", "100"], fontsize=6, color=C_GREY)
    ax.set_title("Speech Profile", fontweight="bold", fontsize=10, color=C_NAVY, pad=14)
    plt.tight_layout(pad=0.5)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ── chart: range marker ───────────────────────────────────────────────────────

_RANGE_SPECS = [
    # (metric_key, label, x_min, x_max, good_lo, good_hi, unit)
    ("wpm",               "Speaking Rate",    40,  260, 130, 160, "wpm"),
    ("ddk_rate",          "DDK Rate",          1,   10,   5,   7, "syl/sec"),
    ("pitch_std",         "Pitch Variation",   0,   90,  20,  55, "Hz"),
    ("avg_word_confidence","Word Confidence",  0.3, 1.0, 0.85, 1.0, ""),
    ("word_error_rate",   "Word Error Rate",   0,  0.5,  0,  0.10, ""),
]


def _range_marker_chart(tasks: list) -> bytes | None:
    # Collect one value per metric (prefer free_speech > read_sentence > pataka)
    priority = {"free_speech": 0, "read_sentence": 1, "pataka": 2}
    metric_vals: dict[str, float] = {}
    for t in sorted(tasks, key=lambda t: priority.get(t.get("task_id", ""), 9)):
        m = t.get("metrics", {})
        for key, *_ in _RANGE_SPECS:
            if key not in metric_vals and m.get(key) is not None:
                metric_vals[key] = float(m[key])

    rows = [(label, metric_vals[key], xmin, xmax, glo, ghi, unit)
            for key, label, xmin, xmax, glo, ghi, unit in _RANGE_SPECS
            if key in metric_vals]
    if not rows:
        return None

    n = len(rows)
    fig, axes = plt.subplots(n, 1, figsize=(6.0, n * 0.95 + 0.4))
    fig.patch.set_facecolor("white")
    if n == 1:
        axes = [axes]

    for ax, (label, val, xmin, xmax, glo, ghi, unit) in zip(axes, rows):
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(-0.5, 0.5)
        ax.axis("off")

        span = xmax - xmin

        # background track
        track = mpatches.FancyBboxPatch(
            (xmin, -0.18), span, 0.36,
            boxstyle="round,pad=0.01", linewidth=0,
            facecolor="#EEEEEE", zorder=1,
        )
        ax.add_patch(track)

        # good range band
        good_w = ghi - glo
        good = mpatches.FancyBboxPatch(
            (glo, -0.18), good_w, 0.36,
            boxstyle="round,pad=0.01", linewidth=0,
            facecolor="#C8E6C9", zorder=2,
        )
        ax.add_patch(good)

        # "Normal" label above band
        ax.text((glo + ghi) / 2, 0.30, "Normal range",
                ha="center", va="bottom", fontsize=6.5, color=C_GREEN, zorder=5)

        # user dot
        dot_color = C_GREEN if glo <= val <= ghi else (C_ORANGE if abs(val - glo) < span * 0.2 or abs(val - ghi) < span * 0.2 else C_RED)
        ax.plot(val, 0, "o", markersize=11, color=dot_color, zorder=6, markeredgecolor="white", markeredgewidth=1.5)

        # value label below dot
        val_str = f"{val:.0%}" if unit == "" and "confidence" in label.lower() else \
                  f"{val:.0%}" if unit == "" and "error" in label.lower() else \
                  f"{val:.1f}" if isinstance(val, float) and val < 10 else f"{val:.0f}"
        if unit:
            val_str += f" {unit}"
        ax.text(val, -0.33, val_str, ha="center", va="top", fontsize=7.5,
                color=dot_color, fontweight="bold", zorder=6)

        # left label
        ax.text(xmin - span * 0.01, 0, label, ha="right", va="center",
                fontsize=8.5, color=C_NAVY, fontweight="bold")

        # range tick labels
        ax.text(glo, -0.46, f"{glo:.0f}" if ghi > 5 else f"{glo:.2f}",
                ha="center", va="top", fontsize=6, color=C_GREY)
        ax.text(ghi, -0.46, f"{ghi:.0f}" if ghi > 5 else f"{ghi:.2f}",
                ha="center", va="top", fontsize=6, color=C_GREY)

    fig.suptitle("Where You Land vs. Normal Ranges", fontsize=10,
                 fontweight="bold", color=C_NAVY, y=1.01)
    plt.tight_layout(pad=0.3, h_pad=1.2)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ── transcript with confidence highlights ─────────────────────────────────────

def _transcript_paragraph(task: dict, style) -> list:
    """Return flowables: task label + word-colored transcript.

    Colors words by per-word confidence from low_confidence_words list.
    Falls back to relative coloring: bottom 25% of words by confidence
    get orange/red, so there's always visible variation even in clean sessions.
    """
    tid = task.get("task_id", "")
    if tid == "pataka":
        return []
    metrics = task.get("metrics", {})
    transcript = metrics.get("transcript", "").strip()
    if not transcript:
        return []

    label_map = {"read_sentence": "Read Aloud", "free_speech": "Free Speech"}
    label = label_map.get(tid, tid)

    # Best source: word_timestamps has per-word confidence for every word
    wt = metrics.get("word_timestamps", [])
    avg_conf = metrics.get("avg_word_confidence", 1.0)

    if wt:
        # Map in order — zip with transcript words to preserve punctuation
        wt_confs = [float(w.get("confidence", avg_conf)) for w in wt]
        transcript_words = [w.get("word", "") for w in wt]
        # Rebuild transcript from timestamps to ensure alignment
        words = transcript_words
        word_confs = wt_confs
    else:
        # Fallback: explicit low-confidence list + avg for the rest
        explicit = {w["word"].lower().strip(".,!?'\""): w["confidence"]
                    for w in metrics.get("low_confidence_words", [])}
        words = transcript.split()
        word_confs = [explicit.get(w.lower().strip(".,!?'\""), avg_conf) for w in words]

    # Always use absolute thresholds — word_timestamps gives real per-word scores
    def _abs_color(c: float) -> str:
        if c >= 0.85: return C_GREEN
        if c >= 0.65: return C_ORANGE
        return C_RED

    parts = []
    for word, conf in zip(words, word_confs):
        c = _abs_color(conf)
        if c == C_GREEN:
            parts.append(word)
        else:
            parts.append(f'<font color="{c}"><b>{word}</b></font>')

    colored_text = " ".join(parts)
    legend = (
        f'<font color="{C_GREY}" size="8">  '
        f'<font color="{C_GREEN}">■</font> Clear  '
        f'<font color="{C_ORANGE}">■</font> Less certain  '
        f'<font color="{C_RED}">■</font> Low confidence</font>'
    )

    return [
        Paragraph(f'<b>{label}</b>', style),
        Paragraph(colored_text + legend, style),
        Spacer(1, 0.08 * inch),
    ]


# ── styles factory ────────────────────────────────────────────────────────────

def _make_styles():
    def S(name, **kw):
        defaults = dict(fontName="Helvetica", fontSize=10, leading=15)
        defaults.update(kw)
        return ParagraphStyle(name, **defaults)

    title   = S("Title",    fontName="Helvetica-Bold", fontSize=22,
                textColor=colors.HexColor(C_NAVY), alignment=TA_CENTER, spaceAfter=2, spaceBefore=0)
    sub     = S("Sub",      fontSize=9, textColor=colors.HexColor(C_GREY),
                alignment=TA_CENTER, spaceAfter=8, spaceBefore=2)
    heading = S("Heading",  fontName="Helvetica-Bold", fontSize=12,
                textColor=colors.HexColor(C_BLUE), spaceBefore=14, spaceAfter=5)
    score   = S("Score",    fontName="Helvetica-Bold", fontSize=36,
                textColor=colors.HexColor(C_NAVY), alignment=TA_CENTER, spaceAfter=2)
    body    = S("Body",     fontSize=10, leading=16, spaceAfter=4)
    hi      = S("Hi",       fontSize=10, leading=18, spaceAfter=4,
                leftIndent=10, rightIndent=10,
                backColor=colors.HexColor(C_BG), borderPadding=(8, 8, 8, 8))
    tx      = S("Tx",       fontSize=10, leading=17, spaceAfter=2,
                leftIndent=10, rightIndent=10,
                backColor=colors.HexColor("#FFFDE7"), borderPadding=(6, 6, 6, 6))
    disc    = S("Disc",     fontSize=7.5, textColor=colors.HexColor(C_GREY), leading=11)

    return title, sub, heading, score, body, hi, tx, disc


# ── main builder ──────────────────────────────────────────────────────────────

def generate_pdf(assessment: dict, narrative: dict, output_path: str) -> str:
    parent = os.path.dirname(output_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        rightMargin=0.75 * inch, leftMargin=0.75 * inch,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch,
    )

    title_s, sub_s, heading_s, score_s, body_s, hi_s, tx_s, disc_s = _make_styles()

    scores = assessment["scores"]
    tasks  = assessment.get("tasks", [])
    story  = []

    # ── header ──
    story.append(Paragraph("SpeakEasy Assessment Report", title_s))
    story.append(Paragraph(
        f"Session: {assessment['session_id']}  ·  User: {assessment['user_id']}",
        sub_s,
    ))
    story.append(HRFlowable(width="100%", thickness=1.5,
                             color=colors.HexColor(C_BLUE), spaceAfter=12))

    # ── composite score ──
    story.append(Paragraph("Overall Score", heading_s))
    story.append(Paragraph(f"{scores['overall']} / 100", score_s))
    story.append(Spacer(1, 0.08 * inch))

    # ── score table ──
    story.append(Paragraph("Score Breakdown", heading_s))
    table_data = [["Category", "Score", "Status"]]
    for label, key in [("Fluency","fluency"), ("Clarity","clarity"),
                        ("Rhythm","rhythm"),   ("Prosody","prosody"),
                        ("Pronunciation","pronunciation")]:
        val = scores.get(key, 0)
        status = "Good" if val >= 70 else "Fair" if val >= 50 else "Needs Work"
        status_color = C_GREEN if val >= 70 else C_ORANGE if val >= 50 else C_RED
        table_data.append([
            label, str(val),
            Paragraph(f'<font color="{status_color}"><b>{status}</b></font>', body_s),
        ])

    score_table = Table(table_data, colWidths=[2.5*inch, 1.2*inch, 1.5*inch])
    score_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), colors.HexColor(C_BLUE)),
        ("TEXTCOLOR",     (0,0), (-1,0), colors.white),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,0), 10),
        ("FONTNAME",      (0,1), (-1,-1), "Helvetica"),
        ("FONTSIZE",      (0,1), (-1,-1), 10),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.HexColor("#F5F5F5"), colors.white]),
        ("ALIGN",         (1,0), (-1,-1), "CENTER"),
        ("GRID",          (0,0), (-1,-1), 0.4, colors.HexColor("#E0E0E0")),
        ("TOPPADDING",    (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("ROUNDEDCORNERS",(0,0), (-1,-1), 3),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 0.18 * inch))

    # ── charts row: bar + radar ──
    story.append(Paragraph("Visualizations", heading_s))
    bar_img   = Image(io.BytesIO(_bar_chart(scores)),   width=4.2*inch, height=2.4*inch)
    radar_img = Image(io.BytesIO(_radar_chart(scores)), width=2.8*inch, height=2.8*inch)
    chart_row = Table([[bar_img, radar_img]], colWidths=[4.3*inch, 3.0*inch])
    chart_row.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN",  (0,0), (-1,-1), "CENTER"),
    ]))
    story.append(chart_row)
    story.append(Spacer(1, 0.1 * inch))

    # ── range marker chart ──
    range_bytes = _range_marker_chart(tasks)
    if range_bytes:
        n_metrics = sum(1 for key, *_ in _RANGE_SPECS
                        if any(t.get("metrics", {}).get(key) is not None for t in tasks))
        img_h = max(1.8, n_metrics * 1.0)
        story.append(Image(io.BytesIO(range_bytes), width=6.5*inch, height=img_h*inch))
        story.append(Spacer(1, 0.1 * inch))
    else:
        import logging
        logging.getLogger(__name__).warning("range_marker_chart returned None — no matching metrics found in tasks")

    # ── transcript with confidence coloring ──
    story.append(Paragraph("What You Said", heading_s))
    story.append(Paragraph(
        f'<font color="{C_GREY}" size="9">Words are color-coded by recognition confidence. '
        f'<font color="{C_RED}"><b>Red</b></font> words were harder for the system to recognize '
        f'— these often indicate pronunciation areas to work on.</font>',
        body_s,
    ))
    for t in tasks:
        story.extend(_transcript_paragraph(t, tx_s))

    # ── narrative sections (no struggled_moments) ──
    story.append(Paragraph("Summary", heading_s))
    story.append(Paragraph(
        (narrative.get("overall_summary") or "—").replace("\n", "<br/>"), body_s))

    story.append(Paragraph("Key Metrics at a Glance", heading_s))
    story.append(Paragraph(
        (narrative.get("data_highlights") or "—").replace("\n", "<br/>"), hi_s))

    story.append(Paragraph("Strengths", heading_s))
    story.append(Paragraph(
        (narrative.get("strengths") or "—").replace("\n", "<br/>"), body_s))

    story.append(Paragraph("Areas for Improvement", heading_s))
    story.append(Paragraph(
        (narrative.get("weaknesses") or "—").replace("\n", "<br/>"), body_s))

    story.append(Paragraph("Improvement Exercises", heading_s))
    story.append(Paragraph(
        (narrative.get("recommendations") or "—").replace("\n", "<br/>"), body_s))

    story.append(Paragraph("Next Focus", heading_s))
    story.append(Paragraph(
        (narrative.get("next_focus") or "—").replace("\n", "<br/>"), body_s))

    # ── disclaimer ──
    story.append(Spacer(1, 0.12 * inch))
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=colors.HexColor("#E0E0E0"), spaceAfter=6))
    story.append(Paragraph(
        "This report is generated by SpeakEasy, an AI speech coaching tool, and is NOT a medical "
        "diagnosis. Please consult a licensed speech-language pathologist for clinical assessment.",
        disc_s,
    ))

    doc.build(story)
    return output_path
