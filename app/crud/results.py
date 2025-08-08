import os
from datetime import datetime
from collections import defaultdict

from app.core.db_session import collection
from app.schemas.test_results import TestResult
from app.schemas.dashboard import PairStats, Stats, PairStimulus, DashboardData
from app.utils.formatters import format_dashboard_results
from app.utils.export_csv import export_results_to_csv


def export_to_csv():
    docs = collection.stream()
    results: list[TestResult] = []

    for doc in docs:
        results.append(TestResult(**doc.to_dict()))
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"abx_results_{timestamp}.csv"
    output_path = os.path.join("/tmp", filename)

    return export_results_to_csv(results, output_path)


def get_dashboard_data():
    docs = collection.stream()
    results: list[TestResult] = []

    for doc in docs:
        # Agregar excepcion
        results.append(TestResult(**doc.to_dict()))

    pair_stats: dict[str, PairStats] = {}

    for result in results:
        responses = result.responses
        comparisons = result.test_config.comparisons

        for idx, response in enumerate(responses):
            if idx >= len(comparisons):
                continue

            comp = comparisons[idx]
            pair_info = comp.pair_info
            pair_id = pair_info.pair_id
            stimulus = pair_info.stimulus_type
            pulse_density = pair_info.pulse_density

            if pair_id not in pair_stats:
                pair_stats[pair_id] = PairStats(
                    stimulus=stimulus,
                    pulse_density=pulse_density,
                    correct=0.0,
                    total=0
                )

            pair_stats[pair_id].total += 1
            if response.correct is True:
                pair_stats[pair_id].correct += 1
            if response.response == "tie":
                pair_stats[pair_id].correct += 0.5

    # Estadísticas generales
    total_responses = sum(len(r.responses) for r in results)
    correct_responses = sum(
        sum(
            1 if resp.correct is True else 0.5 if resp.response == "tie" else 0
            for resp in r.responses
        )
        for r in results
    )
    accuracy_percentage = round((correct_responses / total_responses) * 100, 1) if total_responses > 0 else 0

    stats = Stats(
        total_tests=len(results),
        total_responses=total_responses,
        correct_responses=correct_responses,
        accuracy_percentage=accuracy_percentage
    )

    # Datos para gráficos
    accuracy_data: dict[str, list[float]] = defaultdict(list)
    response_data: dict[str, list[int]] = defaultdict(list)
    by_stimulus: dict[str, list[PairStimulus]] = defaultdict(list)

    for pair_id, data in pair_stats.items():
        stimulus = data.stimulus
        density = data.pulse_density
        accuracy = int((data.correct / data.total) * 100) if data.total > 0 else 0

        by_stimulus[stimulus].append(PairStimulus(
            label=f"{density} p/s",
            pulse_density=int(density),
            accuracy=accuracy,
            pair_id=pair_id,
            correct=int(data.correct),
            total=data.total
        ))
        accuracy_data[stimulus].append(accuracy)
        response_data[stimulus].append(data.total)

    for stim in by_stimulus:
        by_stimulus[stim] = sorted(by_stimulus[stim], key=lambda x: x.pulse_density)

    dashboard_data = DashboardData(
        stats=stats,
        stimulus_pairs=dict(by_stimulus),
        responses=format_dashboard_results(results),
    )
    return dashboard_data