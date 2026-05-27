"""Report Generator for session analytics.

Generates reports in TXT, CSV, and PDF formats from session data.
Reports are saved to the app's external storage directory.
"""

import os
import csv
import time
from datetime import datetime

import config


class ReportGenerator:
    """Generates session reports in multiple formats."""

    def __init__(self):
        self._report_dir = self._get_report_dir()

    @staticmethod
    def _get_report_dir():
        """Get the directory for saving reports.

        On Android, uses external storage. Falls back to current directory.

        Returns:
            String path to report directory.
        """
        try:
            from plyer import storagepath
            report_dir = os.path.join(
                storagepath.get_documents_dir(),
                config.REPORT_DIR_NAME
            )
        except Exception:
            # Fallback: use current directory
            report_dir = os.path.join(
                os.path.expanduser("~"),
                config.REPORT_DIR_NAME
            )

        # Create directory if it doesn't exist
        os.makedirs(report_dir, exist_ok=True)
        return report_dir

    def generate_report(self, session_summary, event_log, fatigue_history,
                        fmt="txt"):
        """Generate a report in the specified format.

        Args:
            session_summary: Dict from SessionTracker.get_summary().
            event_log: List of event dicts from SessionTracker.
            fatigue_history: List of (timestamp, score) tuples.
            fmt: Format - 'txt', 'csv', or 'pdf'.

        Returns:
            String path to the generated report file, or None on error.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"driver_report_{timestamp}"

        if fmt == "txt":
            return self._generate_txt(filename, session_summary, event_log)
        elif fmt == "csv":
            return self._generate_csv(filename, session_summary, event_log)
        elif fmt == "pdf":
            return self._generate_pdf(filename, session_summary, event_log)
        else:
            print(f"[ERROR] Unknown report format: {fmt}")
            return None

    def _generate_txt(self, filename, summary, events):
        """Generate a plain text report.

        Args:
            filename: Base filename (without extension).
            summary: Session summary dict.
            events: Event log list.

        Returns:
            Path to the generated file.
        """
        filepath = os.path.join(self._report_dir, f"{filename}.txt")

        try:
            duration_str = self._format_duration(summary.get('session_duration', 0))

            with open(filepath, 'w') as f:
                f.write("=" * 60 + "\n")
                f.write("  DRIVER SAFETY MONITORING REPORT\n")
                f.write("=" * 60 + "\n\n")

                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Driver: {config.DRIVER_NAME}\n")
                f.write(f"Session Duration: {duration_str}\n\n")

                f.write("-" * 40 + "\n")
                f.write("  SESSION STATISTICS\n")
                f.write("-" * 40 + "\n")
                f.write(f"Total Yawns:          {summary.get('total_yawns', 0)}\n")
                f.write(f"Drowsiness Events:    {summary.get('drowsiness_events', 0)}\n")
                f.write(f"Phone Usage Events:   {summary.get('phone_usage_events', 0)}\n")
                f.write(f"Distraction Events:   {summary.get('distraction_count', 0)}\n\n")

                f.write("-" * 40 + "\n")
                f.write("  FATIGUE ANALYSIS\n")
                f.write("-" * 40 + "\n")
                f.write(f"Max Fatigue Score:    {summary.get('max_fatigue_score', 0):.1f}/100\n")
                f.write(f"Max Fatigue Level:    {summary.get('max_fatigue_level', 'N/A')}\n")
                f.write(f"Average EAR:          {summary.get('average_ear', 0):.3f}\n")
                f.write(f"Average MAR:          {summary.get('average_mar', 0):.3f}\n\n")

                # Event timeline
                if events:
                    f.write("-" * 40 + "\n")
                    f.write("  EVENT TIMELINE\n")
                    f.write("-" * 40 + "\n")
                    for event in events[-50:]:  # Last 50 events
                        ts = datetime.fromtimestamp(
                            event['timestamp']
                        ).strftime('%H:%M:%S')
                        f.write(f"  [{ts}] {event['type']}: {event['description']}\n")

                f.write("\n" + "=" * 60 + "\n")
                f.write("  End of Report\n")
                f.write("=" * 60 + "\n")

            print(f"[INFO] TXT report saved: {filepath}")
            return filepath

        except Exception as e:
            print(f"[ERROR] Failed to generate TXT report: {e}")
            return None

    def _generate_csv(self, filename, summary, events):
        """Generate a CSV report.

        Args:
            filename: Base filename (without extension).
            summary: Session summary dict.
            events: Event log list.

        Returns:
            Path to the generated file.
        """
        filepath = os.path.join(self._report_dir, f"{filename}.csv")

        try:
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)

                # Summary section
                writer.writerow(["Driver Safety Monitoring Report"])
                writer.writerow([])
                writer.writerow(["Metric", "Value"])
                writer.writerow(["Date", datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow(["Driver", config.DRIVER_NAME])
                writer.writerow(["Session Duration (s)",
                                f"{summary.get('session_duration', 0):.0f}"])
                writer.writerow(["Total Yawns", summary.get('total_yawns', 0)])
                writer.writerow(["Drowsiness Events",
                                summary.get('drowsiness_events', 0)])
                writer.writerow(["Phone Usage Events",
                                summary.get('phone_usage_events', 0)])
                writer.writerow(["Distraction Count",
                                summary.get('distraction_count', 0)])
                writer.writerow(["Max Fatigue Score",
                                f"{summary.get('max_fatigue_score', 0):.1f}"])
                writer.writerow(["Max Fatigue Level",
                                summary.get('max_fatigue_level', 'N/A')])
                writer.writerow(["Average EAR",
                                f"{summary.get('average_ear', 0):.3f}"])
                writer.writerow(["Average MAR",
                                f"{summary.get('average_mar', 0):.3f}"])

                # Event log
                writer.writerow([])
                writer.writerow(["Event Log"])
                writer.writerow(["Timestamp", "Type", "Description"])
                for event in events:
                    ts = datetime.fromtimestamp(
                        event['timestamp']
                    ).strftime('%Y-%m-%d %H:%M:%S')
                    writer.writerow([ts, event['type'], event['description']])

            print(f"[INFO] CSV report saved: {filepath}")
            return filepath

        except Exception as e:
            print(f"[ERROR] Failed to generate CSV report: {e}")
            return None

    def _generate_pdf(self, filename, summary, events):
        """Generate a PDF report using fpdf2.

        Args:
            filename: Base filename (without extension).
            summary: Session summary dict.
            events: Event log list.

        Returns:
            Path to the generated file.
        """
        filepath = os.path.join(self._report_dir, f"{filename}.pdf")

        try:
            from fpdf import FPDF

            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)

            # Title
            pdf.set_font("Helvetica", "B", 18)
            pdf.cell(0, 15, "Driver Safety Monitoring Report", ln=True, align="C")
            pdf.ln(5)

            # Date and driver info
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 8, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                     ln=True)
            pdf.cell(0, 8, f"Driver: {config.DRIVER_NAME}", ln=True)
            duration_str = self._format_duration(summary.get('session_duration', 0))
            pdf.cell(0, 8, f"Session Duration: {duration_str}", ln=True)
            pdf.ln(5)

            # Session Statistics section
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 10, "Session Statistics", ln=True)
            pdf.set_font("Helvetica", "", 11)

            stats = [
                ("Total Yawns", summary.get('total_yawns', 0)),
                ("Drowsiness Events", summary.get('drowsiness_events', 0)),
                ("Phone Usage Events", summary.get('phone_usage_events', 0)),
                ("Distraction Count", summary.get('distraction_count', 0)),
            ]
            for label, value in stats:
                pdf.cell(80, 8, f"  {label}:", border=0)
                pdf.cell(0, 8, str(value), ln=True)

            pdf.ln(3)

            # Fatigue Analysis section
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 10, "Fatigue Analysis", ln=True)
            pdf.set_font("Helvetica", "", 11)

            fatigue_stats = [
                ("Max Fatigue Score",
                 f"{summary.get('max_fatigue_score', 0):.1f}/100"),
                ("Max Fatigue Level", summary.get('max_fatigue_level', 'N/A')),
                ("Average EAR", f"{summary.get('average_ear', 0):.3f}"),
                ("Average MAR", f"{summary.get('average_mar', 0):.3f}"),
            ]
            for label, value in fatigue_stats:
                pdf.cell(80, 8, f"  {label}:", border=0)
                pdf.cell(0, 8, str(value), ln=True)

            pdf.ln(5)

            # Event Timeline
            if events:
                pdf.set_font("Helvetica", "B", 14)
                pdf.cell(0, 10, "Event Timeline", ln=True)
                pdf.set_font("Helvetica", "", 9)

                for event in events[-30:]:  # Last 30 events
                    ts = datetime.fromtimestamp(
                        event['timestamp']
                    ).strftime('%H:%M:%S')
                    line = f"  [{ts}] {event['type']}: {event['description']}"
                    pdf.cell(0, 6, line, ln=True)

            pdf.output(filepath)
            print(f"[INFO] PDF report saved: {filepath}")
            return filepath

        except ImportError:
            print("[ERROR] fpdf2 not installed. Cannot generate PDF.")
            return None
        except Exception as e:
            print(f"[ERROR] Failed to generate PDF report: {e}")
            return None

    @staticmethod
    def _format_duration(seconds):
        """Format duration in seconds to HH:MM:SS string.

        Args:
            seconds: Duration in seconds.

        Returns:
            Formatted string.
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def get_report_dir(self):
        """Get the report directory path.

        Returns:
            String path.
        """
        return self._report_dir
