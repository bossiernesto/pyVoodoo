class AssemblerBytecodeException(Exception):
    pass


class InstructionNotFoundException(AssemblerBytecodeException):
    pass

class PersistorException(Exception):
    pass