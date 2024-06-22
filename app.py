import streamlit as st
import json
import subprocess
import sys
import os
from streamlit_ace import st_ace
from utils import compare_output


def add_problem():
    if 'problems' not in st.session_state:
        st.session_state.problems = []

    st.session_state.problems.append({
        "name": "",
        "description": "",
        "requirements": [],
        "answer_code": "",
        "test_code": "",
        "input": [],
        "expected_answers": [],
        "expected_answers_type": "",
        "subproblem_of": []
    })


def save_problems():
    grading_criteria = [{
        "name": problem["name"],
        "requirements": problem["requirements"],
        "test_code": problem["test_code"],
        "input": problem["input"],
        "expected_answers": problem["expected_answers"],
        "expected_answers_type": problem["expected_answers_type"],
        "subproblem_of": problem["subproblem_of"]
    } for problem in st.session_state.problems]

    problem_solutions = [{
        "name": problem["name"],
        "description": problem["description"],
        "answer_code": problem["answer_code"]
    } for problem in st.session_state.problems]

    with open('grading_criteria.json', 'w', encoding='utf-8') as f:
        json.dump(grading_criteria, f, indent=4, ensure_ascii=False)

    with open('problem_solutions.json', 'w', encoding='utf-8') as f:
        json.dump(problem_solutions, f, indent=4, ensure_ascii=False)

    st.success("Problems and solutions saved successfully!")


def execute_code(problem, test_input):
    test_code = problem["test_code"].replace('<input>', test_input)

    # Add subproblem code if any
    subproblems = reversed(problem['subproblem_of'])
    for subproblem_name in subproblems:
        subproblem = next((p for p in st.session_state.problems if p["name"] == subproblem_name), None)
        if subproblem:
            test_code = f"{subproblem['answer_code']}\n{test_code}"

    # Create a temporary file to run the code
    temp_py_file = 'temp_code.py'
    with open(temp_py_file, 'w', encoding='utf-8') as f:
        import_statements = "\n".join([f"import {req}" for req in problem["requirements"] if req.strip()])
        f.write(f"{import_statements}\n{problem['answer_code']}\n{test_code}")

    try:
        output = subprocess.check_output([sys.executable, temp_py_file], universal_newlines=True).strip()
    except subprocess.CalledProcessError as e:
        output = str(e)

    os.remove(temp_py_file)
    return test_code, output


st.title("Grading Criteria Creator")

if 'problems' not in st.session_state:
    st.session_state.problems = []

# Add problem button
st.button("Add Problem", on_click=add_problem)

for i, problem in enumerate(st.session_state.problems):
    st.subheader(f"Problem {i + 1}")

    problem["name"] = st.text_input(f"Problem Name {i + 1}", problem["name"], key=f"name_{i}")

    problem["description"] = st.text_area(f"Problem Description (Markdown) {i + 1}", problem["description"],
                                          key=f"description_{i}")

    requirements = st.text_input(f"Requirements (comma-separated) {i + 1}", ", ".join(problem["requirements"]),
                                 key=f"requirements_{i}")
    problem["requirements"] = [req.strip() for req in requirements.split(",")]

    problem["answer_code"] = st_ace(f"Answer Code {i + 1}", language='python', key=f"answer_code_{i}")
    problem["test_code"] = st_ace(f"Test Code {i + 1}", language='python', key=f"test_code_{i}")

    num_inputs = st.number_input(f"Number of Test Cases {i + 1}", min_value=1, value=len(problem["input"]) or 1,
                                 key=f"num_inputs_{i}")

    # Ensure the lists are long enough
    if len(problem["input"]) < num_inputs:
        problem["input"].extend([""] * (num_inputs - len(problem["input"])))
    if len(problem["expected_answers"]) < num_inputs:
        problem["expected_answers"].extend([""] * (num_inputs - len(problem["expected_answers"])))

    for j in range(num_inputs):
        cols = st.columns(2)
        with cols[0]:
            problem["input"][j] = st.text_input(f"Test Case Input {i + 1}.{j + 1}", value=problem["input"][j],
                                                key=f"input_{i}_{j}")
        with cols[1]:
            problem["expected_answers"][j] = st.text_input(f"Expected Answer {i + 1}.{j + 1}",
                                                           value=problem["expected_answers"][j],
                                                           key=f"expected_answer_{i}_{j}")

    problem["expected_answers_type"] = st.selectbox(f"Expected Answer Type {i + 1}",
                                                    ["float", "list", "dict", "set", "str", "int", "pass", "ratio"],
                                                    index=["float", "list", "dict", "set", "str", "int", "pass",
                                                           "ratio"].index(problem["expected_answers_type"] if problem[
                                                        "expected_answers_type"] else "float"),
                                                    key=f"expected_answers_type_{i}")

    subproblem_of = st.text_input(f"Subproblem Of (comma-separated) {i + 1}", ", ".join(problem["subproblem_of"]),
                                  key=f"subproblem_of_{i}")
    problem["subproblem_of"] = [sub.strip() for sub in subproblem_of.split(",")]

    if st.button(f"Run Test Code {i + 1}"):
        test_input = problem["input"][0]  # Use the first input for the test
        test_code, output = execute_code(problem, test_input)
        expected_answer = problem["expected_answers"][0]  # Use the first expected answer for comparison
        comparison_result = compare_output(output, expected_answer, problem["expected_answers_type"])

        st.text_area(f"Generated Test Code {i + 1}", test_code, height=200)
        st.text_area(f"Test Output {i + 1}", output, height=100)
        st.text_area(f"Expected Answer {i + 1}", expected_answer, height=100)
        st.text_area(f"Comparison Result {i + 1}", str(comparison_result), height=50)

# Save problems button
st.button("Save Problems", on_click=save_problems)

# Display the problems JSON
st.subheader("Problems JSON")
st.json(st.session_state.problems)

# Display the grading criteria JSON
st.subheader("Grading Criteria JSON")
grading_criteria = [{
    "name": problem["name"],
    "requirements": problem["requirements"],
    "test_code": problem["test_code"],
    "input": problem["input"],
    "expected_answers": problem["expected_answers"],
    "expected_answers_type": problem["expected_answers_type"],
    "subproblem_of": problem["subproblem_of"]
} for problem in st.session_state.problems]
st.json(grading_criteria)
