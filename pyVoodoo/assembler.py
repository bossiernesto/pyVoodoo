import opcode
from collections import OrderedDict
import dis
import marshal
import binascii
from array import array
from pyVoodoo.assemblerExceptions import *
import sys
import types
from .flags import *
from utils import listify
from .stackeffects import *


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

hasnoargs = set(x for x in sorted(raw_opmap.values()) if x.code() < opcode.HAVE_ARGUMENT)
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
    CO_OPTIMIZED: "OPTIMIZED",
    CO_NEWLOCALS: "NEWLOCALS",
    CO_VARARGS: "VARARGS",
    CO_VARKEYWORDS: "VARKEYWORDS",
    CO_NESTED: "NESTED",
    CO_GENERATOR: "GENERATOR",
    CO_NOFREE: "NOFREE",
    CO_GENERATOR_ALLOWED: "GENERATOR_ALLOWED",
}


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

    def _code_as_list(self):
        return list(self.code)

    def set_stack_size(self, size):
        if size < 0:  # Check lower boundary
            raise AssemblerBytecodeException("Stack underflow")
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
        if not isinstance(op, int):
            op = opcode_by_name(op)

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
        return self.emit_arg('LOAD_CONST', arg)

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

        self.emit_arg('LOAD_FAST', arg)

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


def with_name(f, name):
    try:
        f.__name__ = name
        return f
    except (TypeError, AttributeError):
        return types.FunctionType(
            f.func_code, f.func_globals, name, f.func_defaults, f.func_closure
        )


for name, value in hasnoargs:
    if not hasattr(Code, name):
        def threat_noargument(self, opname=name):
            op = opmap[opname]
            self.stackchange(tuple(stack_effects[op]))
            self.emit_bytecode(op)


        setattr(Code, name, threat_noargument)

# stack effects allocation
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
                self.stackchange(se)
                self.emit_arg(op, arg)
        else:
            def do_op(self, op=op, se=stack_effects[op]):
                self.stackchange(se)
                self.emit(op)

        setattr(Code, name, with_name(do_op, name))

for op in haslocal:
    if not hasattr(Code, opname[op]):
        def do_local(self, varname, op=op):
            if not self.co_flags & CO_OPTIMIZED:
                raise AssertionError(
                    "co_flags must include CO_OPTIMIZED to use fast locals"
                )
            self.stackchange(stack_effects[op])
            try:
                arg = self.co_varnames.index(varname)
            except ValueError:
                arg = len(self.co_varnames)
                self.co_varnames.append(varname)
            self.emit_arg(op, arg)


        setattr(Code, opname[op], with_name(do_local, opname[op]))

for op in hasjrel + hasjabs:
    if not hasattr(Code, opname[op]):
        def do_jump(self, address=None, op=op):
            self.stackchange(stack_effects[op])
            return self.jump(op, address)


        setattr(Code, opname[op], with_name(do_jump, opname[op]))

        # TODO: PRINT_EXPR should be separated in a separate method, the syntax should be handled in other way different
