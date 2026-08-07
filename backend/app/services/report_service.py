"""
PDF report generation using reportlab.
"""
from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table,
                                 TableStyle)

DARK_RED = colors.HexColor("#8b0000")
BLACK = colors.HexColor("#1a0a0a")


def generate_pdf_report(analysis) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("TitleRed", parent=styles["Title"], textColor=DARK_RED)
    heading_style = ParagraphStyle("HeadingRed", parent=styles["Heading2"], textColor=DARK_RED)

    story = [
        Paragraph("MEMFORENSIX — Memory Forensics Report", title_style),
        Spacer(1, 6),
        Paragraph(f"Generated: {datetime.utcnow().isoformat()} UTC", styles["Normal"]),
        Paragraph(f"Target File: {analysis.filename}", styles["Normal"]),
        Paragraph(f"SHA-256: {analysis.file_hash_sha256}", styles["Normal"]),
        Paragraph(f"Status: {analysis.status.value}", styles["Normal"]),
        Spacer(1, 12),
        Paragraph("Executive Summary", heading_style),
    ]

    suspicious_procs = sum(1 for p in analysis.processes if p.is_suspicious)
    suspicious_conns = sum(1 for c in analysis.connections if c.is_suspicious)
    critical_yara = sum(1 for m in analysis.yara_matches if m.severity == "critical")

    summary_data = [
        ["Metric", "Count"],
        ["Total Processes", str(len(analysis.processes))],
        ["Suspicious Processes", str(suspicious_procs)],
        ["Total Network Connections", str(len(analysis.connections))],
        ["Suspicious Connections", str(suspicious_conns)],
        ["YARA Matches", str(len(analysis.yara_matches))],
        ["Critical YARA Matches", str(critical_yara)],
        ["ML Anomalies Detected", str(sum(1 for f in analysis.ml_findings if f.is_anomaly))],
    ]
    summary_table = Table(summary_data, colWidths=[300, 100])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLACK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 16))

    story.append(Paragraph("Suspicious Processes", heading_style))
    proc_rows = [["PID", "Name", "Command Line", "Reasons"]]
    for p in analysis.processes:
        if p.is_suspicious:
            proc_rows.append([str(p.pid), p.name, (p.cmdline or "")[:60],
                               ", ".join(p.suspicion_reasons or [])[:80]])
    if len(proc_rows) > 1:
        t = Table(proc_rows, colWidths=[40, 80, 200, 150])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK_RED),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("None detected.", styles["Normal"]))

    story.append(Spacer(1, 16))
    story.append(Paragraph("YARA Rule Matches", heading_style))
    yara_rows = [["Rule", "Severity", "Tags"]]
    for m in analysis.yara_matches:
        yara_rows.append([m.rule_name, m.severity, ", ".join(m.tags or [])])
    if len(yara_rows) > 1:
        t2 = Table(yara_rows, colWidths=[180, 80, 200])
        t2.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK_RED),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        story.append(t2)
    else:
        story.append(Paragraph("None detected.", styles["Normal"]))

    doc.build(story)
    return buffer.getvalue()
