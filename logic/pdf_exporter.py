"""
PDF export functionality for weekly seating assignments.

This module generates professional PDF reports showing:
- Weekly seating assignments by day
- Student-seat mappings in tabular format
- Summary statistics (occupancy, conflicts, etc.)
- German language formatting
"""

from typing import Dict, List, Optional
from datetime import datetime
from io import BytesIO

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from models.assignment import Assignment
from models.student import Student
from models.seat import Seat
from config import WEEKDAYS


class PdfExporter:
    """PDF report generator for seating assignments."""

    @staticmethod
    def export_week_to_pdf(
        week: str,
        assignments: Dict[str, List[Assignment]],
        students: List[Student],
        seats: List[Seat],
        statistics: Optional[Dict[str, any]] = None
    ) -> bytes:
        """Generate PDF report for a week's assignments.

        Args:
            week: Week identifier (e.g., "2025-W43")
            assignments: Dict mapping day -> list of assignments
            students: List of all students (for name lookup)
            seats: List of all seats (for seat lookup)
            statistics: Optional statistics dict from AssignmentEngine

        Returns:
            PDF content as bytes

        Raises:
            ImportError: If ReportLab is not installed
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab is required for PDF export. Install with: pip install reportlab")

        # Create in-memory buffer
        buffer = BytesIO()

        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        # Build content
        story = []

        # Create styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e3a5f'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1e3a5f'),
            spaceAfter=12
        )

        # Title
        title = Paragraph(f"Sitzplan für Woche {week}", title_style)
        story.append(title)
        story.append(Spacer(1, 0.5*cm))

        # Create lookup dictionaries
        student_dict = {s.id: s for s in students}
        seat_dict = {s.id: s for s in seats}

        # Generate daily tables for each day
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

        for day in days:
            # Day heading
            german_day = WEEKDAYS.get(day, day.capitalize())
            day_heading = Paragraph(german_day, heading_style)
            story.append(day_heading)

            # Get assignments for this day
            day_assignments = assignments.get(day, [])

            if day_assignments:
                # Create table data
                table_data = [["Sitzplatz", "Student", "Raum"]]  # Header row

                for assignment in day_assignments:
                    student = student_dict.get(assignment.student_id)
                    seat = seat_dict.get(assignment.seat_id)

                    student_name = student.name if student else f"ID: {assignment.student_id}"
                    seat_display = f"Platz {seat.number}" if seat else f"ID: {assignment.seat_id}"
                    room_id = seat.room_id if seat else "N/A"

                    table_data.append([seat_display, student_name, room_id])

                # Create table
                table = Table(table_data, colWidths=[4*cm, 8*cm, 4*cm])
                table.setStyle(TableStyle([
                    # Header styling
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

                    # Body styling
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
                ]))

                story.append(table)
            else:
                # No assignments for this day
                no_assign_text = Paragraph("<i>Keine Zuteilungen für diesen Tag</i>", styles['Normal'])
                story.append(no_assign_text)

            story.append(Spacer(1, 0.5*cm))

        # Add page break before statistics
        story.append(PageBreak())

        # Statistics section
        if statistics:
            stats_heading = Paragraph("Statistik", heading_style)
            story.append(stats_heading)

            stats_data = [
                ["Metrik", "Wert"],
                ["Gesamtzuweisungen", str(statistics.get('total_assignments', 0))],
                ["Konflikte", str(statistics.get('total_conflicts', 0))],
                ["Auslastung", f"{statistics.get('occupancy_rate', 0):.1f}%"],
                ["Tage mit Konflikten", str(statistics.get('days_with_conflicts', 0))],
                ["Konfliktrate", f"{statistics.get('conflict_rate', 0):.1f}%"],
                ["Anzahl Studenten", str(statistics.get('total_students', 0))],
                ["Anzahl Sitzplätze", str(statistics.get('total_seats', 0))],
            ]

            stats_table = Table(stats_data, colWidths=[8*cm, 6*cm])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
            ]))

            story.append(stats_table)

        # Footer with generation timestamp
        story.append(Spacer(1, 1*cm))
        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        footer_text = Paragraph(
            f"<i>Erstellt am: {timestamp}</i>",
            styles['Normal']
        )
        story.append(footer_text)

        # Build PDF
        doc.build(story)

        # Get PDF content
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    @staticmethod
    def save_pdf_to_file(pdf_content: bytes, filename: str) -> None:
        """Save PDF content to a file.

        Args:
            pdf_content: PDF content as bytes (from export_week_to_pdf)
            filename: Path to output file

        Raises:
            IOError: If file cannot be written
        """
        try:
            with open(filename, 'wb') as f:
                f.write(pdf_content)
        except Exception as e:
            raise IOError(f"Failed to save PDF to {filename}: {str(e)}")

    @staticmethod
    def is_available() -> bool:
        """Check if PDF export functionality is available.

        Returns:
            True if ReportLab is installed, False otherwise
        """
        return REPORTLAB_AVAILABLE
