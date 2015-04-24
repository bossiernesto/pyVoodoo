import opcode
from collections import OrderedDict
import dis
import types
import marshal
import binascii
from array import array
from pyVoodoo.assemblerExceptions import *
import sys
from pyVoodoo.ir import with_name


def listify(gen):
    "Convert a generator into a function which returns a list"

    def patched(*args, **kwargs):
        return list(gen(*args, **kwargs))

    return patched


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
# make ops global
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


def opcode_by_name(name):
    try:
        return opmap[name]
    except KeyError as e:
        raise InexistentInstruction(e)


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
                self.dump(const, indent + '   ')
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
                print("%s   %s" % (indent, h[i:i + 60]))


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
            # Add a comment to this line
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


class Code(object):
    def __init__(self):
        self.argcount = 0
        self.stacksize = 0
        self.flags = CO_OPTIMIZED | CO_NEWLOCALS
        self.filename = '<generated code>'
        self.name = '<lambda>'
        self.firstlineno = 0
        self.freevars = ()
        self.cellvars = ()
        self.code = array('B')
        self.consts = [None]
        self.names = []
        self.varnames = []
        self.lnotab = array('B')
        self.stacksize = 0

        self.emit_bytecode = self.code.append
        self.blocks = []
        self.stack_history = []

        self._ss = 0

    def set_stack_size(self, size):
        if size < 0:  # Check lower boundary
            raise AssertionError("Stack underflow")
        if size > self.stacksize:
            self.stacksize = size
        bytes = len(self.code) - len(self.stack_history) + 1
        if bytes > 0:
            self.stack_history.extend([self._ss] * bytes)
        self._ss = size

    def get_stack_size(self):
        return self._ss

    stack_size = property(get_stack_size, set_stack_size)

    def to_bytecode_string(self):
        return bytes(self.code)

    def find_first_opcode_index(self, op):
        results = self.find_opcode_index(op)
        return results[0]

    @listify
    def find_opcode_index(self, op):
        _op = op
        if not isinstance(op, int):
            _op = opcode_by_name(op)

        i = 0
        while i < len(self.code):
            if self.code[i] == _op:
                yield i
            if self.code[i] < opcode.HAVE_ARGUMENT:  # 90, as mentioned earlier
                i += 1
            else:
                i += 3

    def emit_arg(self, op, arg):
        emit = self.emit_bytecode
        if arg > 0xFFFF:
            emit(opcode.EXTENDED_ARG)
            emit((arg >> 16) & 255)
            emit((arg >> 24) & 255)
        emit(op)
        emit(arg & 255)
        emit((arg >> 8) & 255)

    def LOAD_CONST(self, const):
        self.stackchange((0, 1))
        pos = 0
        hashable = True
        try:
            hash(const)
        except TypeError:
            hashable = False
        while 1:
            try:
                arg = self.consts.index(const, pos)
                it = self.consts[arg]
            except ValueError:
                arg = len(self.consts)
                self.consts.append(const)
                break
            else:
                if type(it) is type(const) and (hashable or it is const):
                    break
            pos = arg + 1
            continue
        return self.emit_arg(opmap['LOAD_CONST'], arg)

    def RETURN_VALUE(self):
        self.stackchange((1, 0))
        self.emit_bytecode(opmap['RETURN_VALUE'])
        self.stack_unknown()

    def LOAD_FAST(self, const_name):
        self.stackchange(tuple(_se.LOAD_FAST))
        try:
            arg = self.varnames.index(const_name)
        except ValueError:
            self.STORE_FAST(const_name)
            arg = self.varnames.index(const_name)

        self.emit_arg(opmap['LOAD_FAST'], arg)

    LOAD_DEREF = LOAD_FAST

    def STORE_FAST(self, const_name):
        self.stackchange(tuple(_se.STORE_FAST))
        try:
            arg = self.varnames.index(const_name)
        except ValueError:
            arg = len(self.varnames)
            self.varnames.append(const_name)
        self.emit_arg(opmap['STORE_FAST'], arg)

    def stackchange(self, *tuple_mod):
        (inputs, outputs) = tuple_mod[0]
        if self._ss is None:
            raise AssertionError("Unknown stack size at this location")
        self.stack_size -= inputs
        self.stack_size += outputs

    def stack_unknown(self):
        self._ss = None


    def __getattr__(self, name):
        def _missing(*args, **kwargs):
            message = "A missing method was called\r\n"
            message += "The object was {0}, the method was {1} \r\n".format(self, name)
            message += "It was called with {0} and {1} as arguments\r\n".format(args, kwargs)
            raise AssemblerBytecodeException(message)

        return _missing


class _se(object):
    """Quick way of defining static stack effects of opcodes"""
    POP_TOP = END_FINALLY = POP_JUMP_IF_FALSE = POP_JUMP_IF_TRUE = 1, 0
    ROT_TWO = 2, 2
    ROT_THREE = 3, 3
    ROT_FOUR = 4, 4
    DUP_TOP = 1, 2
    UNARY_POSITIVE = UNARY_NEGATIVE = UNARY_NOT = UNARY_CONVERT = \
        UNARY_INVERT = GET_ITER = LOAD_ATTR = IMPORT_FROM = 1, 1

    BINARY_POWER = BINARY_MULTIPLY = BINARY_DIVIDE = BINARY_FLOOR_DIVIDE = \
        BINARY_TRUE_DIVIDE = BINARY_MODULO = BINARY_ADD = BINARY_SUBTRACT = \
        BINARY_SUBSCR = BINARY_LSHIFT = BINARY_RSHIFT = BINARY_AND = \
        BINARY_XOR = BINARY_OR = COMPARE_OP = 2, 1

    INPLACE_POWER = INPLACE_MULTIPLY = INPLACE_DIVIDE = \
        INPLACE_FLOOR_DIVIDE = INPLACE_TRUE_DIVIDE = INPLACE_MODULO = \
        INPLACE_ADD = INPLACE_SUBTRACT = INPLACE_LSHIFT = INPLACE_RSHIFT = \
        INPLACE_AND = INPLACE_XOR = INPLACE_OR = 2, 1

    SLICE_0, SLICE_1, SLICE_2, SLICE_3 = \
        (1, 1), (2, 1), (2, 1), (3, 1)
    STORE_SLICE_0, STORE_SLICE_1, STORE_SLICE_2, STORE_SLICE_3 = \
        (2, 0), (3, 0), (3, 0), (4, 0)
    DELETE_SLICE_0, DELETE_SLICE_1, DELETE_SLICE_2, DELETE_SLICE_3 = \
        (1, 0), (2, 0), (2, 0), (3, 0)

    STORE_SUBSCR = 3, 0
    DELETE_SUBSCR = STORE_ATTR = 2, 0
    DELETE_ATTR = STORE_DEREF = 1, 0
    PRINT_EXPR = PRINT_ITEM = PRINT_NEWLINE_TO = IMPORT_STAR = 1, 0
    RETURN_VALUE = YIELD_VALUE = STORE_NAME = STORE_GLOBAL = STORE_FAST = 1, 0
    PRINT_ITEM_TO = LIST_APPEND = 2, 0

    LOAD_LOCALS = LOAD_CONST = LOAD_NAME = LOAD_GLOBAL = LOAD_FAST = \
        LOAD_CLOSURE = LOAD_DEREF = IMPORT_NAME = BUILD_MAP = 0, 1

    EXEC_STMT = BUILD_CLASS = 3, 0
    JUMP_IF_TRUE = JUMP_IF_FALSE = \
        JUMP_IF_TRUE_OR_POP = JUMP_IF_FALSE_OR_POP = 1, 1


if sys.version >= "2.5":
    _se.YIELD_VALUE = 1, 1

stack_effects = [(0, 0)] * 256

for name in opname.values():
    op = opmap[name]
    name = name.replace('+', '_')

    if hasattr(_se, name):
        # update stack effects table from the _se class
        stack_effects[op] = getattr(_se, name)

    if not hasattr(Code, name):
        # Create default method for Code class
        if op >= opcode.HAVE_ARGUMENT:
            def do_op(self, arg, op=op, se=stack_effects[op]):
                self.stackchange(se);
                self.emit_arg(op, arg)
        else:
            def do_op(self, op=op, se=stack_effects[op]):
                self.stackchange(se);
                self.emit(op)

        setattr(Code, name, with_name(do_op, name))