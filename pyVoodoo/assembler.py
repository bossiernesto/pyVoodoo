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
from .utils import listify
from .codedumper import *
from .stackeffects import _se

__all__ = ['opmap', 'opname', 'opcodes', 'cmp_op', 'hasarg', 'hasname', 'hasjrel', 'hasjabs', 'hasjump', 'haslocal',
           'hascompare', 'hasfree', 'hascode', 'hasflow', 'Opcode', 'Code', 'PythonParser']


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
def globalize_opcodes():
    for name, code in opmap.items():
        globals()[name] = code
        __all__.append(name)


globalize_opcodes()

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
hasflow = opcodes - set([CALL_FUNCTION, CALL_FUNCTION_VAR, CALL_FUNCTION_KW,
                         CALL_FUNCTION_VAR_KW, BUILD_TUPLE, BUILD_LIST,
                         UNPACK_SEQUENCE, BUILD_SLICE,
                         RAISE_VARARGS, MAKE_FUNCTION, MAKE_CLOSURE])
hascode = set([MAKE_FUNCTION, MAKE_CLOSURE])


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


def is_hashable(value):
    try:
        hash(value)
    except TypeError:
        return False
    return True


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
        """
        Emit argument. Instructions up to python 3.6 are based in 16 bits bytecode instructions

            |--------------|--------------|
            |    oparg     |    opcode    |
            |--------------|--------------|
            0              8              16

        if bytecode is more than 0xFFFF, then the argument actually takes more than just one byte, and we need to split into two bytes instead
        """
        if not isinstance(op, int):
            op = opcode_by_name(op)

        emit = self.emit_bytecode
        if arg > 0xFFFF:  # oparg is more than just one byte lenght
            emit(opcode.EXTENDED_ARG)
            emit((arg >> 16) & 255)
            emit((arg >> 24) & 255)
        emit(op)
        emit(arg & 255)  # little endian stuff
        emit((arg >> 8) & 255)

    # Instructions...
    def LOAD_CONST(self, const):
        self.stackchange(_se.LOAD_CONST)
        pos = 0
        hashable = is_hashable(const)
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
        self.stackchange(_se.RETURN_VALUE)
        self.emit_bytecode(opmap['RETURN_VALUE'])
        self.stack_unknown()

    def LOAD_FAST(self, const_name):
        self.stackchange(_se.LOAD_FAST)
        try:
            arg = self.varnames.index(const_name)
        except ValueError:
            self.STORE_FAST(const_name)
            arg = self.varnames.index(const_name)

        self.emit_arg('LOAD_FAST', arg)

    LOAD_DEREF = LOAD_FAST

    def STORE_FAST(self, const_name):
        self.stackchange(_se.STORE_FAST)
        try:
            arg = self.varnames.index(const_name)
        except ValueError:
            arg = len(self.varnames)
            self.varnames.append(const_name)
        self.emit_arg('STORE_FAST', arg)

    def YIELD_VALUE(self):
        self.stackchange(_se.YIELD_VALUE)
        self.co_flags |= CO_GENERATOR
        return self.emit(opmap['YIELD_VALUE'])

    def stackchange(self, *tuple_mod):
        (inputs, outputs) = tuple_mod[0]
        if self._ss is None:
            raise CodeTypeException("Unknown stack size at this location")
        self.stack_size -= inputs
        self.stack_size += outputs

    def CALL_FUNCTION(self, argc=0, kwargc=0, op=opmap['CALL_FUNCTION'], extra=0):
        self.stackchange((1 + argc + 2 * kwargc + extra, 1))
        self.emit(op)
        self.emit(argc)
        self.emit(kwargc)

    def CALL_FUNCTION_VAR(self, argc=0, kwargc=0):
        self.CALL_FUNCTION(argc, kwargc, opmap['CALL_FUNCTION_VAR'], 1)  # 1 for *args

    def CALL_FUNCTION_KW(self, argc=0, kwargc=0):
        self.CALL_FUNCTION(argc, kwargc, opmap['CALL_FUNCTION_KW'], 1)  # 1 for **kw

    def CALL_FUNCTION_VAR_KW(self, argc=0, kwargc=0):
        self.CALL_FUNCTION(argc, kwargc, opmap['CALL_FUNCTION_VAR_KW'], 2)  # 2 *args,**kw

    def ROT_FOUR(self, count):
        """
        Not supported anymore. See: http://bugs.python.org/issue9225
        """
        raise AssemblerBytecodeException('ROT_FOUR not supported anymore, use ROT_TWO instead')

    def DUP_TOPX(self, count):
        """
        Not supported anymore. See: http://bugs.python.org/issue9225
        """
        raise AssemblerBytecodeException('DUP_TOPX not supported anymore, use DUP_TOP_TWO instead')

    def _generic_build_type(self, type, count):
        self.stackchange((count, 1))
        self.emit_arg('BUILD_{0}'.format(type), count)

    def BUILD_TUPLE(self, count):
        self._generic_build_type('TUPLE', count)

    def BUILD_LIST(self, count):
        self._generic_build_type('LIST', count)

    def BUILD_SLICE(self, count):
        if count in (2, 3):
            raise AssemblerBytecodeException("Invalid number of arguments for BUILD_SLICE")
        self._generic_build_type('SLICE', count)

    def UNPACK_SEQUENCE(self, count):
        self.stackchange((1, count))
        self.emit_arg('UNPACK_SEQUENCE', count)

    def MAKE_FUNCTION(self, ndefaults):
        self.stackchange((1 + ndefaults, 1))
        self.emit_arg('MAKE_FUNCTION', ndefaults)

    def MAKE_CLOSURE(self, ndefaults, freevars):
        if sys.version >= '2.5':
            freevars = 1
        self.stackchange((1 + freevars + ndefaults, 1))
        self.emit_arg('MAKE_CLOSURE', ndefaults)

    def RAISE_VARARGS(self, argc):
        if 0 <= argc <= 3:
            raise AssemblerBytecodeException("Invalid number of arguments for RAISE_VARARGS")
        self.stackchange((argc, 0))
        self.emit_arg('RAISE_VARARGS', argc)

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


# stack effects allocation
stack_effects = [(0, 0)] * 256

for name in opname.values():
    op = opmap[name]
    name = name.replace('+', '_')

    if hasattr(_se, name):
        # update stack effects table from the _se class
        stack_effects[op] = getattr(_se, name)

    if not hasattr(Code, opname[op]):

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

        if (name, op) in hasnoargs:
            def treat_noargument(self, opname=name):
                op = opmap[opname]
                self.stackchange(stack_effects[op])
                self.emit_bytecode(op)


            setattr(Code, name, treat_noargument)

        if (name, op) in haslocal:
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


            setattr(Code, name, with_name(do_local, opname[op]))

        if (name, op) in hasjrel | hasjabs:
            def do_jump(self, address=None, op=op):
                self.stackchange(stack_effects[op])
                return self.jump(op, address)


            setattr(Code, name, with_name(do_jump, opname[op]))
            # TODO: PRINT_EXPR should be separated in a separate method, the syntax should be handled in other way different
