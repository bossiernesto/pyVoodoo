import PyMetabuilder
import types

class InstanceCodeGenerator:
    def get_object_code_builder(self):
        pass

    def create_function(self, name, number_arguments, filename='<string>', string_code=None):
        code_to_compile = string_code or 'pass'

        object_with_code = compile(string_code, filename, 'exec')


class ObjectCode(object):
    pass


class ObjectCodeBuilder(PyMetabuilder.MetaBuilder.MetaBuilder):
    def __init__(self):
        PyMetabuilder.MetaBuilder.MetaBuilder.__init__(self)
        self.model(ObjectCode)
        self.property('co_argcount', type=int)
        self.property('co_nlocals')
        self.property('co_stacksize')
        self.property('co_flags')
        self.property('co_code')
        self.property('co_consts')
        self.property('co_names')
        self.property('co_varnames')
        self.property('co_filename', type=str)
        self.property('co_name', type=str)
        self.property('co_firstlineno')

    def build(self):
        instance = PyMetabuilder.MetaBuilder.MetaBuilder.build(self)
        return self.to_code_type(instance)

    def to_code_type(self, instance):
        return types.CodeType(instance.co_argcount,\
            instance.co_nlocals,\
            instance.co_stacksize,\
            instance.co_flags,\
            instance.co_code,\
            instance.co_consts,\
            instance.co_names,\
            instance.co_varnames,\
            instance.co_filename,\
            instance.co_name,\
            instance.co_firstlineno,\
            instance.co_lnotab)
