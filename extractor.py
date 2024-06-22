import re

def extract_personal_info_from_markdown(markdown_text):
    info = {}
    lines = markdown_text.split('\n')
    for line in lines:
        match = re.match(r'>\s*(\w+):\s*(.+)', line)
        if match:
            key = match.group(1).strip()
            value = match.group(2).strip()
            info[key] = value
    return info

def extract_problems_and_answers(notebook):
    answers = []
    problems = []
    personal_info = {}

    PROBLEM_INDICATOR = "Q. "
    PERSONAL_INFO_INDICATOR = "신원 정보 확인"

    cell_iter = iter(notebook.cells)
    for cell in cell_iter:
        if cell.cell_type == 'markdown':
            if PERSONAL_INFO_INDICATOR in cell.source:
                personal_info = extract_personal_info_from_markdown(cell.source)
            elif PROBLEM_INDICATOR in cell.source:
                problems.append(cell.source)
                answers.append(next(cell_iter).source)

    return personal_info, problems, answers
