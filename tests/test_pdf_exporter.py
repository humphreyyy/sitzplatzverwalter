"""
Unit tests for the PdfExporter module.

Tests PDF generation functionality including:
- Basic PDF generation
- Empty assignments handling
- Statistics rendering
- File saving
- Error handling
"""

import unittest
import os
import tempfile
from logic.pdf_exporter import PdfExporter, REPORTLAB_AVAILABLE
from models.assignment import Assignment
from models.student import Student
from models.seat import Seat


class TestPdfExporter(unittest.TestCase):
    """Test cases for the PdfExporter class."""

    def setUp(self):
        """Set up test data."""
        self.students = [
            Student(id="st1", name="Alice Schmidt", weekly_pattern={"monday": True}),
            Student(id="st2", name="Bob Müller", weekly_pattern={"monday": True}),
        ]
        self.seats = [
            Seat(id="s1", room_id="r1", number=1, x=0, y=0),
            Seat(id="s2", room_id="r1", number=2, x=10, y=0),
        ]
        self.assignments = {
            "monday": [
                Assignment(student_id="st1", seat_id="s1", day="monday", week="2025-W43"),
                Assignment(student_id="st2", seat_id="s2", day="monday", week="2025-W43"),
            ],
            "tuesday": [],
            "wednesday": [],
            "thursday": [],
            "friday": [],
            "saturday": [],
            "sunday": [],
        }
        self.week = "2025-W43"

    @unittest.skipUnless(REPORTLAB_AVAILABLE, "ReportLab not installed")
    def test_export_week_to_pdf_basic(self):
        """Test basic PDF generation with valid data."""
        pdf_content = PdfExporter.export_week_to_pdf(
            week=self.week,
            assignments=self.assignments,
            students=self.students,
            seats=self.seats
        )

        self.assertIsInstance(pdf_content, bytes)
        self.assertGreater(len(pdf_content), 0)
        # Check PDF header magic bytes
        self.assertTrue(pdf_content.startswith(b'%PDF'))

    @unittest.skipUnless(REPORTLAB_AVAILABLE, "ReportLab not installed")
    def test_export_week_to_pdf_empty_assignments(self):
        """Test PDF generation with no assignments."""
        empty_assignments = {
            day: [] for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        }

        pdf_content = PdfExporter.export_week_to_pdf(
            week=self.week,
            assignments=empty_assignments,
            students=self.students,
            seats=self.seats
        )

        self.assertIsInstance(pdf_content, bytes)
        self.assertGreater(len(pdf_content), 0)
        self.assertTrue(pdf_content.startswith(b'%PDF'))

    @unittest.skipUnless(REPORTLAB_AVAILABLE, "ReportLab not installed")
    def test_export_week_to_pdf_with_statistics(self):
        """Test PDF generation with statistics section."""
        statistics = {
            'total_assignments': 2,
            'total_conflicts': 0,
            'occupancy_rate': 14.29,
            'days_with_conflicts': 0,
            'conflict_rate': 0.0,
            'total_students': 2,
            'total_seats': 2,
        }

        pdf_content = PdfExporter.export_week_to_pdf(
            week=self.week,
            assignments=self.assignments,
            students=self.students,
            seats=self.seats,
            statistics=statistics
        )

        self.assertIsInstance(pdf_content, bytes)
        self.assertGreater(len(pdf_content), 0)
        self.assertTrue(pdf_content.startswith(b'%PDF'))

    @unittest.skipUnless(REPORTLAB_AVAILABLE, "ReportLab not installed")
    def test_export_week_to_pdf_missing_student(self):
        """Test PDF generation with assignment referencing non-existent student."""
        assignments = {
            "monday": [
                Assignment(student_id="st999", seat_id="s1", day="monday", week="2025-W43"),
            ],
        }

        # Should still generate PDF, showing ID instead of name
        pdf_content = PdfExporter.export_week_to_pdf(
            week=self.week,
            assignments=assignments,
            students=self.students,
            seats=self.seats
        )

        self.assertIsInstance(pdf_content, bytes)
        self.assertGreater(len(pdf_content), 0)

    @unittest.skipUnless(REPORTLAB_AVAILABLE, "ReportLab not installed")
    def test_export_week_to_pdf_missing_seat(self):
        """Test PDF generation with assignment referencing non-existent seat."""
        assignments = {
            "monday": [
                Assignment(student_id="st1", seat_id="s999", day="monday", week="2025-W43"),
            ],
        }

        # Should still generate PDF, showing ID instead of seat number
        pdf_content = PdfExporter.export_week_to_pdf(
            week=self.week,
            assignments=assignments,
            students=self.students,
            seats=self.seats
        )

        self.assertIsInstance(pdf_content, bytes)
        self.assertGreater(len(pdf_content), 0)

    @unittest.skipUnless(REPORTLAB_AVAILABLE, "ReportLab not installed")
    def test_save_pdf_to_file(self):
        """Test saving PDF content to a file."""
        pdf_content = PdfExporter.export_week_to_pdf(
            week=self.week,
            assignments=self.assignments,
            students=self.students,
            seats=self.seats
        )

        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            tmp_path = tmp.name

        try:
            # Save PDF
            PdfExporter.save_pdf_to_file(pdf_content, tmp_path)

            # Verify file exists and has content
            self.assertTrue(os.path.exists(tmp_path))
            with open(tmp_path, 'rb') as f:
                saved_content = f.read()
            self.assertEqual(saved_content, pdf_content)
        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_save_pdf_to_file_invalid_path(self):
        """Test saving PDF to invalid path raises error."""
        pdf_content = b'%PDF-1.4\ntest'
        invalid_path = '/nonexistent/directory/file.pdf'

        with self.assertRaises(IOError):
            PdfExporter.save_pdf_to_file(pdf_content, invalid_path)

    def test_is_available(self):
        """Test checking if PDF export is available."""
        result = PdfExporter.is_available()
        self.assertIsInstance(result, bool)
        self.assertEqual(result, REPORTLAB_AVAILABLE)

    @unittest.skipIf(REPORTLAB_AVAILABLE, "Test only when ReportLab is not available")
    def test_export_without_reportlab(self):
        """Test that export fails gracefully when ReportLab is not installed."""
        with self.assertRaises(ImportError) as context:
            PdfExporter.export_week_to_pdf(
                week=self.week,
                assignments=self.assignments,
                students=self.students,
                seats=self.seats
            )
        self.assertIn("ReportLab", str(context.exception))

    @unittest.skipUnless(REPORTLAB_AVAILABLE, "ReportLab not installed")
    def test_export_week_to_pdf_all_days_with_assignments(self):
        """Test PDF generation with assignments on all days."""
        all_days_assignments = {}
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

        for day in days:
            all_days_assignments[day] = [
                Assignment(student_id="st1", seat_id="s1", day=day, week="2025-W43"),
            ]

        pdf_content = PdfExporter.export_week_to_pdf(
            week=self.week,
            assignments=all_days_assignments,
            students=self.students,
            seats=self.seats
        )

        self.assertIsInstance(pdf_content, bytes)
        self.assertGreater(len(pdf_content), 0)

    @unittest.skipUnless(REPORTLAB_AVAILABLE, "ReportLab not installed")
    def test_export_week_to_pdf_german_characters(self):
        """Test PDF generation with German characters (umlauts)."""
        german_students = [
            Student(id="st1", name="Müller, Jürgen", weekly_pattern={"monday": True}),
            Student(id="st2", name="Schröder, Björn", weekly_pattern={"monday": True}),
        ]
        german_assignments = {
            "monday": [
                Assignment(student_id="st1", seat_id="s1", day="monday", week="2025-W43"),
                Assignment(student_id="st2", seat_id="s2", day="monday", week="2025-W43"),
            ],
        }

        pdf_content = PdfExporter.export_week_to_pdf(
            week=self.week,
            assignments=german_assignments,
            students=german_students,
            seats=self.seats
        )

        self.assertIsInstance(pdf_content, bytes)
        self.assertGreater(len(pdf_content), 0)

    @unittest.skipUnless(REPORTLAB_AVAILABLE, "ReportLab not installed")
    def test_export_week_to_pdf_large_dataset(self):
        """Test PDF generation with many assignments."""
        # Create 50 students and 50 seats
        many_students = [
            Student(id=f"st{i}", name=f"Student {i}", weekly_pattern={"monday": True})
            for i in range(50)
        ]
        many_seats = [
            Seat(id=f"s{i}", room_id="r1", number=i, x=i*10, y=0)
            for i in range(50)
        ]
        many_assignments = {
            "monday": [
                Assignment(student_id=f"st{i}", seat_id=f"s{i}", day="monday", week="2025-W43")
                for i in range(50)
            ],
        }

        pdf_content = PdfExporter.export_week_to_pdf(
            week=self.week,
            assignments=many_assignments,
            students=many_students,
            seats=many_seats
        )

        self.assertIsInstance(pdf_content, bytes)
        self.assertGreater(len(pdf_content), 0)


if __name__ == '__main__':
    unittest.main()
