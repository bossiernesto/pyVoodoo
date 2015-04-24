from unittest import TestCase
from pyVoodoo.assembler import Code, opcode_by_name
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


    def test_code_store_big_index(self):
        for i in range(65539):
            self.code.varnames.append(None)
        self.code.LOAD_CONST(1)
        self.code.LOAD_FAST(1)

        self.assertEqual([100, 1, 0, 144, 1, 0, 125, 3, 0, 144, 1, 0, 124, 3, 0], list(self.code.code))
        from pyVoodoo.assemblerExceptions import InexistentInstruction

        self.assertRaises(InexistentInstruction, self.code.find_opcode_index, 'EXTENDED_ARG')
        self.assertEqual([6], self.code.find_opcode_index(125))
        self.assertEqual([3, 9], self.code.find_opcode_index(144))

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

    def test_fail_varname_value(self):
        self.code.LOAD_CONST(1)
        self.code.LOAD_FAST('b')  # Will fail, STORE_FAST('b') is added to the code

        self.assertIn('b', self.code.varnames)
        self.assertEqual([100, 1, 0, 125, 0, 0, 124, 0, 0], list(self.code.code))

    def test_rescue_varname_creation(self):
        self.code.LOAD_CONST(1)
        self.code.STORE_FAST('b')

        self.assertIn('b', self.code.varnames)
        self.assertEqual([100, 1, 0, 125, 0, 0], list(self.code.code))

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

    def test_error_stack_underflow(self):
        from pyVoodoo import AssemblerBytecodeException

        self.assertRaises(AssemblerBytecodeException, self.code.DUP_TOP)

    def test_top_opcodes(self):
        self.code.LOAD_CONST(1)
        self.code.DUP_TOP()
        self.code.DUP_TOP()

        self.assertEqual([100, 1, 0, 4, 4], list(self.code.code))
        self.assertEqual(3, self.code.stack_size)

    def test_unary_index_lookup(self):
        self.code.LOAD_CONST(1)
        for i in range(3):
            self.code.DUP_TOP()

        self.assertEqual(3, self.code.find_first_opcode_index(4))
        self.assertEqual([3, 4, 5], self.code.find_opcode_index(4))

    def test_duptwo_error_opcode(self):
        from pyVoodoo import AssemblerBytecodeException
        self.code.LOAD_CONST(1)

        self.assertRaises(AssemblerBytecodeException, self.code.DUP_TOP_TWO)

    def test_duptwo_valid(self):
        self.code.LOAD_CONST(1456)
        self.code.LOAD_CONST(134)
        self.code.DUP_TOP_TWO()

        self.assertEqual(4, self.code.stack_size)
        self.assertEqual([100, 1, 0, 100, 2, 0, 5], list(self.code.code))

    # Find Instruction tests
    def test_missing_method(self):
        from pyVoodoo import AssemblerBytecodeException

        self.assertRaises(AssemblerBytecodeException, self.code.missingmethodcalled)

    def test_find_instruction(self):
        self.code.LOAD_CONST(42)
        self.code.RETURN_VALUE()

        self.assertEqual([0], self.code.find_opcode_index(100))
        self.assertEqual([3], self.code.find_opcode_index(83))

    def test_find_instruction_load(self):
        self.code.LOAD_CONST(1)
        self.code.LOAD_FAST('b')

        self.assertEqual([6], self.code.find_opcode_index(124))
        self.assertEqual(6, self.code.find_first_opcode_index(124))
        self.assertEqual([6], self.code.find_opcode_index('LOAD_FAST'))

        self.assertEqual([0], self.code.find_opcode_index('LOAD_CONST'))

        from pyVoodoo.assemblerExceptions import InexistentInstruction

        self.assertRaises(InexistentInstruction, self.code.find_opcode_index, 'STOR_FAST')


    def test_find_instruction_by_name(self):
        self.assertEqual(125, opcode_by_name('STORE_FAST'))

    def test_find_inexistent_bytecode_name(self):
        from pyVoodoo.assemblerExceptions import InexistentInstruction

        self.assertRaises(InexistentInstruction, opcode_by_name, 'STOR_FAST')