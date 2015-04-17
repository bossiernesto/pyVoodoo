import opcode
from _io import StringIO
from collections import OrderedDict
import dis

class Opcode(tuple):
    """An int which represents an opcode - has a nicer repr."""
    def __repr__(self):
       return "{0}: {1}".format(self[0],self[1])

    def opcode_name(self):
        return self[0]

    def code(self):
        return self[1]



opmap = dict((name.replace('+', '_'), Opcode((name, code)))
              for name, code in opcode.opmap.items()
              if name != 'EXTENDED_ARG')
opmap = OrderedDict(sorted(opmap.items()))
opname = dict((code.code(), name) for name, code in opmap.items())
opcodes = set(opname)

make_opcode = lambda code: Opcode((opname[code],code))

#CMP
cmp_op = opcode.cmp_op

#make ops global
hasarg = set(x for x in opcodes if x >= opcode.HAVE_ARGUMENT)
hasconst = set(make_opcode(x) for x in opcode.hasconst)
hasname = set(make_opcode(x) for x in opcode.hasname)
hasjrel = set(make_opcode(x) for x in opcode.hasjrel)
hasjabs = set(make_opcode(x) for x in opcode.hasjabs)
hasjump = hasjrel.union(hasjabs)
haslocal = set(make_opcode(x) for x in opcode.haslocal)
hascompare = set(make_opcode(x) for x in opcode.hascompare)
hasfree = set(make_opcode(x) for x in opcode.hasfree)

COMPILER_FLAG_NAMES = {
     1: "OPTIMIZED",
     2: "NEWLOCALS",
     4: "VARARGS",
     8: "VARKEYWORDS",
    16: "NESTED",
    32: "GENERATOR",
    64: "NOFREE",
}

# Flags from code.h
CO_OPTIMIZED              = 0x0001      # use LOAD/STORE_FAST instead of _NAME
CO_NEWLOCALS              = 0x0002      # only cleared for module/exec code
CO_VARARGS                = 0x0004
CO_VARKEYWORDS            = 0x0008
CO_NESTED                 = 0x0016      # ???
CO_GENERATOR              = 0x0032
CO_NOFREE                 = 0x0064      # set if no free or cell vars
CO_GENERATOR_ALLOWED      = 0x0128      # unused

class CodeList(list):

    def __str__(self):
        f = StringIO()
        # printcodelist(self, f)
        return f.getvalue()


class Code:
    pass


