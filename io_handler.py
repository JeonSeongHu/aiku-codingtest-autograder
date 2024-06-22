import json
import os
import pandas as pd
from datetime import datetime

def save_grading_results(results_dir, notebook_filename, personal_info, results):
    individual_result_path = os.path.join(results_dir, f'{notebook_filename}_result.json')
    with open(individual_result_path, 'w', encoding='utf-8') as f:
        json.dump({'personal_info': personal_info, 'results': results}, f, indent=4, ensure_ascii=False)

def save_overall_results(results_dir, all_results):
    df = pd.DataFrame(all_results)
    overall_result_path = os.path.join(results_dir, 'overall_results.csv')
    df.to_csv(overall_result_path, index=False, encoding='utf-8-sig')

def create_results_directory():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_dir = f'results/{timestamp}'
    os.makedirs(results_dir, exist_ok=True)
    return results_dir

def copy_grading_criteria(results_dir, grading_criteria):
    criteria_copy_path = os.path.join(results_dir, 'grading_criteria.json')
    with open(criteria_copy_path, 'w', encoding='utf-8') as f:
        json.dump(grading_criteria, f, indent=4, ensure_ascii=False)
