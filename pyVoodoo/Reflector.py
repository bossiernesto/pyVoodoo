import inspect

class Reflector:

    @staticmethod
    def who_am_i():
        return inspect.stack()[1][3]

    @staticmethod
    def who_called_me():
        return inspect.stack()[2][3]
