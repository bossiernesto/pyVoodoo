import types

class InstanceMutator:

    @staticmethod
    def unbind(f):
        """
        Function that unbinds a given function if it's actually binded to an object. If it's not binded to an object it'll
        raise a TypeError Exception

        :param f: function to unbind from an object
        :type f: function
        :raises: TypeError
        """
        self = getattr(f, '__self__', None)
        if self is not None and not isinstance(self, types.ModuleType) and not isinstance(self, type):
            if hasattr(f, '__func__'):
                return f.__func__
            return getattr(type(f.__self__), f.__name__)
        raise TypeError('not a bound method')

    @staticmethod
    def bind(f, obj,new_f_name):
        obj.__dict__[new_f_name] = types.MethodType(f, obj, obj.__class__)

    @staticmethod
    def rebind(f, obj,new_f_name=None):
        InstanceMutator.bind(InstanceMutator.unbind(f), obj,new_f_name)
