import streamlit as st
import json
import subprocess
import sys
import os
from streamlit_ace import st_ace
from utils import compare_output
import nbformat as nbf
import io


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
    if 'uploaded_grading_criteria' not in st.session_state or 'uploaded_problem_solutions' not in st.session_state:
        st.error("Please upload both files.")
        return

    try:
        grading_criteria = json.load(st.session_state.uploaded_grading_criteria)
        problem_solutions = json.load(st.session_state.uploaded_problem_solutions)

        problems = []
        for gc, ps in zip(grading_criteria, problem_solutions):
            if str(gc["number"]) == str(ps["number"]):
                problems.append({**gc, **ps})
            else:
                st.warning(
                    f"Problem number mismatch: {gc['number']} in grading_criteria, {ps['number']} in problem_solutions"
                )

        st.session_state.problems = problems

        # Update Streamlit-ace values
        for i, problem in enumerate(st.session_state.problems):
            st.session_state[f"answer_code_{i}"] = problem["answer_code"]
            st.session_state[f"test_code_{i}"] = problem["test_code"]

        st.success("Problems loaded successfully!")

    except json.JSONDecodeError:
        st.error("Invalid JSON format in one or both of the uploaded files.")
    except Exception as e:
        st.error(f"An error occurred while loading problems: {e}")


    except json.JSONDecodeError:
        st.error("Invalid JSON format in one or both of the uploaded files.")
    except Exception as e:
        st.error(f"An error occurred while loading problems: {e}")



def generate_grading_criteria_bytes():
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

    grading_criteria_bytes = json.dumps(grading_criteria, indent=4, ensure_ascii=False).encode('utf-8')
    return grading_criteria_bytes

def generate_problem_solutions_bytes():
    problem_solutions = [{
        "number": problem["number"],
        "name": problem["name"],
        "description": problem["description"],
        "answer_code": problem["answer_code"]
    } for problem in st.session_state.problems]

    return json.dumps(problem_solutions, indent=4, ensure_ascii=False).encode('utf-8')



def execute_code(problem, test_input):
    test_code = problem['answer_code'] + "\nprint()\n" + problem["test_code"].replace('<input>', test_input)

    subproblems = reversed(problem['subproblem_of'])
    for subproblem_number in subproblems:
        subproblem = next((p for p in st.session_state.problems if p["number"] == subproblem_number), None)
        if subproblem:
            test_code = f"{subproblem['answer_code']}\n{test_code}"

    temp_py_file = 'temp_code.py'
    with open(temp_py_file, 'w', encoding='utf-8') as f:
        import_statements = "\n".join(
            f"import {req}{' as np' if req == 'numpy' else ' as pd' if req == 'pandas' else ''}"
            for req in problem["requirements"] if req
        )
        final_code = f"{import_statements}\n{test_code}".strip()
        f.write(final_code)

    try:
        output = subprocess.check_output([sys.executable, temp_py_file], stderr=subprocess.STDOUT,
                                         universal_newlines=True).strip().split('\n')[-1]
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

    notebook_bytes_io = io.BytesIO()

    notebook_json = nbf.writes(notebook, version=4)  # Use writes to get JSON string
    notebook_bytes = notebook_json.encode('utf-8')  # Encode to bytes

    notebook_bytes_io.write(notebook_bytes)  # Write bytes to the buffer
    notebook_bytes_io.seek(0)  # Reset the buffer's position for reading

    return notebook_bytes_io.getvalue()

st.session_state.uploaded_grading_criteria = st.file_uploader("Upload grading_criteria.json", type=["json"], key="grading_criteria")
st.session_state.uploaded_problem_solutions = st.file_uploader("Upload problem.json", type=["json"], key="problem_solutions")
st.button("Load Problems from Uploaded JSONs", on_click=load_problems)

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
    - **Requirement:** 채점 시에 필요한 패키지를 쉼표(,)로 구분하여 입력합니다. (예: numpy, pandas)
    - **모범 답안 코드:** 파이썬 코드로 정답을 작성합니다.
    - **채점 코드:** 파이썬 코드로 작성하며, `<input>`을 사용하여 테스트 케이스 입력 값을 활용할 수 있습니다.
    - **Expected Answer Type:** 채점 시 예상되는 정답의 데이터 타입을 선택합니다.
    
    ### 추가 정보:
    - **문제 설명:** 마크다운 문법을 지원하여 문제를 보기 좋게 작성할 수 있습니다.
    - **부분 문제:** 특정 문제를 풀기 위해 먼저 풀어야 하는 문제의 번호를 쉼표(,)로 구분하여 입력합니다.
    - **Test Case Input:** 테스트 케이스의 입력 값을 지정합니다.
    - **Expected Answer:** 각 테스트 케이스에 대한 예상되는 정답을 입력합니다.

    ### **테스트 코드 입력 가이드**:
    - 각 Test case에 대한 해당 코드의 출력(print) **마지막 줄** 결과와, Expected answers의 결과를 정해진 type에 따라 비교합니다.
    - Expected answer와 output을 비교하지 않고 점수를 코드 내에서 직접 계산하여 출력하고자 하는 경우, 'point'를 선택하면 됩니다.
    - <input>을 이용하면, test case input을 직접 명시할 수 있습니다. <input>은 Test case에 명시된 값으로 실행시 대체됩니다.
    - Output은 모든 출력의 마지막 줄에 해당하며 해당 string이 Expected Answer Type으로 변환되어 Expected Answer와 비교됩니다.
    

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

        problem["description"] = st.text_area("Description", problem["description"], key=f"description_{i}")
        st.markdown(problem["description"])
        requirements = st.text_input("Requirements (comma-separated)", ", ".join(problem["requirements"]), key=f"requirements_{i}")
        problem["requirements"] = [req.strip() for req in requirements.split(",")]
        st.markdown("**모범 답안 작성**")
        problem["answer_code"] = st_ace(
            language='python',
            key=f"answer_code_{i}",
            value=problem["answer_code"]  # Get from session state or use empty string
        )
        st.markdown("**태스트 코드 작성 (가이드라인 필독)**")
        problem["test_code"] = st_ace(
            language='python',
            key=f"test_code_{i}",
            value=problem["test_code"]  # Get from session state or use empty string
        )
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

        problem["expected_answers_type"] = st.selectbox(f"Expected Answer Type", ["float", "list", "dict", "set", "str", "int", "short-answer question", "point"], index=["float", "list", "dict", "set", "str", "int", "short-answer question", "point"].index(problem["expected_answers_type"] if problem["expected_answers_type"] else "float"), key=f"expected_answers_type_{i}")

        subproblem_of = st.text_input(f"부분 문제 (comma-separated)", ", ".join(problem["subproblem_of"]), key=f"subproblem_of_{i}")
        problem["subproblem_of"] = [sub.strip() for sub in subproblem_of.split(",")]

        if st.button("Run Test Code", key=f"run_test_code_{i}"):
            test_input = problem["input"][0]

            # Clear the output variable before running the test code
            output = ""

            test_code, output = execute_code(problem, test_input)
            expected_answer = problem["expected_answers"][0]

            st.text_area("Generated Test Code", test_code, height=200)
            st.text_area("Test Output", output, height=100)  # Display the output (including errors)
            st.text_area("Expected Answer", expected_answer, height=100)

            # Error handling for both execution and comparison
            if "Error during execution:" not in output:
                try:
                    comparison_result = compare_output(output, expected_answer, problem["expected_answers_type"])
                    st.text_area("Comparison Result", str(comparison_result), height=50)
                except Exception as e:
                    st.text_area("Comparison Result", f"Error during comparison: {e}", height=50)

st.button("Add Problem", on_click=add_problem)



st.download_button(
    label="Download Problems JSON",
    data=generate_problem_solutions_bytes(),
    file_name="problems.json",
    mime="application/json"
)

# Display the problems JSON
st.subheader("Problems JSON")
st.json(st.session_state.problems)

st.download_button(
    label="Download Grading Criteria JSON",
    data=generate_grading_criteria_bytes(),
    file_name="grading_criteria.json",
    mime="application/json"
)

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

st.download_button(
    label="Create Colab Notebooks",
    data=create_colab_notebooks(),
    file_name="colab_notebook.ipynb",
    mime="application/json"
)
