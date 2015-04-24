from unittest import TestCase
from pyVoodoo.assembler import Code, opcode_by_name
from test.fixture.code_test_fixture import *
from pyVoodoo import AssemblerBytecodeException


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
        self.assertEqual([100, 1, 0, 125, 0, 0], self.code._code_as_list())

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


        self.assertRaises(AssemblerBytecodeException, self.code.DUP_TOP)

    def test_top_opcodes(self):
        self.code.LOAD_CONST(1)
        self.code.DUP_TOP()
        self.code.DUP_TOP()

        self.assertEqual([100, 1, 0, 4, 4], self.code._code_as_list())
        self.assertEqual(3, self.code.stack_size)

    def test_unary_index_lookup(self):
        self.code.LOAD_CONST(1)
        for i in range(3):
            self.code.DUP_TOP()

        self.assertEqual(3, self.code.find_first_opcode_index(4))
        self.assertEqual([3, 4, 5], self.code.find_opcode_index(4))

    # Find Instruction tests
    def test_missing_method(self):
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

    # Opcode testing
    def test_POP_TOP_failure_instruction(self):  #1
        self.assertRaises(AssemblerBytecodeException, self.code.POP_TOP)

    def test_POP_TOP_instruction(self):  #1
        self.code.LOAD_CONST(514)
        self.assertEqual(1, self.code.stack_size)
        self.assertEqual([100, 1, 0], self.code._code_as_list())

        self.code.POP_TOP()
        self.assertEqual(0, self.code.stack_size)
        self.assertEqual([100, 1, 0, 1], self.code._code_as_list())
        self.assertEqual([0, 1, 1, 1], self.code.stack_history)

    def test_ROT_TWO_failure(self):  #2
        self.code.LOAD_CONST(4242)
        self.assertRaises(AssemblerBytecodeException, self.code.ROT_TWO)

    def test_ROT_TWO_instruction(self):  #2
        self.code.LOAD_CONST(3442)
        self.code.LOAD_CONST(2211)
        self.assertEqual([100, 1, 0, 100, 2, 0], self.code._code_as_list())
        self.assertEqual([None, 3442, 2211], self.code.consts)

        self.code.ROT_TWO()
        self.assertEqual([100, 1, 0, 100, 2, 0, 2], self.code._code_as_list())
        self.assertEqual([None, 3442, 2211], self.code.consts)

    def test_ROT_THREE_failure(self):  #3
        self.code.LOAD_CONST(4242)
        self.code.LOAD_CONST(2211)
        self.assertRaises(AssemblerBytecodeException, self.code.ROT_THREE)

    def test_ROT_THREE_instruction(self):  #3
        self.code.LOAD_CONST(3442)
        self.code.LOAD_CONST(2211)
        self.code.LOAD_CONST(1)
        self.assertEqual([100, 1, 0, 100, 2, 0, 100, 3, 0], self.code._code_as_list())
        self.assertEqual([None, 3442, 2211, 1], self.code.consts)

        self.code.ROT_THREE()
        self.assertEqual([100, 1, 0, 100, 2, 0, 100, 3, 0, 3], self.code._code_as_list())
        self.assertEqual([None, 3442, 2211, 1], self.code.consts)

    def test_DUP_TOP_error_instruction(self):  #4

        self.code.LOAD_CONST(1)

        self.assertRaises(AssemblerBytecodeException, self.code.DUP_TOP_TWO)

    def test_DUP_TOP_instruction(self):  #4
        self.code.LOAD_CONST(1456)
        self.code.LOAD_CONST(134)
        self.code.DUP_TOP_TWO()

        self.assertEqual(4, self.code.stack_size)
        self.assertEqual([100, 1, 0, 100, 2, 0, 5], self.code._code_as_list())

    def test_DUP_TOP_TWO_failure(self):#5
        self.code.LOAD_CONST(23425)
        self.assertRaises(AssemblerBytecodeException, self.code.DUP_TOP_TWO)

    def test_DUP_TOP_TWO_instruction(self):#5
        self.code.LOAD_CONST(341)
        self.code.LOAD_CONST(4828)
        self.code.DUP_TOP_TWO()
        self.assertEqual([100, 1, 0, 100, 2, 0, 5], self.code._code_as_list())
        self.assertEqual(4, self.code.stack_size)
        self.assertEqual([None, 341, 4828], self.code.consts)

    def test_NOP_opcode(self): #9
        self.code.NOP()
        self.assertEqual([9], list(self.code.code))
        self.assertEqual(0, self.code.stack_size)

    def test_UNARY_POSITIVE_failure(self):#10
        #TOS = +TOS
        self.assertRaises(AssemblerBytecodeException, self.code.UNARY_POSITIVE)

    def test_UNARY_POSITIVE_instruction(self):#10
        self.code.LOAD_CONST(-144)
        self.code.UNARY_POSITIVE()

        self.assertEqual([100, 1, 0, 10], self.code._code_as_list())
        self.assertEqual(1, self.code.stack_size)
        self.assertEqual([None, -144], self.code.consts)

    def tets_UNARY_NEGATIVE_failure(self):#11
        #TOS = -TOS
        self.assertRaises(AssemblerBytecodeException, self.code.UNARY_NEGATIVE)

    def test_UNARY_NEGATIVE_instruction(self):#11
        self.code.LOAD_CONST(1344)
        self.code.UNARY_NEGATIVE()

        self.assertEqual([100, 1, 0, 11], self.code._code_as_list())
        self.assertEqual(1, self.code.stack_size)
        self.assertEqual([None, 1344], self.code.consts)

    def test_UNARY_NOT_failure(self):#12
        #TOS = not TOS
        self.assertRaises(AssemblerBytecodeException, self.code.UNARY_NOT)

    def test_UNARY_NOT_instruction(self):#12
        self.code.LOAD_CONST(146)
        self.code.UNARY_NOT()

        self.assertEqual([100, 1, 0, 12], self.code._code_as_list())
        self.assertEqual(1, self.code.stack_size)
        self.assertEqual([None, 146], self.code.consts)

    def test_UNARY_INVERT_failure(self):#15
        #TOS = ~TOS
        self.assertRaises(AssemblerBytecodeException, self.code.UNARY_INVERT)

    def test_UNARY_INVERT_instruction(self):#15
        self.code.LOAD_CONST(1)
        self.code.UNARY_INVERT()

        self.assertEqual([100, 1, 0, 15], self.code._code_as_list())
        self.assertEqual(1, self.code.stack_size)
        self.assertEqual([None, 1], self.code.consts)

    #TODO: continue on instr. BINARY_POWER -> 19