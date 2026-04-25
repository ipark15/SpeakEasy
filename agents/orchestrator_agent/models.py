from uagents import Model


class AssessmentRequest(Model):
    session_id: str
    assessment_json: str  # full assessment dict serialized as JSON string


class ReportResponse(Model):
    session_id: str
    pdf_path: str
    status: str    # "success" or "error: <message>"
    summary: str   # Gemma overall summary for frontend display
