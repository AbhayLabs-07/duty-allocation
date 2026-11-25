import io
from typing import List, Dict, Any, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

class ReportGenerator:
    """
    Generates downloadable reports in Excel (.xlsx), PDF, and Printable HTML.
    Supports all 8 required institutional reports.
    """

    @staticmethod
    def generate_excel(report_type: str, title: str, headers: List[str], data_rows: List[List[Any]]) -> io.BytesIO:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = report_type[:30]

        # College / System Title Header
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(headers))
        title_cell = ws.cell(row=1, column=1)
        title_cell.value = "CENTRAL EXAMINATION DEPARTMENT - FAIRNESS & ALLOCATION SYSTEM"
        title_cell.font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
        title_cell.fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        title_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 32

        # Subtitle
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(headers))
        sub_cell = ws.cell(row=2, column=1)
        sub_cell.value = f"REPORT: {title.upper()}"
        sub_cell.font = Font(name="Calibri", size=11, bold=True, color="333333")
        sub_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[2].height = 22

        # Table Column Headers
        header_fill = PatternFill(start_color="3B82F6", end_color="3B82F6", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        thin_border = Border(
            left=Side(style='thin', color='D1D5DB'),
            right=Side(style='thin', color='D1D5DB'),
            top=Side(style='thin', color='D1D5DB'),
            bottom=Side(style='thin', color='D1D5DB')
        )

        ws.row_dimensions[4].height = 24
        for col_idx, header_text in enumerate(headers, start=1):
            cell = ws.cell(row=4, column=col_idx)
            cell.value = header_text
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border

        # Data Rows
        zebra_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
        for row_idx, row_data in enumerate(data_rows, start=5):
            ws.row_dimensions[row_idx].height = 20
            is_zebra = (row_idx % 2 == 0)
            for col_idx, val in enumerate(row_data, start=1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.value = val
                cell.font = Font(name="Calibri", size=10)
                cell.border = thin_border
                if is_zebra:
                    cell.fill = zebra_fill
                
                # Role highlight
                if str(val) == "JS":
                    cell.font = Font(name="Calibri", size=10, bold=True, color="1D4ED8")
                elif str(val) == "Reliever":
                    cell.font = Font(name="Calibri", size=10, bold=True, color="047857")
                elif str(val) == "Standby":
                    cell.font = Font(name="Calibri", size=10, bold=True, color="B45309")
                elif str(val) == "SS":
                    cell.font = Font(name="Calibri", size=10, bold=True, color="6D28D9")

        # Auto-fit column widths
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    @staticmethod
    def generate_pdf(title: str, headers: List[str], data_rows: List[List[Any]]) -> io.BytesIO:
        output = io.BytesIO()
        doc = SimpleDocTemplate(
            output,
            pagesize=landscape(letter),
            leftMargin=30,
            rightMargin=30,
            topMargin=30,
            bottomMargin=30
        )
        styles = getSampleStyleSheet()
        elements = []

        # Header Title
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1E3A8A'),
            spaceAfter=4,
            alignment=1
        )
        subtitle_style = ParagraphStyle(
            'SubTitleStyle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#4B5563'),
            spaceAfter=15,
            alignment=1
        )

        elements.append(Paragraph("Smart Exam Duty Fairness & Allocation System", title_style))
        elements.append(Paragraph(f"Official Examination Report: {title}", subtitle_style))

        # Format table data
        table_data = [[Paragraph(f"<b>{h}</b>", styles['Normal']) for h in headers]]
        for row in data_rows[:250]: # Limit max per page chunk for stability
            formatted_row = [Paragraph(str(c if c is not None else "-"), styles['Normal']) for c in row]
            table_data.append(formatted_row)

        col_count = len(headers)
        avail_width = 730
        col_width = avail_width / max(1, col_count)

        table = Table(table_data, colWidths=[col_width] * col_count, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ]))
        elements.append(table)

        doc.build(elements)
        output.seek(0)
        return output

    @staticmethod
    def generate_html(title: str, headers: List[str], data_rows: List[List[Any]]) -> str:
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title} - Smart Exam Duty Fairness System</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 20px; color: #1e293b; }}
        .header {{ text-align: center; border-bottom: 2px solid #2563eb; padding-bottom: 15px; margin-bottom: 20px; }}
        .header h1 {{ margin: 0; color: #1e3a8a; font-size: 22px; }}
        .header p {{ margin: 5px 0 0; color: #64748b; font-size: 14px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 10px; }}
        th {{ background: #2563eb; color: #ffffff; padding: 10px 12px; text-align: left; border: 1px solid #93c5fd; }}
        td {{ padding: 8px 12px; border: 1px solid #e2e8f0; }}
        tr:nth-child(even) {{ background: #f8fafc; }}
        .role-js {{ font-weight: bold; color: #2563eb; }}
        .role-rel {{ font-weight: bold; color: #059669; }}
        .role-stb {{ font-weight: bold; color: #d97706; }}
        .role-ss {{ font-weight: bold; color: #7c3aed; }}
        .print-btn {{ background: #2563eb; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 14px; margin-bottom: 15px; }}
        @media print {{
            .print-btn {{ display: none; }}
            body {{ margin: 0; }}
        }}
    </style>
</head>
<body>
    <button class="print-btn" onclick="window.print()">Print / Save as PDF</button>
    <div class="header">
        <h1>Smart Exam Duty Fairness & Allocation System</h1>
        <p>Official Examination Report: {title} | Generated: {openpyxl.utils.datetime.datetime.now().strftime("%d-%b-%Y %I:%M %p")}</p>
    </div>
    <table>
        <thead>
            <tr>
                {"".join(f"<th>{h}</th>" for h in headers)}
            </tr>
        </thead>
        <tbody>
"""
        for row in data_rows:
            html += "            <tr>\n"
            for cell in row:
                c_val = str(cell if cell is not None else "-")
                c_class = ""
                if c_val == "JS":
                    c_class = ' class="role-js"'
                elif c_val == "Reliever":
                    c_class = ' class="role-rel"'
                elif c_val == "Standby":
                    c_class = ' class="role-stb"'
                elif c_val == "SS":
                    c_class = ' class="role-ss"'
                html += f"                <td{c_class}>{c_val}</td>\n"
            html += "            </tr>\n"

        html += """        </tbody>
    </table>
</body>
</html>
"""
        return html
