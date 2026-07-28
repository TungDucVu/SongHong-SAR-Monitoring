import os
import re
import shutil
import zipfile

def package_latex():
    tex_path = 'outputs/REPORT/bao_cao_giam_sat_song_hong.tex'
    pkg_dir = 'outputs/latex_package'
    zip_path = 'outputs/latex_package.zip'

    with open(tex_path, 'r', encoding='utf-8') as f:
        tex_content = f.read()

    # Extract all figure references
    fig_paths = re.findall(r'\\includegraphics(?:\[.*?\])?\{([\s\S]*?)\}', tex_content)
    fig_paths = sorted(list(set(fig_paths)))

    os.makedirs(pkg_dir, exist_ok=True)
    os.makedirs(os.path.join(pkg_dir, 'figures'), exist_ok=True)

    # Copy tex source
    shutil.copy(tex_path, os.path.join(pkg_dir, 'bao_cao_giam_sat_song_hong.tex'))

    # Copy images
    copied = 0
    for fig_rel in fig_paths:
        src_fig = os.path.join('outputs/REPORT', fig_rel)
        dst_fig = os.path.join(pkg_dir, fig_rel)
        os.makedirs(os.path.dirname(dst_fig), exist_ok=True)
        if os.path.exists(src_fig):
            shutil.copy(src_fig, dst_fig)
            copied += 1

    # Create ZIP archive
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(pkg_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, os.path.dirname(pkg_dir))
                zipf.write(full_path, rel_path)

    print(f"[OK] LaTeX package created in '{pkg_dir}/' with {copied} figure images.")
    print(f"[OK] Zip archive created at '{zip_path}'.")

if __name__ == "__main__":
    package_latex()
