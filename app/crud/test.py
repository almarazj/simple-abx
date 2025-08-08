import uuid
from datetime import datetime

from app.core.db_session import collection
from app.schemas.test_results import TestResult, SubmitResponseResult, ResponseItem, TestConfig
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
