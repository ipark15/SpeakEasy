import io
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable, Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)


# ── chart helpers ─────────────────────────────────────────────────────────────

def _score_color(val: int) -> str:
    if val >= 70:
        return "#4CAF50"
    if val >= 50:
        return "#FFC107"
    return "#F44336"


def _bar_chart(scores: dict) -> bytes:
    cats = ["Fluency", "Clarity", "Rhythm", "Prosody", "Pronunciation"]
    vals = [scores.get("fluency", 0), scores.get("clarity", 0), scores.get("rhythm", 0),
            scores.get("prosody", 0), scores.get("pronunciation", scores.get("voice_quality", 0))]
    bar_colors = [_score_color(v) for v in vals]

    fig, ax = plt.subplots(figsize=(6, 3.2))
    bars = ax.barh(cats, vals, color=bar_colors, edgecolor="white", height=0.55)
    ax.set_xlim(0, 110)
    ax.set_xlabel("Score", fontsize=9)
    ax.set_title("Score Breakdown", fontweight="bold", fontsize=11)
    ax.axvline(x=50, color="gray", linestyle="--", alpha=0.35, linewidth=0.8)
    ax.axvline(x=70, color="green", linestyle="--", alpha=0.35, linewidth=0.8)
    for bar, val in zip(bars, vals):
        ax.text(val + 1.5, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _radar_chart(scores: dict) -> bytes:
    cats = ["Fluency", "Clarity", "Rhythm", "Prosody", "Pronun-\nciation"]
    vals = [scores.get("fluency", 0), scores.get("clarity", 0), scores.get("rhythm", 0),
            scores.get("prosody", 0), scores.get("pronunciation", scores.get("voice_quality", 0))]

    N = len(cats)
    angles = [n / N * 2 * np.pi for n in range(N)]
    angles += angles[:1]
    vals_plot = vals + vals[:1]

    fig, ax = plt.subplots(figsize=(3.8, 3.8), subplot_kw=dict(polar=True))
    ax.plot(angles, vals_plot, "o-", linewidth=2, color="#2196F3")
    ax.fill(angles, vals_plot, alpha=0.2, color="#2196F3")
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(cats, fontsize=8)
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(["25", "50", "75", "100"], fontsize=6, color="gray")
    ax.set_title("Speech Profile", fontweight="bold", fontsize=11, pad=14)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ── main PDF builder ──────────────────────────────────────────────────────────

def generate_pdf(assessment: dict, narrative: dict, output_path: str) -> str:
    parent = os.path.dirname(output_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        rightMargin=0.75 * inch, leftMargin=0.75 * inch,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch,
    )

    base = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle", parent=base["Heading1"],
        fontSize=22, textColor=colors.HexColor("#1A237E"),
        alignment=TA_CENTER, spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", parent=base["Normal"],
        fontSize=10, textColor=colors.gray,
        alignment=TA_CENTER, spaceAfter=4,
    )
    section_header = ParagraphStyle(
        "SectionHeader", parent=base["Heading2"],
        fontSize=13, textColor=colors.HexColor("#1565C0"),
        spaceBefore=14, spaceAfter=6,
    )
    score_display = ParagraphStyle(
        "ScoreDisplay", parent=base["Normal"],
        fontSize=52, textColor=colors.HexColor("#1A237E"),
        alignment=TA_CENTER, spaceAfter=2,
    )
    body_style = ParagraphStyle(
        "Body", parent=base["Normal"],
        fontSize=10, leading=15, spaceAfter=4,
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer", parent=base["Normal"],
        fontSize=8, textColor=colors.gray, leading=12,
    )

    scores = assessment["scores"]
    story = []

    # ── title block ──
    story.append(Paragraph("SpeakEasy Assessment Report", title_style))
    story.append(Paragraph(
        f"Session: {assessment['session_id']}  |  User: {assessment['user_id']}",
        subtitle_style,
    ))
    story.append(HRFlowable(
        width="100%", thickness=1,
        color=colors.HexColor("#1565C0"), spaceAfter=10,
    ))

    # ── overall score ──
    story.append(Paragraph("Overall Score", section_header))
    story.append(Paragraph(f"{scores['overall']} / 100", score_display))
    story.append(Spacer(1, 0.1 * inch))

    # ── score table ──
    story.append(Paragraph("Score Breakdown", section_header))
    table_data = [["Category", "Score", "Status"]]
    for label, key in [
        ("Fluency", "fluency"), ("Clarity", "clarity"),
        ("Rhythm", "rhythm"), ("Prosody", "prosody"),
        ("Pronunciation", "pronunciation"),
    ]:
        val = scores.get(key, 0)
        status = "Good" if val >= 70 else "Fair" if val >= 50 else "Needs Work"
        table_data.append([label, str(val), status])

    score_table = Table(table_data, colWidths=[2.5 * inch, 1.2 * inch, 1.5 * inch])
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1565C0")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F5F5F5"), colors.white]),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 0.15 * inch))

    # ── charts ──
    story.append(Paragraph("Visualizations", section_header))

    bar_img = Image(io.BytesIO(_bar_chart(scores)), width=4.4 * inch, height=2.5 * inch)
    radar_img = Image(io.BytesIO(_radar_chart(scores)), width=2.9 * inch, height=2.9 * inch)
    chart_row = Table([[bar_img, radar_img]], colWidths=[4.5 * inch, 3.0 * inch])
    chart_row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(chart_row)
    story.append(Spacer(1, 0.1 * inch))

    # ── narrative sections ──
    narrative_sections = [
        ("Summary",                      "overall_summary"),
        ("Strengths",                    "strengths"),
        ("Areas for Improvement",        "weaknesses"),
        ("Specific Challenging Moments", "struggled_moments"),
        ("Improvement Suggestions",      "recommendations"),
        ("Recommended Next Focus",       "next_focus"),
    ]
    for title, key in narrative_sections:
        story.append(Paragraph(title, section_header))
        text = narrative.get(key, "").replace("\n", "<br/>")
        story.append(Paragraph(text or "—", body_style))

    # ── disclaimer ──
    story.append(Spacer(1, 0.1 * inch))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceAfter=6))
    story.append(Paragraph(
        "Disclaimer: This report is generated by SpeakEasy, an automated AI speech coaching tool, "
        "and is NOT a medical diagnosis. Please consult a licensed speech-language pathologist for "
        "clinical assessment and diagnosis.",
        disclaimer_style,
    ))

    doc.build(story)
    return output_path
