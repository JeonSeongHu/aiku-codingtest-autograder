import nbformat
import os
import subprocess
import sys
from utils import create_import_statements, compare_output
from extractor import extract_personal_info_from_markdown, extract_problems_and_answers

def grade_notebook(notebook_path, grading_criteria):
    with open(notebook_path, 'r', encoding='utf-8') as f:
        notebook = nbformat.read(f, as_version=4)

    personal_info, problems, answers = extract_problems_and_answers(notebook)

    results = {}
    for problem, answer, criteria in zip(problems, answers, grading_criteria):
        problem_name = criteria['name']
        answered_code = answer
        test_code = criteria['test_code']
        requirements = criteria['requirements']
        test_inputs = criteria['input']
        expected_outputs = criteria['expected_answers']
        answer_type = criteria['expected_answers_type']
        subproblems = reversed(criteria['subproblem_of'])

        temp_py_file = 'temp_code.py'
        with open(temp_py_file, 'w', encoding='utf-8') as f:
            f.write(answered_code)

        test_results = []

        for test_input, expected_output in zip(test_inputs, expected_outputs):
            full_test_code = test_code.replace('<input>', str(test_input))
            full_test_code = f"{answered_code}\n{full_test_code}"
            for subproblem in subproblems:
                subproblem_index = next((i for i, item in enumerate(grading_criteria) if item['name'] == subproblem), -1)
                subproblem_code = answers[subproblem_index]
                full_test_code = f"{subproblem_code}\n{full_test_code}"

            with open(temp_py_file, 'w', encoding='utf-8') as f:
                if requirements:
                    import_statements = create_import_statements(requirements)
                else:
                    import_statements = ""
                f.write(import_statements + full_test_code)

            try:
                output = subprocess.check_output([sys.executable, temp_py_file], universal_newlines=True).strip()
                point = compare_output(output, expected_output, answer_type)
                test_results.append({'test_input': test_input, 'output': output, 'expected': expected_output, 'point': point})
            except subprocess.CalledProcessError as e:
                test_results.append({'test_input': test_input, 'output': str(e), 'expected': expected_output, 'point': 0.0})

        results[problem_name] = test_results
        os.remove(temp_py_file)

    return personal_info, results
