import os
from datetime import datetime
from models import TimeEntry
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def _generate_pdf_with_reportlab(path, title_lines, entries_lines):
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4
    margin = 40
    y = height - margin
    c.setFont("Helvetica-Bold", 14)
    for line in title_lines:
        c.drawString(margin, y, line)
        y -= 18
    y -= 6
    c.setFont("Helvetica", 10)
    lines_per_page = int((y - margin) / 14)
    line_count = 0
    for ln in entries_lines:
        if line_count >= lines_per_page:
            c.showPage()
            y = height - margin
            c.setFont("Helvetica", 10)
            line_count = 0
        c.drawString(margin, y, ln)
        y -= 14
        line_count += 1
    c.showPage()
    c.save()


def gerar_pdf_relatorio(emp, start, end):
    """
    Gera um PDF com os registros do funcionário entre start e end.
    Retorna o caminho para o arquivo gerado.
    """
    # diretório de saída
    proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    outdir = os.path.join(proj_root, 'temp')
    os.makedirs(outdir, exist_ok=True)
    filename = f"relatorio_{emp.id}_{start.strftime('%Y%m%d')}_{end.strftime('%Y%m%d')}.pdf"
    path = os.path.join(outdir, filename)

    # coletar registros do banco
    entries = TimeEntry.query.filter(
        TimeEntry.employee_id == emp.id,
        TimeEntry.timestamp >= start,
        TimeEntry.timestamp <= end
    ).order_by(TimeEntry.timestamp).all()

    title_lines = [
        f"Relatório de: {emp.name} ({emp.setor or '—'})",
        f"Período: {start.date()} a {end.date()}",
        f"Gerado em: {datetime.now().isoformat()}",
        ""
    ]

    if not entries:
        entries_lines = ["Nenhum registro encontrado no período."]
    else:
        entries_lines = [f"{e.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {e.entry_type}" for e in entries]

    # tenta gerar PDF com reportlab; se falhar, cria um arquivo texto com extensão .pdf
    try:
        _generate_pdf_with_reportlab(path, title_lines, entries_lines)
    except Exception:
        # fallback: arquivo texto com extensão .pdf
        with open(path, 'w', encoding='utf-8') as f:
            for l in title_lines:
                f.write(l + "\n")
            f.write("\n")
            for l in entries_lines:
                f.write(l + "\n")
    return path