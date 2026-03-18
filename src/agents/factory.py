from specialists import RegistrarBot, ChiefStrategist

class Agency:
    @staticmethod
    def hire(specialist_name):
        if specialist_name == "registrar":
            return RegistrarBot(llm="gemini-flash")
        elif specialist_name == "strategist":
            return ChiefStrategist(llm="claude-sonnet")