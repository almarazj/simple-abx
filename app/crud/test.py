import uuid
from datetime import datetime
from app.database.models import TestResult
from app.models.schemas import SubmitResponseResult
from app.database.session import collection
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
        test_config={},
    )
    result_dict = test_result.to_dict()
    return user_id, result_dict


def create_comparisons(user_id, test_result: TestResult):
    comparisons = generate_test_sequence()
    test_result.test_config = {"comparisons": comparisons}
    update_test_results(user_id, test_result.to_dict())
    return test_result


def get_test_info(user_id):
    doc = collection.document(user_id).get()
    test_result = TestResult(**doc.to_dict())
    if not test_result.test_config:
        test_result = create_comparisons(user_id, test_result)
    comparisons = test_result.test_config.get("comparisons", [])
    current = len(test_result.responses)
    return current, comparisons


def submit_test_response(user_id: str, response: str) -> SubmitResponseResult:
    doc = collection.document(user_id).get()
    test_result = TestResult(**doc.to_dict())

    comparisons = test_result.test_config.get("comparisons", [])
    current = len(test_result.responses)
    correct = None

    correct_answer = comparisons[current].get("correct_answer")
    correct = (response == correct_answer)
    test_result.responses.append({
        "stimulus": comparisons[current].get("pair_info").get("stimulus_type"),
        "pulse_density": comparisons[current].get("pair_info").get("pulse_density"),
        "response": response,
        "correct": correct
    })
    update_test_results(user_id, test_result.to_dict())
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
            next_comparison=comparisons[current]
        )
