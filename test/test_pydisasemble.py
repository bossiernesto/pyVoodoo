from pyVoodoo.assembler import *
import unittest

class TestDissasemble(unittest.TestCase):

    def test_compile_simple_pyfile(self):
        raw_code = b'd\x00\x00d\x01\x00l\x00\x00Z\x00\x00Gd\x02\x00d\x03\x00\x84\x00\x00d\x03\x00e\x01\x00\x83\x03\x00Z\x02\x00e\x02\x00\x83\x00\x00Z\x03\x00e\x03\x00j\x04\x00\x83\x00\x00\x01e\x05\x00e\x03\x00j\x03\x00\x83\x01\x00\x01d\x01\x00S'
        code =PythonParser()._parse_from_py('fixture/a.py', False)
        self.assertEqual(raw_code, code.co_code)
        self.assertEqual(1, code.co_firstlineno)
        self.assertEqual(64, code.co_flags)
        self.assertEqual(b'\x0c\x03\x16\x07\t\x01\n\x01', code.co_lnotab)
        self.assertEqual(4, code.co_stacksize)
        self.assertEqual(tuple(), code.co_varnames)

    def test_compile_simple_expression(self):
        source = """x=1
y=2
print(x+y)"""
        code = PythonParser().convertFromSource(source, False)
        self.assertEqual(b'd\x00\x00Z\x00\x00d\x01\x00Z\x01\x00e\x02\x00e\x00\x00e\x01\x00\x17\x83\x01\x00\x01d\x02\x00S', code.co_code)
        self.assertEqual((1,2,None), code.co_consts)
        self.assertEqual(1, code.co_firstlineno)
        self.assertEqual(64, code.co_flags)
        self.assertEqual(b'\x06\x01\x06\x01', code.co_lnotab)
        self.assertEqual(3, code.co_stacksize)
        self.assertEqual(('x', 'y', 'print'), code.co_names)
        self.assertEqual(tuple(), code.co_varnames)

