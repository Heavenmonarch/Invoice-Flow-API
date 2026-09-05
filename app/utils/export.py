import csv
import io
import logging
from datetime import datetime, timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

logger = logging.getLogger(__name__)


BRAND_DARK = colors.HexColor("#1E3A5F")
BRAND_ACCENT = colors.HexColor("#2E86AB")
LIGHT_BG = colors.HexColor("#EBF4F8")
WHITE = colors.white
BLACK = colors.black
GREEN = colors.HexColor("#27AE60")
MUTED = colors.HexColor("#777777")


def generate_commission_csv(
    rows: list[dict],
    period: str,
    organization_name: str,
) -> io.StringIO:
    """
    Generates a CSV file in memory and returns a StringIO buffer.
    Each row is one staff member's commission summary for the period.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Header metadata
    writer.writerow(["Organization", organization_name])
    writer.writerow(["Period", period])
    writer.writerow([
        "Generated At",
        datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    ])
    writer.writerow([])

    # Column headers
    writer.writerow([
        "Staff Name",
        "Email",
        "Total Sales",
        "Total Revenue (₦)",
        "Commission Rate (%)",
        "Commission Amount (₦)",
        "Status",
    ])

    # Data rows
    for row in rows:
        writer.writerow([
            row.get("full_name", ""),
            row.get("email", ""),
            row.get("total_sales", 0),
            f"{row.get('total_amount', 0):,.2f}",
            f"{row.get('commission_rate', 0):.2f}",
            f"{row.get('total_commission', 0):,.2f}",
            row.get("status", "").capitalize(),
        ])

    # Totals row
    writer.writerow([])
    writer.writerow([
        "TOTAL",
        "",
        sum(r.get("total_sales", 0) for r in rows),
        f"{sum(r.get('total_amount', 0) for r in rows):,.2f}",
        "",
        f"{sum(r.get('total_commission', 0) for r in rows):,.2f}",
        "",
    ])

    output.seek(0)
    return output


# for pdfs
def generate_commission_pdf(
    rows: list[dict],
    period: str,
    organization_name: str,
) -> io.BytesIO:
    """
    Generates a PDF report in memory and returns a BytesIO buffer.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )

    styles = getSampleStyleSheet()
    elements = []

    
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontSize=20,
        textColor=BRAND_DARK,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=MUTED,
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    elements.append(Paragraph("Commission Report", title_style))
    elements.append(Paragraph(organization_name, subtitle_style))
    elements.append(Paragraph(f"Period: {period}", subtitle_style))
    elements.append(Paragraph(
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        subtitle_style,
    ))
    elements.append(Spacer(1, 0.3 * inch))

  
    total_sales = sum(r.get("total_sales", 0) for r in rows)
    total_revenue = sum(r.get("total_amount", 0) for r in rows)
    total_commission = sum(r.get("total_commission", 0) for r in rows)

    summary_data = [
        ["Total Staff", "Total Sales", "Total Revenue", "Total Commission"],
        [
            str(len(rows)),
            str(total_sales),
            f"₦{total_revenue:,.2f}",
            f"₦{total_commission:,.2f}",
        ],
    ]
    summary_table = Table(summary_data, colWidths=[2 * inch] * 4)
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BACKGROUND", (0, 1), (-1, 1), LIGHT_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, MUTED),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT_BG, WHITE]),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.2 * inch))

  
    headers = [
        "Staff Name",
        "Email",
        "Total Sales",
        "Total Revenue (₦)",
        "Commission (₦)",
        "Status",
    ]
    col_widths = [1.8 * inch, 2.2 * inch, 1 * inch, 1.8 * inch, 1.8 * inch, 1 * inch]

    table_data = [headers]
    for row in rows:
        status = row.get("status", "pending")
        table_data.append([
            row.get("full_name", ""),
            row.get("email", ""),
            str(row.get("total_sales", 0)),
            f"₦{row.get('total_amount', 0):,.2f}",
            f"₦{row.get('total_commission', 0):,.2f}",
            status.capitalize(),
        ])

    # Totals row
    table_data.append([
        "TOTAL",
        "",
        str(total_sales),
        f"₦{total_revenue:,.2f}",
        f"₦{total_commission:,.2f}",
        "",
    ])

    main_table = Table(table_data, colWidths=col_widths)

    # Build row-level style commands
    style_commands = [
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 1), (1, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.5, MUTED),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        # Totals row — last row
        ("BACKGROUND", (0, -1), (-1, -1), BRAND_DARK),
        ("TEXTCOLOR", (0, -1), (-1, -1), WHITE),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]

    # Alternate row colors for data rows
    for i in range(1, len(table_data) - 1):
        bg = LIGHT_BG if i % 2 == 0 else WHITE
        style_commands.append(("BACKGROUND", (0, i), (-1, i), bg))

    # Color-code status column
    status_col = 5
    for i, row in enumerate(rows, start=1):
        status = row.get("status", "pending")
        color = {
            "approved": GREEN,
            "paid": BRAND_ACCENT,
            "disputed": colors.HexColor("#E74C3C"),
            "pending": MUTED,
        }.get(status, BLACK)
        style_commands.append(("TEXTCOLOR", (status_col, i), (status_col, i), color))
        style_commands.append(("FONTNAME", (status_col, i), (status_col, i), "Helvetica-Bold"))

    main_table.setStyle(TableStyle(style_commands))
    elements.append(main_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer