from unittest import TestCase
from pyVoodoo.assembler import Code
from test.fixture.code_test_fixture import *


class CodeTest(TestCase):
    def setUp(self):
        self.code = Code()

    def test_code_return_function(self):
        self.code.LOAD_CONST(42)
        self.code.RETURN_VALUE()

        self.assertEqual([None, 42], self.code.consts)
        self.assertEqual([100, 1, 0, 83], list(self.code.code))
        self.assertEqual(0, self.code.firstlineno)
        self.assertEqual([], self.code.blocks)
        self.assertEqual(0, self.code.argcount)

    def test_semantic_equivalence_return_function(self):
        expected = test_function.__code__.co_code
        self.code.LOAD_CONST(42)
        self.code.RETURN_VALUE()

        self.assertEqual(list(expected), list(self.code.code))
        self.assertEqual(expected, self.code.to_bytecode_string())

    def test_code_load_return(self):
        self.code.LOAD_CONST(1)
        self.code.STORE_FAST(0)
        self.code.LOAD_FAST(0)
        self.code.RETURN_VALUE()

        self.assertEqual([None, 1], self.code.consts)
        self.assertEqual([100, 1, 0, 125, 0, 0, 124, 0, 0, 83], list(self.code.code))
        self.assertEqual(0, self.code.firstlineno)
        self.assertEqual([], self.code.blocks)
        self.assertEqual(0, self.code.argcount)


    def test_semantically_equivalence_load_return(self):
        self.code.LOAD_CONST(1)
        self.code.STORE_FAST('a')
        self.code.LOAD_FAST('a')
        self.code.RETURN_VALUE()

        expected = load_and_return.__code__.co_code
        self.assertEqual(expected, self.code.to_bytecode_string())
        self.assertEqual(['a'], self.code.varnames)
        self.assertEqual(('a',), load_and_return.__code__.co_varnames)
        self.assertEqual(list(expected), list(self.code.code))
