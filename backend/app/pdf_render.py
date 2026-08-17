from pathlib import Path

from fpdf import FPDF


class BriefPDF(FPDF):
    def header(self) -> None:
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(30, 95, 138)
        self.cell(0, 8, "Second Shift", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(90, 101, 119)
        self.cell(
            0,
            5,
            "Organises notes. Not a medical device. Not medical advice.",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        self.ln(2)

    def footer(self) -> None:
        self.set_y(-12)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")


def _ascii(text: str) -> str:
    return (
        text.replace("“", '"')
        .replace("”", '"')
        .replace("‘", "'")
        .replace("’", "'")
        .replace("–", ", ")
        .replace("—", ". ")
        .encode("latin-1", "replace")
        .decode("latin-1")
    )


def write_pdf(markdown: str, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    pdf = BriefPDF()
    pdf.set_margins(16, 16, 16)
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()
    pdf.set_text_color(26, 35, 50)
    usable = pdf.w - pdf.l_margin - pdf.r_margin
    for raw in markdown.splitlines():
        line = _ascii(raw).replace("**", "")
        if line.startswith("# "):
            pdf.set_font("Helvetica", "B", 16)
            pdf.multi_cell(usable, 8, line[2:])
        elif line.startswith("## "):
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(30, 95, 138)
            pdf.multi_cell(usable, 7, line[3:])
            pdf.set_text_color(26, 35, 50)
        elif line.startswith("- ") or line.startswith("  - "):
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(usable, 5.5, f"  {line.lstrip()}")
        elif line.strip() == "":
            pdf.ln(2)
        else:
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(usable, 5.5, line)
    pdf.output(path)
