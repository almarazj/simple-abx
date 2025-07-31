import uuid
from datetime import datetime
from collections import defaultdict

from app.schemas.test_results import TestResult, SubmitResponseResult, ResponseItem, TestConfig
from app.schemas.dashboard import PairStats, Stats, PairStimulus, DashboardData

from app.core.db_session import collection
from app.utils.test_config import generate_test_sequence


def update_test_results(user_id, test_result):
    collection.document(user_id).set(test_result)


def create_participant_result(form_data):
    user_id = str(uuid.uuid4())
    test_result = TestResult(
        user_id=user_id,
        participant_info=form_data,
        start_time=datetime.now(),
        responses=[],
        test_config=TestConfig(comparisons=[]),
    )
    result_dict = test_result.model_dump()
    return user_id, result_dict


def create_comparisons(user_id, test_result: TestResult):
    comparisons = generate_test_sequence()
    test_result.test_config = TestConfig(comparisons=comparisons)
    update_test_results(user_id, test_result.model_dump())
    return test_result


def get_test_info(user_id):
    doc = collection.document(user_id).get()
    test_result = TestResult(**doc.to_dict())
    if not test_result.test_config.comparisons:
        test_result = create_comparisons(user_id, test_result)
    comparisons = test_result.test_config.comparisons
    current = len(test_result.responses)
    return current, comparisons


def submit_test_response(user_id: str, response: str) -> SubmitResponseResult:
    doc = collection.document(user_id).get()
    test_result = TestResult(**doc.to_dict())

    comparisons = test_result.test_config.comparisons
    current = len(test_result.responses)

    comparison = comparisons[current]
    correct_answer = comparison.correct_answer
    correct = (response == correct_answer)
    
    response_item = ResponseItem(
        stimulus=comparison.pair_info.stimulus_type,
        pulse_density=comparison.pair_info.pulse_density,
        response=response,
        correct=correct
    )
    test_result.responses.append(response_item)
    update_test_results(user_id, test_result.model_dump())
    
    current += 1
    if current >= len(comparisons):
        return SubmitResponseResult(
            status="completed",
            current=current,
            total=len(comparisons),
            redirect=f"/results?user_id={user_id}"
        )
    else:
        return SubmitResponseResult(
            status="continue",
            current=current + 1,
            total=len(comparisons),
            next_comparison=comparisons[current].model_dump()
        )


def get_results(user_id):
    doc = collection.document(user_id).get()
    if not doc.exists:
        return {
            "total_comparisons": 0,
            "correct_responses": 0,
            "accuracy_percentage": 0
        }
    test_result = TestResult(**doc.to_dict())
    responses = test_result.responses
    total_comparisons = len(responses)
    correct_responses = sum(
        1 if r.correct is True else 0.5 if (r.response == "tie") else 0
        for r in responses
    )
    accuracy_percentage = round((correct_responses / total_comparisons) * 100, 1) if total_comparisons > 0 else 0
    return {
        "total_comparisons": total_comparisons,
        "correct_responses": correct_responses,
        "accuracy_percentage": accuracy_percentage
    }


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
        accuracy = (data.correct / data.total) * 100 if data.total > 0 else 0

        by_stimulus[stimulus].append(PairStimulus(
            label=f"{density} p/s",
            pulse_density=int(density),
            accuracy=accuracy,
            pair_id=pair_id
        ))
        accuracy_data[stimulus].append(accuracy)
        response_data[stimulus].append(data.total)

    for stim in by_stimulus:
        by_stimulus[stim] = sorted(by_stimulus[stim], key=lambda x: x.pulse_density)

    dashboard_data = DashboardData(
        stats=stats,
        pair_stats=pair_stats,
        accuracy_data=dict(accuracy_data),
        response_data=dict(response_data),
        stimulus_pairs=dict(by_stimulus),
        results=results,
    )
    return dashboard_data