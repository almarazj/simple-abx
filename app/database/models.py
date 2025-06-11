# Ejemplo de esquema para Firestore (puedes adaptar según tus necesidades)
class TestResult:
    def __init__(self, user_id, participant_info, start_time, end_time, responses, test_config, statistics, created_at):
        self.user_id = user_id
        self.participant_info = participant_info
        self.start_time = start_time
        self.end_time = end_time
        self.responses = responses
        self.test_config = test_config
        self.statistics = statistics
        self.created_at = created_at

    def to_dict(self):
        return self.__dict__
