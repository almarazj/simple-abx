from app.schemas.test_results import TestResult
from app.schemas.dashboard import ResponsesOverview

def format_dashboard_results(results: list[TestResult]) -> list[ResponsesOverview]:
    formatted_results = []
    for result in sorted(results, key=lambda r: r.start_time, reverse=True):
        total = len(result.responses)
        correct = len([r for r in result.responses if r.correct])
        tie = len([r for r in result.responses if r.response == "tie"])
        score = correct + tie / 2

        formatted_results.append(ResponsesOverview(
            start_time=result.start_time.strftime("%Y-%d-%m %H:%M"),
            age_range=result.participant_info.age_range,
            headphones_brand=result.participant_info.headphones_brand,
            hearing_problems=result.participant_info.hearing_problems,
            audio_experience=result.participant_info.audio_experience,
            score=score,
            total=total
        ))

    return formatted_results
