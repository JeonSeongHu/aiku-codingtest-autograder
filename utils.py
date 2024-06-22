import re

def create_import_statements(requirements):
    import_statements = "\n"
    for requirement in requirements:
        if requirement == "numpy": requirement += " as np"
        if requirement == "pandas": requirement += " as pd"
        import_statements += f"import {requirement}\n"
    return import_statements

def compare_output(output, expected_answer, answer_type):
    if answer_type == "float":
        return float(-1e-6 < float(output) - float(expected_answer) < 1e-6)
    elif answer_type == "ratio":
        return float(output)
    elif answer_type == "pass":
        return None
    else:
        return float(eval(output) == eval(expected_answer))

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
