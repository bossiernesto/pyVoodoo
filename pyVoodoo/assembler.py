import opcode
from _io import StringIO
from collections import OrderedDict
import dis
import types
import marshal
import binascii


class Opcode(tuple):
    """An int which represents an opcode - has a nicer repr."""

    def __repr__(self):
        return "{0}: {1}".format(self[0], self[1])

    def opcode_name(self):
        return self[0]

    def code(self):
        return self[1]


raw_opmap = dict((name.replace('+', '_'), Opcode((name, code)))
             for name, code in opcode.opmap.items()
             if name != 'EXTENDED_ARG')
opmap = OrderedDict(sorted(raw_opmap.values()))
opname = dict((code, name) for name, code in opmap.items())
opcodes = set(opname)
make_opcode = lambda code: Opcode((opname[code], code))

# CMP
cmp_op = opcode.cmp_op
#make ops global
hasarg = set(x for x in raw_opmap.values() if x.code() >= opcode.HAVE_ARGUMENT)
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
CO_OPTIMIZED = 0x0001  # use LOAD/STORE_FAST instead of _NAME
CO_NEWLOCALS = 0x0002  # only cleared for module/exec code
CO_VARARGS = 0x0004
CO_VARKEYWORDS = 0x0008
CO_NESTED = 0x0016  # ???
CO_GENERATOR = 0x0032
CO_NOFREE = 0x0064  # set if no free or cell vars
CO_GENERATOR_ALLOWED = 0x0128  # unused


class PersistorException(Exception):
    pass


class Persistor(object):
    def to_code_type(self, instance):
        if not isinstance(instance, Code):
            raise PersistorException('Invalid instance type for {0}'.format(instance))
        return types.CodeType(instance.co_argcount, \
                              instance.co_nlocals, \
                              instance.co_stacksize, \
                              instance.co_flags, \
                              instance.co_code, \
                              instance.co_consts, \
                              instance.co_names, \
                              instance.co_varnames, \
                              instance.co_filename, \
                              instance.co_name, \
                              instance.co_firstlineno, \
                              instance.co_lnotab)


class AssemblerBytecodeException(Exception):
    pass


class PythonCodeDumper(object):

    def dump(self, code_object, indent=''):
        print("%scode" % indent)
        indent += '   '
        print("%sargcount %d" % (indent, code_object.co_argcount))
        print("%snlocals %d" % (indent, code_object.co_nlocals))
        print("%sstacksize %d" % (indent, code_object.co_stacksize))
        print("%sflags %04x" % (indent, code_object.co_flags))
        self.show_hex("code", code_object.co_code, indent=indent)
        dis.disassemble(code_object)
        print("%sconsts" % indent)
        for const in code_object.co_consts:
            if type(const) == types.CodeType:
                self.dump(const, indent+'   ')
            else:
                print("   %s%r" % (indent, const))
        print("%snames %r" % (indent, code_object.co_names))
        print("%svarnames %r" % (indent, code_object.co_varnames))
        print("%sfreevars %r" % (indent, code_object.co_freevars))
        print("%scellvars %r" % (indent, code_object.co_cellvars))
        print("%sfilename %r" % (indent, code_object.co_filename))
        print("%sname %r" % (indent, code_object.co_name))
        print("%sfirstlineno %d" % (indent, code_object.co_firstlineno))
        self.show_hex("lnotab", code_object.co_lnotab, indent=indent)

    def show_hex(self, label, h, indent):
        h = binascii.hexlify(h)
        if len(h) < 60:
            print("%s%s %s" % (indent, label, h))
        else:
            print("%s%s" % (indent, label))
            for i in range(0, len(h), 60):
                print("%s   %s" % (indent, h[i:i+60]))

class PythonParser(object):

    def _parse_from_py(self, file, debug=True):
        import py_compile
        fd = py_compile.compile(file)
        return self._parse_from_pyc(fd, debug)

    def _parse_from_pyc(self, file, debug=True):
        import time, struct

        with open(file, 'rb') as fd:
            magic = fd.read(4)
            moddate = fd.read(4)
            modtime = time.asctime(time.localtime(struct.unpack('I', moddate)[0]))
            try:
                code = marshal.load(fd)
                fd.close()
            #Add a comment to this line
            except ValueError:
                fd.seek(0)
                fd.read(8)  # skip magic & date & file size; file size added in Python 3.3
                file_size = fd.read(4)
                if debug:
                    print("magic {0}".format(binascii.hexlify(magic)))
                    print("moddate {0} ({1})".format(binascii.hexlify(moddate), modtime))
                    print("file size {0}".format(file_size))
                code = marshal.load(fd)
        return code

    def convertToAssemblerCode(self, file, debug=False):
        code_object = self._parse_from_py(file)
        return self.parse(code_object)

    def convertFromSource(self, source, compile_toasm=True):
        code_object = compile(source, '<string>', 'exec')
        if not compile_toasm:
            return code_object
        return self.parse(code_object)

    def dump_pyfile(self, file, debug=False):
        code_object = self._parse_from_py(file, debug)
        PythonCodeDumper().dump(code_object)

    def parse(self, code_object):
        pass



class Code:
    pass


