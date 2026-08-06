import os
import re
import subprocess
import mistune

def locate_browser():
    paths = [
        r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
        r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    raise RuntimeError("Neither Edge nor Chrome browser binary was found on this system.")

def convert_html_to_pdf(browser_bin, html_file, pdf_file, landscape=False):
    html_abs = os.path.abspath(html_file)
    pdf_abs = os.path.abspath(pdf_file)
    
    cmd = [
        browser_bin,
        '--headless',
        '--disable-gpu',
        '--no-sandbox',
        '--print-to-pdf-no-header',
        f'--print-to-pdf={pdf_abs}'
    ]
    if landscape:
        cmd.append('--landscape')
    cmd.append(f'file:///{html_abs}')
    
    print(f"[PDF Export] Converting '{os.path.basename(html_file)}' -> '{os.path.basename(pdf_file)}'...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(pdf_abs) and os.path.getsize(pdf_abs) > 0:
        print(f"  [OK] Successfully generated: {pdf_abs} ({os.path.getsize(pdf_abs):,} bytes)")
        return True
    else:
        print(f"  [ERROR] Failed to generate PDF. Stderr: {res.stderr}")
        return False

def md_to_styled_html(md_path, html_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    alert_types = {
        'IMPORTANT': ('#dc2626', 'QUAN TRỌNG', '#fef2f2'),
        'NOTE': ('#0284c7', 'LƯU Ý', '#f0f9ff'),
        'TIP': ('#059669', 'MẸO', '#ecfdf5'),
        'WARNING': ('#d97706', 'CẢNH BÁO', '#fffbeb'),
        'CAUTION': ('#dc2626', 'CHÚ Ý', '#fef2f2')
    }

    def replace_alert(match):
        atype = match.group(1).upper()
        content = match.group(2).strip()
        color, tag, bg = alert_types.get(atype, ('#0284c7', 'LƯU Ý', '#f0f9ff'))
        return f'<div class="alert-box" style="border-left: 5px solid {color}; background-color: {bg}; padding: 14px 18px; margin: 18px 0; border-radius: 6px;"><strong>[{atype}]</strong> {content}</div>'

    md_text = re.sub(r'>\s*\[!(IMPORTANT|NOTE|TIP|WARNING|CAUTION)\][ \t]*\n((?:>[^\n]+\n?)+)', replace_alert, md_text)
    md_text = re.sub(r'>\s*\[!(IMPORTANT|NOTE|TIP|WARNING|CAUTION)\][ \t]*(.*)', replace_alert, md_text)

    html_body = mistune.html(md_text)

    styled_document = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Báo Cáo Phân Tích Khoa Học V2 - Giám Sát Sông Hồng SAR (2017 - 2026)</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400&family=Lexend:wght@600;700;800&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
    <style>
        @page {{ size: A4 portrait; margin: 20mm 15mm 20mm 15mm; }}
        body {{
            font-family: 'Be Vietnam Pro', system-ui, -apple-system, sans-serif;
            color: #0f172a;
            line-height: 1.65;
            font-size: 10.5pt;
            background: #ffffff;
            margin: 0;
            padding: 20px 40px;
        }}
        h1 {{ font-family: 'Lexend', sans-serif; font-size: 20pt; font-weight: 800; color: #0284c7; text-align: center; margin-top: 10px; margin-bottom: 8px; line-height: 1.3; }}
        h2 {{ font-family: 'Lexend', sans-serif; font-size: 14pt; font-weight: 700; color: #0369a1; border-bottom: 2px solid #e2e8f0; padding-bottom: 6px; margin-top: 24px; margin-bottom: 12px; }}
        h3 {{ font-family: 'Lexend', sans-serif; font-size: 12pt; font-weight: 700; color: #0f172a; margin-top: 18px; margin-bottom: 8px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 9.5pt; page-break-inside: avoid; }}
        th, td {{ border: 1px solid #cbd5e1; padding: 8px 10px; text-align: left; }}
        th {{ background-color: #f1f5f9; font-weight: 700; color: #0f172a; }}
        img {{ max-width: 100%; height: auto; display: block; margin: 16px auto; border-radius: 6px; border: 1px solid #e2e8f0; page-break-inside: avoid; }}
        blockquote {{ background-color: #f8fafc; border-left: 4px solid #0284c7; margin: 16px 0; padding: 12px 18px; font-style: italic; color: #334155; }}
        code {{ font-family: 'JetBrains Mono', monospace; background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: 9pt; }}
    </style>
</head>
<body>
    {html_body}
</body>
</html>"""

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(styled_document)
    print(f"[HTML Export] Generated: {html_path}")

def parse_latex_to_html(tex_content):
    # Standard LaTeX to HTML parser for styled preview
    title_match = re.search(r'\\title\{([\s\S]*?)\}\n\n?\\author', tex_content)
    author_match = re.search(r'\\author\{([\s\S]*?)\}\n\n?\\date', tex_content)
    date_match = re.search(r'\\date\{([\s\S]*?)\}\n\n?\\begin\{document\}', tex_content)

    title = title_match.group(1) if title_match else "BÁO CÁO PHÂN TÍCH KHOA HỌC"
    author = author_match.group(1) if author_match else "Vũ Đức Tùng"
    date = date_match.group(1) if date_match else "Tháng 7 năm 2026"

    def clean_latex(text):
        text = re.sub(r'\\textbf\{([\s\S]*?)\}', r'<strong>\1</strong>', text)
        text = re.sub(r'\\textit\{([\s\S]*?)\}', r'<em>\1</em>', text)
        text = re.sub(r'\\LARGE', '', text)
        text = re.sub(r'\\Large', '', text)
        text = re.sub(r'\\small', '', text)
        text = re.sub(r'\\\[[\d\.]+em\]', '<br>', text)
        text = re.sub(r'\\\\', '<br>', text)
        return text

    title_html = clean_latex(title)
    author_html = clean_latex(author)
    date_html = clean_latex(date)

    body_match = re.search(r'\\begin\{document\}([\s\S]*?)\\end\{document\}', tex_content)
    body = body_match.group(1) if body_match else tex_content
    body = re.sub(r'\\maketitle', '', body)

    def convert_abstract(m):
        content = m.group(1)
        return f'<div class="abstract"><h3>TÓM TẮT (ABSTRACT)</h3><p>{content}</p></div>'
    body = re.sub(r'\\begin\{abstract\}([\s\S]*?)\\end\{abstract\}', convert_abstract, body)

    sec_counts = [0, 0, 0]
    def sec_repl(m):
        nonlocal sec_counts
        sec_counts[0] += 1
        sec_counts[1] = 0
        sec_counts[2] = 0
        return f'<h2 class="sec-title">{sec_counts[0]}. {m.group(1).strip()}</h2>'

    def subsec_repl(m):
        nonlocal sec_counts
        sec_counts[1] += 1
        sec_counts[2] = 0
        return f'<h3 class="subsec-title">{sec_counts[0]}.{sec_counts[1]}. {m.group(1).strip()}</h3>'

    body = re.sub(r'\\section\*\{([\s\S]*?)\}', r'<h2 class="sec-title" style="color: #dc2626;">\1</h2>', body)
    body = re.sub(r'\\section\{([\s\S]*?)\}', sec_repl, body)
    body = re.sub(r'\\subsection\{([\s\S]*?)\}', subsec_repl, body)

    body = re.sub(r'\\textbf\{([\s\S]*?)\}', r'<strong>\1</strong>', body)
    body = re.sub(r'\\textit\{([\s\S]*?)\}', r'<em>\1</em>', body)
    body = re.sub(r'\\texttt\{([\s\S]*?)\}', r'<code>\1</code>', body)
    body = re.sub(r'\\hrule', '<hr>', body)
    body = re.sub(r'\\vspace\{[\s\S]*?\}', '', body)

    def quote_repl(m):
        return f'<blockquote style="background: #fdf2f2; border-left: 4px solid #dc2626; padding: 12px 18px; margin: 16px 0; font-style: italic;">{m.group(1)}</blockquote>'
    body = re.sub(r'\\begin\{quote\}([\s\S]*?)\\end\{quote\}', quote_repl, body)

    def table_repl(m):
        tbl_content = m.group(1)
        cap = re.search(r'\\caption\{([\s\S]*?)\}', tbl_content)
        caption_txt = cap.group(1) if cap else ""

        rows_match = re.search(r'\\begin\{tabular\}[\s\S]*?\}([\s\S]*?)\\end\{tabular\}', tbl_content)
        if not rows_match:
            return tbl_content
        raw_rows = rows_match.group(1).strip().split(r'\\')
        
        html_rows = []
        is_first = True
        for row in raw_rows:
            row = re.sub(r'\\toprule|\\midrule|\\bottomrule|\\hline', '', row).strip()
            if not row:
                continue
            cols = [re.sub(r'\\textbf\{([\s\S]*?)\}', r'<strong>\1</strong>', c.strip()) for c in row.split('&')]
            if is_first:
                cell_tag = 'th'
                is_first = False
            else:
                cell_tag = 'td'
            row_html = "".join([f'<{cell_tag}>{c}</{cell_tag}>' for c in cols])
            html_rows.append(f'<tr>{row_html}</tr>')
        
        caption_html = f'<div class="table-caption" style="font-weight: 700; margin-bottom: 6px;">{caption_txt}</div>' if caption_txt else ""
        return f'<div class="table-container">{caption_html}<table>{"".join(html_rows)}</table></div>'

    body = re.sub(r'\\begin\{table\}([\s\S]*?)\\end\{table\}', table_repl, body)

    def fig_repl(m):
        fig_content = m.group(1)
        img = re.search(r'\\includegraphics\[.*?\]\{([\s\S]*?)\}', fig_content)
        cap = re.search(r'\\caption\{([\s\S]*?)\}', fig_content)
        img_src = img.group(1) if img else ""
        cap_txt = cap.group(1) if cap else ""
        return f'<div class="fig-box"><img src="{img_src}" alt="Figure"><div class="caption">{cap_txt}</div></div>'

    body = re.sub(r'\\begin\{figure\}([\s\S]*?)\\end\{figure\}', fig_repl, body)

    def itemize_repl(m):
        items = re.findall(r'\\item\s+([\s\S]*?)(?=\\item|\Z)', m.group(1))
        lis = "".join([f'<li>{it.strip()}</li>' for it in items])
        return f'<ul>{lis}</ul>'

    def enumerate_repl(m):
        items = re.findall(r'\\item\s+([\s\S]*?)(?=\\item|\Z)', m.group(1))
        lis = "".join([f'<li>{it.strip()}</li>' for it in items])
        return f'<ol>{lis}</ol>'

    body = re.sub(r'\\begin\{itemize\}([\s\S]*?)\\end\{itemize\}', itemize_repl, body)
    body = re.sub(r'\\begin\{enumerate\}([\s\S]*?)\\end\{enumerate\}', enumerate_repl, body)

    html_doc = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>{title_html}</title>
    <link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&family=Lexend:wght@700;800&display=swap" rel="stylesheet">
    <style>
        @page {{ size: A4 portrait; margin: 20mm 15mm 20mm 15mm; }}
        body {{ font-family: 'Be Vietnam Pro', sans-serif; color: #0f172a; line-height: 1.6; font-size: 10pt; padding: 20px 40px; }}
        h1 {{ font-family: 'Lexend', sans-serif; color: #0284c7; text-align: center; font-size: 18pt; margin-bottom: 6px; }}
        .author-box {{ text-align: center; font-size: 11pt; margin-bottom: 20px; color: #475569; }}
        .abstract {{ background: #f8fafc; border-left: 4px solid #0284c7; padding: 14px; margin-bottom: 20px; border-radius: 4px; }}
        h2.sec-title {{ font-family: 'Lexend', sans-serif; font-size: 13pt; color: #0369a1; border-bottom: 1.5px solid #cbd5e1; padding-bottom: 4px; margin-top: 20px; }}
        h3.subsec-title {{ font-family: 'Lexend', sans-serif; font-size: 11pt; color: #0f172a; margin-top: 14px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 14px 0; font-size: 9pt; }}
        th, td {{ border: 1px solid #cbd5e1; padding: 6px 8px; text-align: left; }}
        th {{ background: #f1f5f9; font-weight: 700; }}
        .fig-box {{ text-align: center; margin: 16px 0; page-break-inside: avoid; }}
        .fig-box img {{ max-width: 95%; border-radius: 4px; border: 1px solid #e2e8f0; }}
        .caption {{ font-size: 8.5pt; color: #64748b; margin-top: 4px; font-style: italic; }}
    </style>
</head>
<body>
    <h1>{title_html}</h1>
    <div class="author-box">{author_html} | {date_html}</div>
    {body}
</body>
</html>"""
    return html_doc

def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    report_v2_dir = os.path.join(base_dir, 'report_v2')
    
    browser_bin = locate_browser()
    print(f"Using browser: {browser_bin}")
    
    # 1. MD -> HTML -> PDF
    md_file = os.path.join(report_v2_dir, 'bao_cao_giam_sat_song_hong.md')
    md_html = os.path.join(report_v2_dir, 'bao_cao_giam_sat_song_hong_styled.html')
    md_pdf = os.path.join(report_v2_dir, 'bao_cao_giam_sat_song_hong.pdf')
    if os.path.exists(md_file):
        md_to_styled_html(md_file, md_html)
        convert_html_to_pdf(browser_bin, md_html, md_pdf)
    
    # 2. TEX -> HTML -> PDF
    tex_file = os.path.join(report_v2_dir, 'bao_cao_giam_sat_song_hong.tex')
    tex_html = os.path.join(report_v2_dir, 'bao_cao_giam_sat_song_hong_tex_styled.html')
    tex_pdf = os.path.join(report_v2_dir, 'bao_cao_giam_sat_song_hong_tex.pdf')
    if os.path.exists(tex_file):
        with open(tex_file, 'r', encoding='utf-8') as f:
            tex_content = f.read()
        parsed_html = parse_latex_to_html(tex_content)
        with open(tex_html, 'w', encoding='utf-8') as f:
            f.write(parsed_html)
        print(f"[LaTeX HTML Export] Generated: {tex_html}")
        convert_html_to_pdf(browser_bin, tex_html, tex_pdf)

    # 3. Slide HTML -> PDF
    slide_html = os.path.join(report_v2_dir, 'slide_bao_cao_thuc_tap.html')
    slide_pdf = os.path.join(report_v2_dir, 'slide_bao_cao_thuc_tap.pdf')
    if os.path.exists(slide_html):
        convert_html_to_pdf(browser_bin, slide_html, slide_pdf, landscape=True)

if __name__ == '__main__':
    main()
