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
