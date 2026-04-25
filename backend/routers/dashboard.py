from __future__ import annotations
import csv
import io
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import backend.db.queries as db

router = APIRouter()


# ── Dashboard ─────────────────────────────────────────────────

@router.get("/dashboard/{user_id}")
def get_dashboard(user_id: str):
    return db.get_dashboard_data(user_id)


# ── Profile ───────────────────────────────────────────────────

class ProfileUpdate(BaseModel):
    user_id: str
    display_name: Optional[str] = None
    goals: Optional[dict] = None


@router.post("/profile")
def update_profile(body: ProfileUpdate):
    return db.upsert_profile(body.user_id, body.display_name, body.goals)


# ── CSV Export ────────────────────────────────────────────────

CSV_COLUMNS = [
    "date", "task",
    "score_overall", "score_fluency", "score_clarity", "score_rhythm",
    "score_prosody", "score_voice_quality", "score_pronunciation",
    "wpm", "word_error_rate", "ddk_rate",
    "jitter", "shimmer", "hnr", "pitch_mean", "pitch_std", "avg_word_confidence",
]


@router.get("/export/{user_id}/csv")
def export_csv(user_id: str):
    data = db.get_dashboard_data(user_id)
    if not data["assessments"]:
        raise HTTPException(status_code=404, detail="No assessments found for this user.")

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for row in data["assessments"]:
        row["date"] = row.get("created_at", "")[:10]
        writer.writerow(row)

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=speakeasy_{user_id[:8]}.csv"},
    )


# ── PDF Export ────────────────────────────────────────────────

@router.get("/export/{user_id}/pdf")
def export_pdf(user_id: str):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors

    data = db.get_dashboard_data(user_id)
    assessments = data["assessments"]
    if not assessments:
        raise HTTPException(status_code=404, detail="No assessments found for this user.")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=inch, rightMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    styles = getSampleStyleSheet()
    story = []

    name = data.get("display_name") or "Patient"
    story.append(Paragraph(f"SpeakEasy Speech Report — {name}", styles["Title"]))
    story.append(Spacer(1, 0.2 * inch))

    # ── Summary section ───────────────────────────────────────
    story.append(Paragraph("Summary", styles["Heading2"]))
    session_count = len(data["sessions"])
    streak = data["current_streak"]
    summary_text = (
        f"Total sessions completed: <b>{session_count}</b> &nbsp;&nbsp; "
        f"Current streak: <b>{streak} day{'s' if streak != 1 else ''}</b> &nbsp;&nbsp; "
        f"Longest streak: <b>{data['longest_streak']} days</b>"
    )
    story.append(Paragraph(summary_text, styles["Normal"]))
    story.append(Spacer(1, 0.15 * inch))

    # Goals
    goals = data.get("goals")
    if goals:
        goal_lines = ", ".join(f"{k}: {v}" for k, v in goals.items())
        story.append(Paragraph(f"Goals: {goal_lines}", styles["Normal"]))
        story.append(Spacer(1, 0.15 * inch))

    # Overall score trend (last 10 sessions)
    recent = [s for s in data["sessions"] if s.get("overall_score") is not None][-10:]
    if recent:
        story.append(Paragraph("Overall Score (recent sessions)", styles["Heading3"]))
        trend_rows = [["Date", "Overall Score"]]
        for s in recent:
            trend_rows.append([s["created_at"][:10], str(s["overall_score"])])
        t = Table(trend_rows, colWidths=[2 * inch, 2 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4F46E5")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.3 * inch))

    # ── Detailed SLP section ──────────────────────────────────
    story.append(Paragraph("Detailed Clinical Metrics (SLP)", styles["Heading2"]))
    story.append(Spacer(1, 0.1 * inch))

    detail_headers = ["Date", "Task", "Overall", "WPM", "WER", "DDK", "Jitter", "Shimmer", "HNR"]
    detail_rows = [detail_headers]
    for a in assessments:
        detail_rows.append([
            a.get("created_at", "")[:10],
            a.get("task", ""),
            str(a.get("score_overall", "")),
            str(a.get("wpm", "—")),
            str(a.get("word_error_rate", "—")),
            str(a.get("ddk_rate", "—")),
            str(a.get("jitter", "—")),
            str(a.get("shimmer", "—")),
            str(a.get("hnr", "—")),
        ])

    col_w = [0.95 * inch] * len(detail_headers)
    dt = Table(detail_rows, colWidths=col_w)
    dt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E1B4B")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ("ALIGN", (2, 0), (-1, -1), "CENTER"),
    ]))
    story.append(dt)

    doc.build(story)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=speakeasy_{user_id[:8]}.pdf"},
    )
