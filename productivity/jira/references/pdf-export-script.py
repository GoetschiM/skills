#!/usr/bin/env python3
"""
Jira Ticket -> PDF Export Script
Usage: python3 /path/to/this/script.py
Requires: fpdf2 (pip install fpdf2 --break-system-packages)

Steps before running:
  1. source /opt/data/home/.hermes/.env
  2. curl .../issue/GL-XXX?fields=summary,description,status,... -o /tmp/jira_issue.json
"""

import json, re
from fpdf import FPDF

FONT_DIR = '/usr/share/fonts/truetype/dejavu/'
KEY_MAP = {
    '\U0001f3af': '[ZIEL]', '\U0001f4cb': '[LISTE]', '\U0001f9e9': '[STRUKTUR]',
    '\U0001f3d7': '[BAU]',  '\U0001f4ce': '[ANHANG]', '\U0001f4cc': '[PIN]',
    '\U0001f680': '[GO]',   '\u2705':     '[OK]',      '\u274c':     '[FAIL]',
    '\u2014':  ' - ',       '\u2022':     ' * ',       '\u2026':    '...',
}
def clean(t):
    for k, v in KEY_MAP.items():
        t = t.replace(k, v)
    return t

def extract_adf(node):
    parts = []
    if isinstance(node, dict):
        content = node.get('content', [])
        if node.get('type') == 'text':
            parts.append(node.get('text', ''))
        for child in content:
            parts.append(extract_adf(child))
        if node.get('type') == 'paragraph':
            parts.append('\n')
        elif node.get('type') == 'heading':
            parts.append('\n')
    elif isinstance(node, str):
        parts.append(node)
    return ''.join(parts)

# Load
d = json.load(open('/tmp/jira_issue.json'))
f = d['fields']
key = d['key']
summary = clean(f['summary'])
status = f['status']['name']
itype = f['issuetype']['name']
priority = f['priority']['name']
created = f['created'][:16]
desc_text = clean(extract_adf(f.get('description', {})))

# PDF
pdf = FPDF()
pdf.add_font('DJVN', '', FONT_DIR + 'DejaVuSans.ttf')
pdf.add_font('DJVN', 'B', FONT_DIR + 'DejaVuSans-Bold.ttf')
pdf.add_page()

# Header
pdf.set_font('DJVN', 'B', 22)
pdf.set_text_color(20, 40, 90)
pdf.cell(0, 12, key)
pdf.ln(5)
pdf.set_font('DJVN', '', 14)
pdf.set_text_color(60, 60, 60)
pdf.multi_cell(0, 7, summary)
pdf.ln(4)

# Meta
pdf.set_font('DJVN', '', 9)
pdf.set_text_color(80, 80, 80)
pdf.cell(0, 5, f'Status: {status}  |  Typ: {itype}  |  Prioritaet: {priority}')
pdf.ln(5)
pdf.cell(0, 5, f'Erstellt: {created}')
pdf.ln(8)

# Line
pdf.set_draw_color(30, 60, 120)
pdf.set_line_width(0.5)
pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y())
pdf.ln(6)

# Description
pdf.set_font('DJVN', 'B', 12)
pdf.set_text_color(30, 60, 120)
pdf.cell(0, 8, 'Beschreibung')
pdf.ln(7)
pdf.set_font('DJVN', '', 10)
pdf.set_text_color(30, 30, 30)
pdf.multi_cell(0, 5, desc_text)

out = f'/tmp/{key}_export.pdf'
pdf.output(out)
print(f'PDF: {out}')
