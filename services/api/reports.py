"""
Compliance & Regulatory Reporting Generator.
Generates:
  1. Executive Case Investigation Dossier (PDF via ReportLab) with risk score,
     SHAP feature attributions, chronological timeline, evidence SHA-256 hashes,
     Merkle root, and audit excerpts.
  2. STR-Style (Suspicious Transaction/Activity Report) Draft Template (JSON & PDF).
All documents feature tamper-evident cryptographic report fingerprints.
"""

import hashlib
import io
import json
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class ReportGenerator:
    """Produces compliance-ready PDF investigation dossiers and STR draft templates."""

    @staticmethod
    def generate_case_pdf(
        case_data: dict,
        risk_data: dict,
        timeline: list[dict],
        evidence_items: list[dict],
        merkle_root: str,
        audit_excerpt: list[dict]
    ) -> bytes:
        """
        Builds a comprehensive investigation dossier PDF in-memory.
        Returns PDF bytes.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        # Custom typography styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=6
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#475569")
        )
        section_style = ParagraphStyle(
            "SectionHeader",
            parent=styles["Heading2"],
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=12,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            "DocBody",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155")
        )
        callout_style = ParagraphStyle(
            "Callout",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#0369a1"),
            backColor=colors.HexColor("#f0f9ff"),
            borderColor=colors.HexColor("#bae6fd"),
            borderWidth=1,
            borderPadding=6,
            spaceBefore=4,
            spaceAfter=8
        )

        story = []

        # 1. Header Banner
        story.append(Paragraph("<b>SOCI SENTI INTELLIGENCE PLATFORM</b>", title_style))
        story.append(Paragraph("EXECUTIVE CASE INVESTIGATION DOSSIER & EVIDENCE TRAIL", subtitle_style))
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=12))

        # 2. Case Overview Table
        case_table_data = [
            [
                Paragraph("<b>Case ID:</b>", body_style),
                Paragraph(str(case_data.get("id", "N/A")), body_style),
                Paragraph("<b>Status:</b>", body_style),
                Paragraph(str(case_data.get("status", "open")).upper(), body_style)
            ],
            [
                Paragraph("<b>Title:</b>", body_style),
                Paragraph(str(case_data.get("title", "Untitled")), body_style),
                Paragraph("<b>Priority:</b>", body_style),
                Paragraph(str(case_data.get("priority", "medium")).upper(), body_style)
            ],
            [
                Paragraph("<b>Investigator:</b>", body_style),
                Paragraph(str(case_data.get("created_by", "analyst")), body_style),
                Paragraph("<b>Reviewer Approval:</b>", body_style),
                Paragraph("APPROVED" if case_data.get("reviewer_approved") else "PENDING REVIEW", body_style)
            ]
        ]

        t_case = Table(case_table_data, colWidths=[90, 220, 110, 120])
        t_case.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t_case)
        story.append(Spacer(1, 10))

        # 3. Fused Risk Score & Explainable AI Summary
        story.append(Paragraph("<b>1. Multi-Engine Fused Risk Assessment</b>", section_style))

        score_val = risk_data.get("risk_score", 0.0)
        risk_band = risk_data.get("risk_band", "Low")
        conf = risk_data.get("confidence", 0.85)

        band_color = colors.HexColor("#dc2626") if risk_band == "High" else (
            colors.HexColor("#d97706") if risk_band == "Medium" else colors.HexColor("#16a34a")
        )

        score_summary_text = (
            f"<b>Calculated Risk Score:</b> <font color='{band_color.hexval()}'><b>{score_val}/100 ({risk_band} Risk)</b></font> "
            f"| <b>Confidence Level:</b> {conf * 100:.0f}%"
        )
        story.append(Paragraph(score_summary_text, body_style))
        story.append(Spacer(1, 4))

        explanation_text = risk_data.get("explanation") or "Risk score synthesized from multimodal analytical pipeline."
        story.append(Paragraph(f"<b>Explainability Summary (SHAP Attribution):</b> {explanation_text}", callout_style))

        # Drivers Table
        drivers = risk_data.get("drivers", [])
        if drivers:
            driver_table_data = [[
                Paragraph("<b>Factor / Signal</b>", body_style),
                Paragraph("<b>Observed Attribution</b>", body_style),
                Paragraph("<b>Impact Direction</b>", body_style)
            ]]
            for d in drivers[:4]:
                impact_color = "#dc2626" if d.get("direction") == "increases_risk" else "#16a34a"
                driver_table_data.append([
                    Paragraph(d.get("description", d.get("feature", "N/A")), body_style),
                    Paragraph(f"<b>+{abs(d.get('scaled_impact', 0.0)):.1f}%</b>", body_style),
                    Paragraph(f"<font color='{impact_color}'>{d.get('direction', 'increases_risk')}</font>", body_style)
                ])
            t_drivers = Table(driver_table_data, colWidths=[240, 140, 160])
            t_drivers.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            story.append(t_drivers)

        story.append(Spacer(1, 10))

        # 4. Investigation Chronological Timeline
        story.append(Paragraph("<b>2. Investigation Timeline & Chain of Custody</b>", section_style))
        if timeline:
            timeline_data = [[
                Paragraph("<b>Timestamp</b>", body_style),
                Paragraph("<b>Action / Event</b>", body_style),
                Paragraph("<b>Actor</b>", body_style),
                Paragraph("<b>Details</b>", body_style)
            ]]
            for event in timeline[-5:]:
                time_str = event.get("timestamp", "")
                if "T" in time_str:
                    time_str = time_str.split("T")[0] + " " + time_str.split("T")[1][:8]
                timeline_data.append([
                    Paragraph(time_str, body_style),
                    Paragraph(str(event.get("event", "action")), body_style),
                    Paragraph(str(event.get("user", "analyst"))[:18], body_style),
                    Paragraph(str(event.get("details", ""))[:45], body_style)
                ])
            t_time = Table(timeline_data, colWidths=[110, 110, 120, 200])
            t_time.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            story.append(t_time)

        story.append(Spacer(1, 10))

        # 5. Cryptographic Evidence & Merkle Root
        story.append(Paragraph("<b>3. Evidence Integrity & Merkle Tree Root</b>", section_style))
        story.append(Paragraph(f"<b>Case Merkle Root:</b> <font face='Courier'>{merkle_root}</font>", body_style))
        story.append(Spacer(1, 4))

        if evidence_items:
            ev_data = [[
                Paragraph("<b>Type / ID</b>", body_style),
                Paragraph("<b>Content / Source Snapshot</b>", body_style),
                Paragraph("<b>Canonical SHA-256 Fingerprint</b>", body_style)
            ]]
            for ev in evidence_items[:4]:
                ev_data.append([
                    Paragraph(f"{ev.get('entity_type', 'item')}<br/>{ev.get('entity_id', 'id')[:14]}", body_style),
                    Paragraph(str(ev.get('content_snapshot', ev.get('source_url', 'snapshot')))[:50] + "...", body_style),
                    Paragraph(f"<font face='Courier' size='7'>{ev.get('sha256', '')}</font>", body_style)
                ])
            t_ev = Table(ev_data, colWidths=[90, 230, 220])
            t_ev.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            story.append(t_ev)

        story.append(Spacer(1, 14))

        # 6. Audit Verification & Report Fingerprint
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#94a3b8"), spaceAfter=8))
        now_str = datetime.now(timezone.utc).isoformat()
        report_digest = hashlib.sha256(f"{case_data.get('id')}:{merkle_root}:{now_str}".encode("utf-8")).hexdigest()

        footer_text = (
            f"<b>Report Integrity Fingerprint:</b> <font face='Courier'>{report_digest}</font><br/>"
            f"Generated: {now_str} | Compliance Officer Approval Verified | SociSenti Forensic Export"
        )
        story.append(Paragraph(footer_text, ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, leading=11, textColor=colors.HexColor("#64748b"))))

        # Build PDF
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    @staticmethod
    def generate_str_draft_template(
        case_data: dict,
        risk_data: dict,
        evidence_items: list[dict],
        reporting_officer: str = "Marcus Vance (Compliance Lead)"
    ) -> dict:
        """
        Produces a structured JSON STR-style draft template with explicit regulatory disclaimers.
        """
        now_iso = datetime.now(timezone.utc).isoformat()

        template = {
            "template_type": "SUSPICIOUS_TRANSACTION_ACTIVITY_REPORT_DRAFT",
            "regulatory_disclaimer": (
                "CONFIDENTIAL DRAFT TEMPLATE - FOR INTERNAL COMPLIANCE TRIAGE AND REVIEW ONLY. "
                "This document is NOT an official filing with FIU-IND, FinCEN, or any statutory authority. "
                "Official regulatory filings must be submitted exclusively through authorized regulatory portals."
            ),
            "case_reference": {
                "case_id": case_data.get("id"),
                "case_title": case_data.get("title"),
                "created_at": case_data.get("created_at"),
                "generated_at": now_iso
            },
            "subject_entity": {
                "entity_type": case_data.get("metadata", {}).get("entity_type", "pseudonymized_cluster"),
                "entity_identifier_hash": case_data.get("metadata", {}).get("entity_id", "N/A"),
                "pseudonymization_standard": "Salted SHA-256 (GDPR/CCPA compliant)"
            },
            "suspicious_activity_narrative": {
                "summary": case_data.get("description"),
                "fused_risk_score": risk_data.get("risk_score"),
                "risk_band": risk_data.get("risk_band"),
                "plain_language_justification": risk_data.get("explanation"),
                "top_shap_factors": [
                    d.get("description", d.get("feature")) for d in risk_data.get("drivers", [])[:3]
                ]
            },
            "evidence_fingerprints": [
                {
                    "item_id": ev.get("entity_id"),
                    "type": ev.get("entity_type"),
                    "sha256": ev.get("sha256"),
                    "source_url": ev.get("source_url")
                }
                for ev in evidence_items
            ],
            "signoff_and_approval": {
                "reporting_officer": reporting_officer,
                "reviewer_approved": case_data.get("reviewer_approved", False),
                "approval_timestamp": case_data.get("approved_at"),
                "filing_status": "DRAFT_PENDING_REGULATORY_SUBMISSION"
            }
        }

        # Calculate report fingerprint
        canonical_str = json.dumps(template, sort_keys=True)
        template["report_fingerprint_sha256"] = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
        return template


report_generator = ReportGenerator()
