"""
Split a PDF into sections based on its top-level bookmarks.
Outputs one PDF per top-level section into a subdirectory.
"""

import re
import sys
from pathlib import Path
import pypdf


def sanitize(title: str) -> str:
    """Make a title safe to use as a filename."""
    title = re.sub(r'[\\/:*?"<>|]', '_', title)
    title = re.sub(r'\s+', '_', title.strip())
    return title[:80]  # cap length


def get_top_level_sections(pdf: pypdf.PdfReader) -> list[dict]:
    """Return list of {title, start_page} for each top-level bookmark."""
    sections = []
    for item in pdf.outline:
        if isinstance(item, list):
            continue  # skip nested groups at top level
        try:
            page = pdf.get_destination_page_number(item)
            sections.append({"title": item.title, "start_page": page})
        except Exception:
            pass
    return sections


def split_pdf(input_path: str, output_dir: str | None = None) -> None:
    input_path = Path(input_path)
    if output_dir is None:
        output_dir = input_path.parent / (input_path.stem + "_sections")
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf = pypdf.PdfReader(str(input_path))
    total_pages = len(pdf.pages)
    sections = get_top_level_sections(pdf)

    if not sections:
        print("No top-level bookmarks found.")
        return

    print(f"Found {len(sections)} top-level sections. Splitting into {output_dir}/\n")

    for i, sec in enumerate(sections):
        start = sec["start_page"]
        end = sections[i + 1]["start_page"] if i + 1 < len(sections) else total_pages

        writer = pypdf.PdfWriter()
        for p in range(start, end):
            writer.add_page(pdf.pages[p])

        filename = f"{i+1:02d}_{sanitize(sec['title'])}.pdf"
        out_path = output_dir / filename
        with open(out_path, "wb") as f:
            writer.write(f)

        print(f"  [{i+1:2d}] pp.{start+1}-{end} ({end-start:3d} pages)  →  {filename}")

    print(f"\nDone. {len(sections)} files written to: {output_dir}")


if __name__ == "__main__":
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else \
        "/data/users/yyx/onProject/CHAI/EducAgent/assets/Pearl_2009_Causality.pdf"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else None
    split_pdf(pdf_path, out_dir)
