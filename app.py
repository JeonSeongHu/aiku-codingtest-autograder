import streamlit as st
import json
import subprocess
import sys
import os
from streamlit_ace import st_ace
from utils import compare_output
import nbformat as nbf



def add_problem():
    if 'problems' not in st.session_state:
        st.session_state.problems = []

    st.session_state.problems.append({
        "number": "",
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

def delete_problem(index):
    del st.session_state.problems[index]

def load_problems():
    uploaded_grading_criteria = st.file_uploader("Upload grading_criteria.json", type=["json"])
    uploaded_problem_solutions = st.file_uploader("Upload problem_solutions.json", type=["json"])

    if uploaded_grading_criteria and uploaded_problem_solutions:
        try:
            # Use .read() to get the file contents before loading JSON
            grading_criteria = json.load(uploaded_grading_criteria)
            problem_solutions = json.load(uploaded_problem_solutions)

            problems = []
            # Iterate over the shorter list to avoid IndexError if lists have different lengths
            for gc, ps in zip(grading_criteria, problem_solutions):
                # Check for matching problem numbers based on string comparison
                if str(gc["number"]) == str(ps["number"]):
                    problems.append({**gc, **ps})

            st.session_state.problems = problems
            st.success("Problems loaded successfully!")

        except json.JSONDecodeError:
            st.error("Invalid JSON format.")
        except Exception as e:
            st.error(f"An error occurred while loading problems: {e}")  # Catch and display general errors



def save_problems():
    grading_criteria = [{
        "number": problem["number"],
        "name": problem["name"],
        "requirements": problem["requirements"],
        "test_code": problem["test_code"],
        "input": problem["input"],
        "expected_answers": problem["expected_answers"],
        "expected_answers_type": problem["expected_answers_type"],
        "subproblem_of": problem["subproblem_of"]
    } for problem in st.session_state.problems]

    problem_solutions = [{
        "number": problem["number"],
        "name": problem["name"],
        "description": problem["description"],
        "answer_code": problem["answer_code"]
    } for problem in st.session_state.problems]

    grading_criteria_bytes = json.dumps(grading_criteria, indent=4, ensure_ascii=False).encode('utf-8')
    problem_solutions_bytes = json.dumps(problem_solutions, indent=4, ensure_ascii=False).encode('utf-8')

    st.download_button(
        label="Download grading_criteria.json",
        data=grading_criteria_bytes,
        file_name="grading_criteria.json",
        mime="application/json"
    )

    st.download_button(
        label="Download problem_solutions.json",
        data=problem_solutions_bytes,
        file_name="problem_solutions.json",
        mime="application/json"
    )


def execute_code(problem, test_input):
    test_code = problem['answer_code'] + "\n" + problem["test_code"].replace('<input>', test_input)

    subproblems = reversed(problem['subproblem_of'])
    for subproblem_number in subproblems:
        subproblem = next((p for p in st.session_state.problems if p["number"] == subproblem_number), None)
        if subproblem:
            test_code = f"{subproblem['answer_code']}\n{test_code}"

    temp_py_file = 'temp_code.py'
    with open(temp_py_file, 'w', encoding='utf-8') as f:
        import_statements = "\n".join([f"import {req}" for req in problem["requirements"] if req.strip()])
        final_code = f"{import_statements}\n{test_code}"
        f.write(final_code)

    try:
        output = subprocess.check_output([sys.executable, temp_py_file], stderr=subprocess.STDOUT,
                                         universal_newlines=True)
    except subprocess.CalledProcessError as e:
        output = f"Error during execution:\n{e.output}"  # Capture and display the error message
    finally:
        os.remove(temp_py_file)  # Clean up the temporary file

    return final_code.strip(), output.strip()  # Strip any extra whitespace from the output

def create_colab_notebooks():
    problem_solutions = [{
        "number": problem["number"],
        "name": problem["name"],
        "description": problem["description"],
        "answer_code": problem["answer_code"]
    } for problem in st.session_state.problems]

    notebook = nbf.v4.new_notebook()

    for problem in problem_solutions:
        problem_number = problem["number"]
        problem_name = problem["name"]
        problem_description = problem["description"]
        answer_code = problem["answer_code"]

        # Markdown cell for problem description
        markdown_cell = nbf.v4.new_markdown_cell()
        markdown_cell.source = f"""
## Q. {problem_number}. {problem_name}

{problem_description}
"""
        notebook.cells.append(markdown_cell)

        # Code cell for answer code
        code_cell = nbf.v4.new_code_cell()
        code_cell.source = f"""
{answer_code}
"""
        notebook.cells.append(code_cell)

        # Save the notebook
    nbf.write(notebook, f'colab_notebook.ipynb')

    st.success("Colab notebooks created successfully!")

st.title("AIKU 코딩테스트 문제 출제 도우미")

if 'problems' not in st.session_state:
    st.session_state.problems = []


with st.expander("사용 설명"):
    st.markdown("""
    ## AIKU 코딩 테스트 문제 출제 도우미에 오신 것을 환영합니다!

    ### 주요 기능:
    - **문제 추가:** 문제 틀을 쉽게 추가하여 문제 은행을 만들 수 있습니다.
    - **문제 상세 설정:** 문제 번호, 제목, 설명, 요구사항(필요 패키지), 모범 답안 코드, 채점 코드, 테스트 케이스를 상세히 설정할 수 있습니다.
    - **테스트 코드 실행:** 실시간으로 작성한 코드를 테스트하고 결과를 확인할 수 있습니다.
    - **Colab 노트북 생성:** 문제 설명과 모범 답안이 담긴 Colab 노트북 파일을 자동으로 생성합니다.
    - **JSON 파일 저장:** 문제 정보와 채점 기준을 JSON 형태로 저장하여 관리를 용이하게 합니다.

    ### 입력 가이드:
    - **문제 번호:** 각 문제에 고유한 번호를 부여합니다. (미입력 시 자동 생성)
    - **요구사항:** 필요한 패키지를 쉼표(,)로 구분하여 입력합니다. (예: numpy, pandas)
    - **모범 답안 코드:** 파이썬 코드로 정답을 작성합니다.
    - **채점 코드:** 파이썬 코드로 작성하며, `<input>`을 사용하여 테스트 케이스 입력 값을 활용할 수 있습니다.
    - **Expected Answer Type:** 채점 시 예상되는 정답의 데이터 타입을 선택합니다.

    ### 추가 정보:
    - **문제 설명:** 마크다운 문법을 지원하여 문제를 보기 좋게 작성할 수 있습니다.
    - **부분 문제:** 특정 문제를 풀기 위해 먼저 풀어야 하는 문제의 번호를 쉼표(,)로 구분하여 입력합니다.
    - **Test Case Input:** 테스트 케이스의 입력 값을 지정합니다.
    - **Expected Answer:** 각 테스트 케이스에 대한 예상되는 정답을 입력합니다.
    """)


for i, problem in enumerate(st.session_state.problems):
    problem_number = problem.get("number", i + 1)

    with st.expander(f"Problem {problem_number}"):
        sub_columns = st.columns(3) #add for delete button
        with sub_columns[0]:
            problem["number"] = st.text_input("Problem Number", problem["number"], key=f"number_{i}")
        with sub_columns[1]:
            problem["name"] = st.text_input("Problem Name", problem["name"], key=f"name_{i}")
        with sub_columns[2]:
            st.button("Delete Problem", key=f"delete_{i}", on_click=delete_problem, args=(i,))

        problem["description"] = st.text_input("Description", problem["description"], key=f"description_{i}")
        st.markdown(problem["description"])
        requirements = st.text_input("Requirements (comma-separated)", ", ".join(problem["requirements"]), key=f"requirements_{i}")
        problem["requirements"] = [req.strip() for req in requirements.split(",")]

        problem["answer_code"] = st_ace(f"모범 답안 코드입니다.\n", language='python', key=f"answer_code_{i}")
        problem["test_code"] = st_ace(f"채점을 위한 코드입니다. 해당 코드의 출력(print) 결과와, 아래의 expected answers의 결과를 정해진 type에 따라 비교합니다.\n\n점수를 직접 출력하고자 하는 경우, 'point'를 선택하면 됩니다. 이 때, 출력 형식은 float여야 하며, 해당 test code의 출력 결과가 그대로 점수로 반영됩니다.\n\n <input> 을 이용하여, test case input을 직접 명시할 수 있습니다.\n\n", language='python', key=f"test_code_{i}")
        num_inputs = st.number_input(f"Number of Test Cases", min_value=1, value=len(problem["input"]) or 1, key=f"num_inputs_{i}")

        if len(problem["input"]) < num_inputs:
            problem["input"].extend([""] * (num_inputs - len(problem["input"])))
        if len(problem["expected_answers"]) < num_inputs:
            problem["expected_answers"].extend([""] * (num_inputs - len(problem["expected_answers"])))

        for j in range(num_inputs):
            cols = st.columns(2)
            with cols[0]:
                problem["input"][j] = st.text_input(f"Test Case Input {j + 1} (생략 가능)", value=problem["input"][j], key=f"input_{i}_{j}")
            with cols[1]:
                problem["expected_answers"][j] = st.text_input(f"Expected Answer {j + 1}", value=problem["expected_answers"][j], key=f"expected_answer_{i}_{j}")

        problem["expected_answers_type"] = st.selectbox(f"Expected Answer Type", ["float", "list", "dict", "set", "str", "int", "pass", "point"], index=["float", "list", "dict", "set", "str", "int", "pass", "point"].index(problem["expected_answers_type"] if problem["expected_answers_type"] else "float"), key=f"expected_answers_type_{i}")

        subproblem_of = st.text_input(f"부분 문제 (comma-separated)", ", ".join(problem["subproblem_of"]), key=f"subproblem_of_{i}")
        problem["부분 문제"] = [sub.strip() for sub in subproblem_of.split(",")]

        if st.button("Run Test Code", key=f"run_test_code_{i}"):
            test_input = problem["input"][0]
            test_code, output = execute_code(problem, test_input)
            expected_answer = problem["expected_answers"][0]

            st.text_area("Generated Test Code", test_code, height=200)
            st.text_area("Test Output", output, height=100)  # Display the output (including errors)
            st.text_area("Expected Answer", expected_answer, height=100)
            if "Error during execution:" not in output:
                try:
                    comparison_result = compare_output(output, expected_answer, problem["expected_answers_type"])
                    st.text_area("Comparison Result", str(comparison_result), height=50)
                except Exception as e:
                    st.text_area("Comparison Result", f"Error during comparison: {e}", height=50)

st.button("Add Problem", on_click=add_problem)
st.button("Load Problems", on_click=load_problems)
st.button("Save Problems", on_click=save_problems)

# Display the problems JSON
st.subheader("Problems JSON")
st.json(st.session_state.problems)

# Display the grading criteria JSON
st.subheader("Grading Criteria JSON")
grading_criteria = [{
    "number": problem["number"],
    "name": problem["name"],
    "requirements": problem["requirements"],
    "test_code": problem["test_code"],
    "input": problem["input"],
    "expected_answers": problem["expected_answers"],
    "expected_answers_type": problem["expected_answers_type"],
    "subproblem_of": problem["subproblem_of"]
} for problem in st.session_state.problems]
st.json(grading_criteria)

st.button("Create Colab Notebooks", on_click=create_colab_notebooks)

