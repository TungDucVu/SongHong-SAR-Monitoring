import os
import re
import subprocess

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

def parse_latex_to_html(tex_content):
    # Extract title, author, date
    title_match = re.search(r'\\title\{([\s\S]*?)\}\n\n?\\author', tex_content)
    author_match = re.search(r'\\author\{([\s\S]*?)\}\n\n?\\date', tex_content)
    date_match = re.search(r'\\date\{([\s\S]*?)\}\n\n?\\begin\{document\}', tex_content)

    title = title_match.group(1) if title_match else "BÁO CÁO PHÂN TÍCH KHOA HỌC"
    author = author_match.group(1) if author_match else "Vũ Đức Tùng"
    date = date_match.group(1) if date_match else "Tháng 7 năm 2026"

    # Clean LaTeX commands in title/author/date
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

    # Extract body after \begin{document}
    body_match = re.search(r'\\begin\{document\}([\s\S]*?)\\end\{document\}', tex_content)
    body = body_match.group(1) if body_match else tex_content

    # Remove \maketitle
    body = re.sub(r'\\maketitle', '', body)

    # Abstract
    def convert_abstract(m):
        content = m.group(1)
        return f'<div class="abstract"><h3>TÓM TẮT (ABSTRACT)</h3><p>{content}</p></div>'
    body = re.sub(r'\\begin\{abstract\}([\s\S]*?)\\end\{abstract\}', convert_abstract, body)

    # Convert sections & section counters
    sec_counts = [0, 0, 0]

    def sec_repl(m):
        nonlocal sec_counts
        sec_counts[0] += 1
        sec_counts[1] = 0
        sec_counts[2] = 0
        title = m.group(1).strip()
        return f'<h2 class="sec-title">{sec_counts[0]}. {title}</h2>'

    def subsec_repl(m):
        nonlocal sec_counts
        sec_counts[1] += 1
        sec_counts[2] = 0
        title = m.group(1).strip()
        return f'<h3 class="subsec-title">{sec_counts[0]}.{sec_counts[1]}. {title}</h3>'

    def subsubsec_repl(m):
        nonlocal sec_counts
        sec_counts[2] += 1
        title = m.group(1).strip()
        return f'<h4 class="subsubsec-title">{sec_counts[0]}.{sec_counts[1]}.{sec_counts[2]}. {title}</h4>'

    body = re.sub(r'\\section\{([\s\S]*?)\}', sec_repl, body)
    body = re.sub(r'\\subsection\{([\s\S]*?)\}', subsec_repl, body)
    body = re.sub(r'\\subsubsection\{([\s\S]*?)\}', subsubsec_repl, body)
    body = re.sub(r'\\paragraph\{([\s\S]*?)\}', r'<h5>\1</h5>', body)

    # Convert text formatting
    body = re.sub(r'\\textbf\{([\s\S]*?)\}', r'<strong>\1</strong>', body)
    body = re.sub(r'\\textit\{([\s\S]*?)\}', r'<em>\1</em>', body)
    body = re.sub(r'\\texttt\{([\s\S]*?)\}', r'<code>\1</code>', body)
    body = re.sub(r'\\hrule', '<hr>', body)
    body = re.sub(r'\\vspace\{[\s\S]*?\}', '', body)

    # Convert Subfigures & Figures
    def subfig_repl(m):
        sub_content = m.group(1)
        img = re.search(r'\\includegraphics\[.*?\]\{([\s\S]*?)\}', sub_content)
        cap = re.search(r'\\caption\{([\s\S]*?)\}', sub_content)
        img_src = img.group(1) if img else ""
        cap_txt = cap.group(1) if cap else ""
        return f'<div class="subfig"><img src="{img_src}" alt="Subfigure"><div class="subcaption">{cap_txt}</div></div>'

    def fig_repl(m):
        fig_content = m.group(1)
        # Parse subfigures if any
        subfigs_html = ""
        if '\\begin{subfigure}' in fig_content:
            subfigs = re.findall(r'\\begin\{subfigure\}[\s\S]*?\{([\s\S]*?)\\end\{subfigure\}', fig_content)
            sub_rendered = []
            for sf in subfigs:
                img = re.search(r'\\includegraphics\[.*?\]\{([\s\S]*?)\}', sf)
                cap = re.search(r'\\caption\{([\s\S]*?)\}', sf)
                img_src = img.group(1) if img else ""
                cap_txt = cap.group(1) if cap else ""
                sub_rendered.append(f'<div class="subfig"><img src="{img_src}"><div class="subcaption">{cap_txt}</div></div>')
            subfigs_html = f'<div class="subfig-row">{"".join(sub_rendered)}</div>'
        else:
            img = re.search(r'\\includegraphics\[.*?\]\{([\s\S]*?)\}', fig_content)
            img_src = img.group(1) if img else ""
            subfigs_html = f'<img src="{img_src}" class="fig-img">'

        cap = re.search(r'\\caption\{([\s\S]*?)\}', fig_content)
        cap_txt = cap.group(1) if cap else ""

        return f'<div class="figure-box">{subfigs_html}<div class="caption"><strong>Hình:</strong> {cap_txt}</div></div>'

    body = re.sub(r'\\begin\{figure\}[\s\S]*?([\s\S]*?)\\end\{figure\}', fig_repl, body)

    # Convert Tables & Tabular
    def table_repl(m):
        tbl_content = m.group(1)
        cap = re.search(r'\\caption\{([\s\S]*?)\}', tbl_content)
        cap_txt = cap.group(1) if cap else ""

        # Extract tabular
        tabular = re.search(r'\\begin\{tabular\}\{[\s\S]*?\}([\s\S]*?)\\end\{tabular\}', tbl_content)
        if not tabular:
            return ""
        lines = tabular.group(1).strip().split('\\\\')

        rows_html = []
        is_header = True
        for line in lines:
            line = line.replace('\\toprule', '').replace('\\midrule', '').replace('\\bottomrule', '').replace('\\hline', '').strip()
            if not line:
                continue
            cols = [c.strip() for c in line.split('&')]
            cell_tag = 'th' if is_header else 'td'
            cells = "".join([f'<{cell_tag}>{c}</{cell_tag}>' for c in cols])
            rows_html.append(f'<tr>{cells}</tr>')
            if is_header:
                is_header = False

        table_html = f'<table>{"".join(rows_html)}</table>'
        return f'<div class="table-box"><div class="table-caption"><strong>Bảng:</strong> {cap_txt}</div>{table_html}</div>'

    body = re.sub(r'\\begin\{table\}[\s\S]*?([\s\S]*?)\\end\{table\}', table_repl, body)

    # Convert Itemize & Enumerate
    def itemize_repl(m):
        items = re.findall(r'\\item\s*([\s\S]*?)(?=\\item|\Z)', m.group(1))
        lis = "".join([f'<li>{i.strip()}</li>' for i in items])
        return f'<ul>{lis}</ul>'

    def enum_repl(m):
        items = re.findall(r'\\item\s*([\s\S]*?)(?=\\item|\Z)', m.group(1))
        lis = "".join([f'<li>{i.strip()}</li>' for i in items])
        return f'<ol>{lis}</ol>'

    body = re.sub(r'\\begin\{itemize\}([\s\S]*?)\\end\{itemize\}', itemize_repl, body)
    body = re.sub(r'\\begin\{enumerate\}([\s\S]*?)\\end\{enumerate\}', enum_repl, body)

    # Convert Equations
    def eq_repl(m):
        eq_txt = m.group(1).strip()
        return f'<div class="equation">\\[ {eq_txt} \\]</div>'

    body = re.sub(r'\\begin\{equation\}([\s\S]*?)\\end\{equation\}', eq_repl, body)

    # Convert escapes and symbols
    body = body.replace('\\%', '%')
    body = body.replace('\\&', '&')
    body = body.replace('\\_', '_')
    body = body.replace('--', '–')
    body = body.replace('~', ' ')

    html_doc = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>{title_html}</title>
    <!-- MathJax for TeX math formulas -->
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <!-- Latin Modern / Computer Modern LaTeX Fonts -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/latin-modern-web@1.0.0/style/latin-modern.min.css">
    <style>
        @page {{
            size: A4 portrait;
            margin: 25mm 20mm 25mm 20mm;
        }}

        body {{
            font-family: 'Latin Modern Roman', 'Computer Modern Roman', 'Times New Roman', serif;
            color: #000000;
            line-height: 1.5;
            font-size: 11pt;
            background: #ffffff;
            margin: 0;
            padding: 20px 40px;
            text-align: justify;
        }}

        .doc-title {{
            text-align: center;
            font-size: 18pt;
            font-weight: bold;
            margin-bottom: 8px;
            line-height: 1.3;
        }}

        .doc-author {{
            text-align: center;
            font-size: 12pt;
            margin-bottom: 4px;
        }}

        .doc-date {{
            text-align: center;
            font-size: 10pt;
            color: #444444;
            margin-bottom: 24px;
        }}

        .abstract {{
            width: 90%;
            margin: 0 auto 24px auto;
            padding: 14px 20px;
            background: #fcfcfc;
            border: 1px solid #e0e0e0;
            font-size: 10pt;
            border-radius: 4px;
        }}

        .abstract h3 {{
            text-align: center;
            font-size: 11pt;
            margin-top: 0;
            margin-bottom: 8px;
            letter-spacing: 1px;
        }}

        h2.sec-title {{
            font-size: 14pt;
            font-weight: bold;
            color: #000000;
            border-bottom: 1.5px solid #000000;
            padding-bottom: 4px;
            margin-top: 24px;
            margin-bottom: 12px;
            page-break-after: avoid;
        }}

        h3.subsec-title {{
            font-size: 12pt;
            font-weight: bold;
            color: #111111;
            margin-top: 18px;
            margin-bottom: 8px;
            page-break-after: avoid;
        }}

        h4.subsubsec-title {{
            font-size: 11pt;
            font-weight: bold;
            color: #222222;
            margin-top: 14px;
            margin-bottom: 6px;
            page-break-after: avoid;
        }}

        h5 {{
            font-size: 11pt;
            font-weight: bold;
            margin-top: 10px;
            margin-bottom: 4px;
        }}

        p {{
            margin-bottom: 10px;
            text-indent: 1.5em;
        }}

        ul, ol {{
            margin-top: 6px;
            margin-bottom: 12px;
            padding-left: 28px;
        }}

        li {{
            margin-bottom: 4px;
        }}

        .table-box {{
            margin: 20px 0;
            text-align: center;
            page-break-inside: avoid;
        }}

        .table-caption {{
            font-size: 10pt;
            margin-bottom: 8px;
            font-weight: normal;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 0 auto;
            font-size: 10pt;
            border-top: 2px solid #000000;
            border-bottom: 2px solid #000000;
        }}

        th {{
            border-bottom: 1px solid #000000;
            padding: 8px 6px;
            font-weight: bold;
            text-align: center;
        }}

        td {{
            padding: 6px 6px;
            border-bottom: 1px solid #e0e0e0;
            text-align: center;
        }}

        .figure-box {{
            margin: 22px 0;
            text-align: center;
            page-break-inside: avoid;
        }}

        .fig-img {{
            max-width: 95%;
            height: auto;
            margin: 0 auto;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}

        .subfig-row {{
            display: flex;
            justify-content: space-around;
            gap: 16px;
            margin-bottom: 8px;
        }}

        .subfig {{
            flex: 1;
            text-align: center;
        }}

        .subfig img {{
            width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}

        .subcaption {{
            font-size: 9pt;
            color: #444444;
            margin-top: 4px;
        }}

        .caption {{
            font-size: 9.5pt;
            color: #222222;
            margin-top: 8px;
        }}

        .equation {{
            text-align: center;
            margin: 16px 0;
            font-size: 11pt;
        }}

        code {{
            font-family: 'Courier New', Courier, monospace;
            background: #f4f4f4;
            padding: 2px 4px;
            font-size: 9.5pt;
        }}

        hr {{
            border: none;
            border-top: 1px solid #cccccc;
            margin: 24px 0;
        }}
    </style>
</head>
<body>
    <div class="doc-title">{title_html}</div>
    <div class="doc-author">{author_html}</div>
    <div class="doc-date">{date_html}</div>
    <hr>
    {body}
</body>
</html>"""
    return html_doc

def main():
    browser = locate_browser()
    report_dir = os.path.abspath("REPORT")
    tex_file = os.path.join(report_dir, "bao_cao_giam_sat_song_hong.tex")
    html_out = os.path.join(report_dir, "bao_cao_giam_sat_song_hong_tex_styled.html")
    pdf_out = os.path.join(report_dir, "bao_cao_giam_sat_song_hong_tex.pdf")

    with open(tex_file, 'r', encoding='utf-8') as f:
        tex_content = f.read()

    html_rendered = parse_latex_to_html(tex_content)

    with open(html_out, 'w', encoding='utf-8') as f:
        f.write(html_rendered)
    print(f"[LaTeX Render] Converted .tex -> HTML: {html_out}")

    # Convert to PDF via Browser Headless
    cmd = [
        browser,
        '--headless',
        '--disable-gpu',
        '--no-sandbox',
        '--print-to-pdf-no-header',
        f'--print-to-pdf={pdf_out}',
        f'file:///{html_out}'
    ]
    print(f"[PDF Export] Generating LaTeX PDF -> '{pdf_out}'...")
    res = subprocess.run(cmd, capture_output=True, text=True)

    if os.path.exists(pdf_out) and os.path.getsize(pdf_out) > 0:
        print(f"  [OK] Successfully generated LaTeX PDF: {pdf_out} ({os.path.getsize(pdf_out):,} bytes)")
        # Also copy/overwrite bao_cao_giam_sat_song_hong.pdf if desired
        target_main_pdf = os.path.join(report_dir, "bao_cao_giam_sat_song_hong.pdf")
        with open(pdf_out, 'rb') as f_src:
            with open(target_main_pdf, 'wb') as f_dst:
                f_dst.write(f_src.read())
        print(f"  [OK] Updated primary report PDF: {target_main_pdf}")
    else:
        print(f"  [ERROR] PDF export failed. Stderr: {res.stderr}")

if __name__ == "__main__":
    main()
