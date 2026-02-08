#!/usr/bin/env python3
import argparse
import json
import pathlib
import shutil
import subprocess
import sys

LATEX_SPECIALS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def latex_escape(value: str) -> str:
    return "".join(LATEX_SPECIALS.get(ch, ch) for ch in value)


def latex_escape_keep_newlines(value: str) -> str:
    placeholder = "__LATEX_LINEBREAK__"
    value = value.replace("\\\\", placeholder)
    escaped = latex_escape(value)
    return escaped.replace(placeholder, "\\\\")


def format_bullets(bullets):
    return " \\newline\n".join(f"- {latex_escape(item)}" for item in bullets)


def roman_numeral(index: int) -> str:
    roman_map = [
        (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
        (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
    ]
    value = index
    result = []
    for arabic, roman in roman_map:
        while value >= arabic:
            result.append(roman)
            value -= arabic
    return "".join(result)


def format_projects(projects):
    blocks = []
    for project in projects:
        topic = latex_escape(project["topic"])
        start = project["start"]
        end = project["end"]
        entries = []
        for idx, item in enumerate(project["items"], start=1):
            numeral = roman_numeral(idx)
            title = latex_escape(item["title"])
            text = latex_escape(item["text"])
            entries.append(f"{numeral}. \\textbf{{{title}:}} {text}")
        entry_text = " \\newline\n".join(entries)
        blocks.append(
            "\\cventry"
            f"{{{start} -- {end}}}"
            f"{{\\topic{{{topic}}}}}"
            "{}{}{}"
            f"{{\n    {entry_text}\n}}"
        )
    return "\n\n".join(blocks)


def render_resume(data):
    personal = data["personal"]
    summary = latex_escape(data["summary"])

    tech_skills = " \\newline\n        ".join(latex_escape(item) for item in data["skills"]["technical"])
    leader_skills = " \\newline\n        ".join(latex_escape(item) for item in data["skills"]["leadership"])

    experience_blocks = []
    for entry in data["experience"]:
        start = entry["start"]
        end = entry["end"]
        role = latex_escape(entry["role"])
        org = latex_escape(entry["org"])
        bullets = format_bullets(entry["bullets"])
        experience_blocks.append(
            "\\cventry"
            f"{{{start} -- {end}}}"
            f"{{{role}}}"
            f"{{{org}}}"
            "{}{}"
            f"{{\n{bullets}\n}}"
        )

    education_blocks = []
    for entry in data["education"]:
        year = entry["year"]
        degree = latex_escape(entry["degree"])
        institution = latex_escape(entry["institution"])
        location = latex_escape(entry["location"])
        education_blocks.append(
            f"\\cventry{{{year}}}{{{degree}}}{{{institution}}}{{{location}}}{{}}{{}}"
        )

    certification_blocks = []
    for entry in data["certifications"]:
        year = entry["year"]
        title = latex_escape(entry["title"])
        issuer = latex_escape(entry["issuer"])
        location = latex_escape(entry.get("location", ""))
        url = entry.get("url")
        if url:
            title = f"\\href{{{url}}}{{``{title}''}}"
        certification_blocks.append(
            f"\\cventry{{{year}}}{{{title}}}{{{issuer}}}{{{location}}}{{}}{{}}"
        )

    language_line = ", ".join(latex_escape(lang) for lang in data["languages"])

    references_note = data.get("references_note")
    reference_columns = []
    for entry in data.get("references", []):
        if entry.get("hidden"):
            continue
        name = latex_escape(entry["name"])
        details = latex_escape_keep_newlines(entry["details"])
        reference_columns.append(f"    \\cvcolumn{{{name}}}{{{details}}}")
    reference_block = "\n".join(reference_columns)

    projects_block = format_projects(data["projects"])
    experience_block = "\n\n".join(experience_blocks)
    education_block = "\n".join(education_blocks)
    certification_block = "\n".join(certification_blocks)

    title = latex_escape_keep_newlines(personal["title"])
    email = latex_escape(personal["email"])
    homepage = latex_escape(personal["homepage"])
    linkedin = latex_escape(personal["linkedin"])
    address = latex_escape(personal["address"])
    mobile = latex_escape(personal["mobile"])
    base_dir = pathlib.Path(__file__).resolve().parents[1]
    photo_path = pathlib.Path(personal["photo"])
    if not photo_path.is_absolute():
        photo_path = (base_dir / photo_path).resolve()
    photo = latex_escape(str(photo_path))

    if references_note:
        references_section = f"\\section{{References}}\n{latex_escape(references_note)}"
    elif reference_block:
        references_section = "\\section{References}\n\n\\begin{cvcolumns}\n" + reference_block + "\n\\end{cvcolumns}"
    else:
        references_section = "\\section{References}\n"

    graphicspath = "\\graphicspath{{Files/}{../}{./}}"

    return f"""\\documentclass[a4paper]{{moderncv}}
\\moderncvtheme[blue]{{classic}}

\\usepackage[scale=0.86]{{geometry}}
\\usepackage{{soul}}
\\usepackage{{xcolor}}
{graphicspath}
\\usepackage{{fontawesome5}}\\newcommand{{\\topic}}[1]{{\\textbf{{\\textsc{{#1}}}}}}
\\newcommand{{\\eubadge}}{{\\raisebox{{-0.25ex}}{{\\colorbox[HTML]{{003399}}{{\\textcolor[HTML]{{FFCC00}}{{\\scriptsize *****}}}}}}}}

\\firstname{{{latex_escape(personal["firstname"])}}}
\\familyname{{{latex_escape(personal["familyname"])}}}
\\title{{{title}}}
\\email{{{email}}}
\\homepage{{{homepage}}}
\\social[linkedin]{{{linkedin}}}
\\address{{{address}}}{{}}{{}}
\\mobile{{{mobile}}}
\\photo[40pt]{{{photo}}}

\\begin{{document}}
\\maketitle

\\section{{Professional Summary}}
{summary}

\\section{{Technical \\& Leadership Skills}}

\\noindent
\\begin{{minipage}}[t]{{0.49\\textwidth}}
    \\textbf{{Technical Skills}}\\par\\medskip
        {tech_skills}
    \\end{{minipage}}\\hfill
    \\begin{{minipage}}[t]{{0.49\\textwidth}}
    \\textbf{{Leadership Skills}}\\par\\medskip
        {leader_skills}
\\end{{minipage}}

\\section{{Professional Experience}}

{experience_block}

\\section{{Selected Projects \\& Research}}

{projects_block}

\\section{{Degree Qualifications}}
{education_block}

\\section{{Certifications \\& Training}}
{certification_block}

\\section{{Languages}}
{language_line}

{references_section}

\\end{{document}}
"""


def write_tex(content: str, output_path: pathlib.Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_pdf(tex_path: pathlib.Path, pdf_path: pathlib.Path) -> None:
    latexmk = shutil.which("latexmk")
    if not latexmk:
        raise RuntimeError("latexmk not found. Install TeX Live or MiKTeX with latexmk.")

    output_dir = pdf_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    aux_dir = output_dir / ".latex"
    aux_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        latexmk,
        "-pdf",
        "-quiet",
        "-synctex=0",
        "-emulate-aux-dir",
        "-output-directory={}".format(output_dir),
        "-auxdir={}".format(aux_dir),
        str(tex_path),
    ]
    subprocess.run(cmd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate resume LaTeX (and optional PDF).")
    parser.add_argument("--data", default="CV/resume.json", help="Path to resume data JSON.")
    parser.add_argument("--output-tex", default="CV/Iraklis_Symeonidis_CV.tex", help="Output .tex path.")
    parser.add_argument("--output-pdf", default="CV/Iraklis_Symeonidis_CV.pdf", help="Output .pdf path.")
    parser.add_argument("--pdf", action="store_true", help="Build PDF via latexmk.")
    args = parser.parse_args()

    base_dir = pathlib.Path(__file__).resolve().parents[1]
    data_path = pathlib.Path(args.data)
    tex_path = pathlib.Path(args.output_tex)
    pdf_path = pathlib.Path(args.output_pdf)

    if not data_path.is_absolute():
        data_path = (base_dir / data_path).resolve()
    if not tex_path.is_absolute():
        tex_path = (base_dir / tex_path).resolve()
    if not pdf_path.is_absolute():
        pdf_path = (base_dir / pdf_path).resolve()

    data = json.loads(data_path.read_text(encoding="utf-8"))
    tex_content = render_resume(data)
    write_tex(tex_content, tex_path)

    if args.pdf:
        build_pdf(tex_path, pdf_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
