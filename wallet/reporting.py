"""Well-formatted PDF report generation (ReportLab)."""
import io
from datetime import date
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (HRFlowable, Image as RLImage, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

from .utils import fmt_money

ACCENTS = {"blue": "#2563EB", "pink": "#DB2777", "green": "#16A34A"}


def _style(name, size, color, bold=True, space=6):
    return ParagraphStyle(name, fontName="Helvetica-Bold" if bold else "Helvetica",
                          fontSize=size, leading=size * 1.4, textColor=color, spaceAfter=space)


def export_pdf(path, user, data, figures, symbol):
    accent = colors.HexColor(ACCENTS.get(user["theme_accent"], "#2563EB"))
    ink = colors.HexColor("#0F172A")
    muted = colors.HexColor("#64748B")
    line = colors.HexColor("#E2E8F0")
    soft = colors.HexColor("#F5F7FA")

    title = _style("t", 22, accent, space=2)
    sub = _style("s", 13, ink, space=2)
    small = _style("sm", 9, muted, bold=False, space=8)
    h2 = _style("h2", 13, ink, space=6)

    t = data["totals"]
    net = t["income"] - t["expense"] - t["savings"]
    who = escape(user["display_name"] or user["username"])

    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm,
                            topMargin=14 * mm, bottomMargin=14 * mm, title="Digital Wallet Report")
    el = [Paragraph("Digital Wallet", title),
          Paragraph(f"Financial report — {data['label']}", sub),
          Paragraph(f"Prepared for {who} · Generated on "
                    f"{date.today().strftime('%d %B %Y')} · Base currency: {user['base_currency']}",
                    small),
          HRFlowable(width="100%", thickness=1, color=line, spaceAfter=10)]

    summary = [["Income", "Expenses", "Savings", "Net"],
               [fmt_money(t["income"], symbol), fmt_money(t["expense"], symbol),
                fmt_money(t["savings"], symbol), fmt_money(net, symbol)]]
    tbl = Table(summary, colWidths=[43 * mm] * 4)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), accent),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TEXTCOLOR", (3, 1), (3, 1), colors.HexColor("#16A34A" if net >= 0 else "#DC2626")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, soft]),
        ("GRID", (0, 0), (-1, -1), 0.5, line),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    el += [tbl, Spacer(0, 12)]

    for fig_title, fig in figures:
        el.append(Paragraph(fig_title, h2))
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
        buf.seek(0)
        w_in, h_in = fig.get_size_inches()
        el.append(RLImage(buf, width=172 * mm, height=172 * mm * h_in / w_in))
        el.append(Spacer(0, 12))

    def cat_table(rows_):
        data_rows = [["Category", "Amount", "% of total", "Entries"]]
        for r in rows_:
            pct = (r["total"] / t["expense"] * 100) if t["expense"] else 0
            data_rows.append([r["name"], fmt_money(r["total"], symbol), f"{pct:.1f}%", str(r["n"])])
        tb = Table(data_rows, colWidths=[70 * mm, 45 * mm, 30 * mm, 27 * mm])
        tb.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), soft),
            ("TEXTCOLOR", (0, 0), (-1, 0), ink),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.4, line),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, soft]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
        return tb

    for key, heading in (("cat_exp", "Expenses by category"), ("cat_inc", "Income by category"),
                         ("cat_sav", "Savings by category")):
        if data[key]:
            el.append(Paragraph(heading, h2))
            el.append(cat_table(data[key]))
            el.append(Spacer(0, 10))

    el.append(Paragraph("Transactions", h2))
    txs = data["txs"]
    if not txs:
        el.append(Paragraph("No transactions in this period.", small))
    else:
        rows_ = [["Date", "Type", "Category", "Description", "Amount"]]
        for tx in txs[:400]:
            sign = {"income": "+", "expense": "-", "savings": "*"}[tx["type"]]
            rows_.append([tx["date"], tx["type"].capitalize(), tx["cat_name"] or "—",
                          tx["description"] or "—",
                          f"{sign}{fmt_money(tx['amount'], symbol)}"])
        if len(txs) > 400:
            rows_.append(["", "", "", f"(showing first 400 of {len(txs)})", ""])
        tb = Table(rows_, colWidths=[24 * mm, 22 * mm, 42 * mm, 62 * mm, 34 * mm], repeatRows=1)
        tb.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), accent),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (4, 0), (4, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.3, line),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, soft]),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
        el.append(tb)

    el += [Spacer(0, 14),
           Paragraph("Generated locally by Digital Wallet — your data never leaves this device.",
                     small)]
    doc.build(el)