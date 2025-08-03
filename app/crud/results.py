import os
from datetime import datetime
from app.utils.export_csv import export_results_to_csv
from app.schemas.test_results import TestResult
from app.core.db_session import collection

def export_to_csv():
    docs = collection.stream()
    results: list[TestResult] = []

    for doc in docs:
        results.append(TestResult(**doc.to_dict()))
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"abx_results_{timestamp}.csv"
    output_path = os.path.join("/tmp", filename)

    return export_results_to_csv(results, output_path)