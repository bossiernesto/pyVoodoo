from pyVoodoo.assembler import *
import unittest

class TestDissasemble(unittest.TestCase):

    def test_compile_simple_pyfile(self):
        raw_code = b'd\x00\x00d\x01\x00l\x00\x00Z\x00\x00Gd\x02\x00d\x03\x00\x84\x00\x00d\x03\x00e\x01\x00\x83\x03\x00Z\x02\x00e\x02\x00\x83\x00\x00Z\x03\x00e\x03\x00j\x04\x00\x83\x00\x00\x01e\x05\x00e\x03\x00j\x03\x00\x83\x01\x00\x01d\x01\x00S'
        code =PythonParser()._parse_from_py('fixture/a.py', False)
        self.assertEquals(raw_code, code.co_code)
        self.assertEquals(1, code.co_firstlineno)
        self.assertEquals(64, code.co_flags)
        self.assertEquals(b'\x0c\x03\x16\x07\t\x01\n\x01', code.co_lnotab)
        self.assertEquals(4, code.co_stacksize)
        self.assertEquals(tuple(), code.co_varnames)

    def test_compile_simple_expression(self):
        source = """x=1
y=2
print(x+y)"""
        code = PythonParser().convertFromSource(source, False)
        self.assertEquals(b'd\x00\x00Z\x00\x00d\x01\x00Z\x01\x00e\x02\x00e\x00\x00e\x01\x00\x17\x83\x01\x00\x01d\x02\x00S', code.co_code)
        self.assertEquals((1,2,None), code.co_consts)
        self.assertEquals(1, code.co_firstlineno)
        self.assertEquals(64, code.co_flags)
        self.assertEquals(b'\x06\x01\x06\x01', code.co_lnotab)
        self.assertEquals(3, code.co_stacksize)
        self.assertEquals(('x', 'y', 'print'), code.co_names)
        self.assertEquals(tuple(), code.co_varnames)

