import os
import json
from grader import grade_notebook
from io_handler import save_grading_results, save_overall_results, create_results_directory, copy_grading_criteria

def main():
    with open('grading_criteria.json', 'r', encoding='utf-8') as f:
        grading_criteria = json.load(f)

    notebook_files = [f for f in os.listdir('answers') if f.endswith('.ipynb')]

    results_dir = create_results_directory()

    all_results = []
    for notebook_file in notebook_files:
        notebook_path = os.path.join('answers', notebook_file)
        personal_info, results = grade_notebook(notebook_path, grading_criteria)

        save_grading_results(results_dir, notebook_file, personal_info, results)

        personal_info.update({problem: sum(test['point'] for test in tests)/len(tests) for problem, tests in results.items()})
        all_results.append(personal_info)

    save_overall_results(results_dir, all_results)
    copy_grading_criteria(results_dir, grading_criteria)

if __name__ == "__main__":
    main()
