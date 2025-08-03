import csv
from app.schemas.test_results import TestResult

def export_results_to_csv(test_results: list[TestResult], output_path: str):
    all_columns_set = set()
    for result in test_results:
        for r in result.responses:
            if r.stimulus and r.pulse_density:
                col_name = f"{r.stimulus}_{r.pulse_density}"
                all_columns_set.add(col_name)

    all_columns = sorted(all_columns_set) 
    header = ['age', 'headphones_brand', 'hearing_problems', 'audio_experience'] + all_columns

    with open(output_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()

        for result in test_results:
            row = {
                'age': result.participant_info.age_range,
                'headphones_brand': result.participant_info.headphones_brand,
                'hearing_problems': result.participant_info.hearing_problems,
                'audio_experience': result.participant_info.audio_experience,
            }

            for r in result.responses:
                if r.stimulus and r.pulse_density:
                    col_name = f"{r.stimulus}_{r.pulse_density}"
                    row[col_name] = r.correct

            writer.writerow(row)
            
    return output_path