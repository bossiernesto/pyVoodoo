# Flags from code.h
CO_OPTIMIZED = 0x0001  # use LOAD/STORE_FAST instead of _NAME
CO_NEWLOCALS = 0x0002  # only cleared for module/exec code
CO_VARARGS = 0x0004
CO_VARKEYWORDS = 0x0008
CO_NESTED = 0x0016  # ???
CO_GENERATOR = 0x0032
CO_NOFREE = 0x0064  # set if no free or cell vars
CO_GENERATOR_ALLOWED = 0x0128  # unused

#Futures
CO_FUTURE_DIVISION = 0x2000
CO_FUTURE_ABSOLUTE_IMPORT = 0x4000  # Python 2.5+ only
CO_FUTURE_WITH_STATEMENT = 0x8000  # Python 2.5+ only