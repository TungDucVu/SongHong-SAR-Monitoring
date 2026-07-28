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
        f'--print-to-pdf={pdf_abs}',
        f'file:///{html_abs}'
    ]
    
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

    # Pre-process GitHub alerts: > [!IMPORTANT] etc.
    alert_types = {
        'IMPORTANT': ('var(--accent-red, #dc2626)', 'quan-trong', '#fef2f2'),
        'NOTE': ('var(--accent-blue, #0284c7)', 'luu-y', '#f0f9ff'),
        'TIP': ('var(--accent-emerald, #059669)', 'meo', '#ecfdf5'),
        'WARNING': ('var(--accent-amber, #d97706)', 'canh-bao', '#fffbeb'),
        'CAUTION': ('var(--accent-red, #dc2626)', 'chu-y', '#fef2f2')
    }

    def replace_alert(match):
        atype = match.group(1).upper()
        content = match.group(2).strip()
        color, tag, bg = alert_types.get(atype, ('#0284c7', 'LUU Y', '#f0f9ff'))
        return f'<div class="alert-box" style="border-left: 5px solid {color}; background-color: {bg}; padding: 14px 18px; margin: 18px 0; border-radius: 6px;"><strong>[{atype}]</strong> {content}</div>'

    md_text = re.sub(r'>\s*\[!(IMPORTANT|NOTE|TIP|WARNING|CAUTION)\][ \t]*\n((?:>[^\n]+\n?)+)', replace_alert, md_text)
    md_text = re.sub(r'>\s*\[!(IMPORTANT|NOTE|TIP|WARNING|CAUTION)\][ \t]*(.*)', replace_alert, md_text)

    # Convert Markdown to HTML via mistune
    html_body = mistune.html(md_text)

    styled_document = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Báo Cáo Phân Tích Khoa Học - Giám Sát Sông Hồng SAR (2017 - 2026)</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400&family=Lexend:wght@600;700;800&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
    <style>
        @page {{
            size: A4 portrait;
            margin: 20mm 15mm 20mm 15mm;
        }}
        
        body {{
            font-family: 'Be Vietnam Pro', system-ui, -apple-system, sans-serif;
            color: #0f172a;
            line-height: 1.65;
            font-size: 10.5pt;
            background: #ffffff;
            margin: 0;
            padding: 20px 40px;
        }}

        h1 {{
            font-family: 'Lexend', sans-serif;
            font-size: 22pt;
            font-weight: 800;
            color: #0284c7;
            text-align: center;
            margin-top: 10px;
            margin-bottom: 8px;
            line-height: 1.3;
        }}

        h2 {{
            font-family: 'Lexend', sans-serif;
            font-size: 15pt;
            font-weight: 800;
            color: #0f172a;
            border-bottom: 2px solid #0284c7;
            padding-bottom: 6px;
            margin-top: 24px;
            margin-bottom: 12px;
            page-break-after: avoid;
        }}

        h3 {{
            font-family: 'Lexend', sans-serif;
            font-size: 12pt;
            font-weight: 700;
            color: #0369a1;
            margin-top: 18px;
            margin-bottom: 8px;
            page-break-after: avoid;
        }}

        h4, h5 {{
            font-family: 'Lexend', sans-serif;
            font-size: 11pt;
            font-weight: 700;
            color: #334155;
            margin-top: 14px;
            margin-bottom: 6px;
            page-break-after: avoid;
        }}

        p {{
            margin-bottom: 10px;
            text-align: justify;
        }}

        blockquote {{
            background: #f8fafc;
            border-left: 4px solid #0284c7;
            margin: 14px 0;
            padding: 10px 16px;
            font-style: normal;
            color: #334155;
            border-radius: 4px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
            font-size: 9.5pt;
            page-break-inside: avoid;
        }}

        th {{
            background-color: #0284c7;
            color: #ffffff;
            font-weight: 700;
            text-align: center;
            padding: 8px 10px;
            border: 1px solid #0284c7;
        }}

        td {{
            padding: 7px 9px;
            border: 1px solid #cbd5e1;
            text-align: center;
        }}

        tr:nth-child(even) {{
            background-color: #f8fafc;
        }}

        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 14px auto;
            border-radius: 6px;
            border: 1px solid #e2e8f0;
            page-break-inside: avoid;
        }}

        em {{
            display: block;
            text-align: center;
            font-size: 9pt;
            color: #64748b;
            margin-top: -6px;
            margin-bottom: 14px;
            font-style: italic;
        }}

        code {{
            font-family: 'JetBrains Mono', monospace;
            background: #f1f5f9;
            color: #0f172a;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 9pt;
        }}

        pre {{
            background: #0f172a;
            color: #f8fafc;
            padding: 14px;
            border-radius: 8px;
            overflow-x: auto;
            font-size: 9pt;
            line-height: 1.45;
            page-break-inside: avoid;
        }}

        pre code {{
            background: transparent;
            color: inherit;
            padding: 0;
        }}

        hr {{
            border: none;
            border-top: 1px solid #e2e8f0;
            margin: 20px 0;
        }}

        .alert-box {{
            page-break-inside: avoid;
        }}
    </style>
</head>
<body>
{html_body}
</body>
</html>"""

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(styled_document)
    print(f"[HTML Render] Created styled HTML report: {html_path}")

def main():
    browser = locate_browser()
    print(f"[Browser Found] Using: {browser}")

    report_dir = os.path.abspath("outputs/REPORT")
    os.makedirs(report_dir, exist_ok=True)

    # 1. Generate PDF for Slides
    slide_html = os.path.join(report_dir, "slide_bao_cao_thuc_tap.html")
    slide_pdf = os.path.join(report_dir, "slide_bao_cao_thuc_tap.pdf")
    if os.path.exists(slide_html):
        convert_html_to_pdf(browser, slide_html, slide_pdf, landscape=True)

    # 2. Generate PDF for Markdown Report
    md_report = os.path.join(report_dir, "bao_cao_giam_sat_song_hong.md")
    report_html = os.path.join(report_dir, "bao_cao_giam_sat_song_hong_styled.html")
    report_pdf = os.path.join(report_dir, "bao_cao_giam_sat_song_hong.pdf")
    
    if os.path.exists(md_report):
        md_to_styled_html(md_report, report_html)
        convert_html_to_pdf(browser, report_html, report_pdf, landscape=False)

    print("\n=============================================================")
    print(" ALL PDF REPORTS GENERATED SUCCESSFULLY IN outputs/REPORT/")
    print("=============================================================")

if __name__ == "__main__":
    main()
