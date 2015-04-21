import unittest
from pyVoodoo import assembler
import opcode as op


class TestOpcodes(unittest.TestCase):
    def setUp(self):
        pass

    def test_raw_opcode_table(self):
        for opcode in assembler.raw_opmap.values():
            self.assertEqual(opcode.code(), op.opmap[opcode.opcode_name()])
            self.assertEqual(opcode.opcode_name(), op.opname[opcode.code()])


    def test_opcode_table(self):
        for code, name in assembler.opname.items():
            self.assertEqual(name, op.opname[code])

    def test_hasopcode(self):
        for opcode in assembler.hasarg:
            self.assertGreaterEqual(opcode.code(), op.HAVE_ARGUMENT)

    def test_has_const(self):
        for opcode in assembler.hasconst:
            self.assertIn(opcode.code(), op.hasconst)
            self.assertEqual(opcode.opcode_name(), op.opname[opcode.code()])

    def test_has_name(self):
        for opcode in assembler.hasname:
            code = opcode.code()
            name = opcode.opcode_name()
            self.assertIn(code, op.hasname)
            self.assertEqual(name, op.opname[code])

    def test_has_jrel(self):
        for opcode in assembler.hasjrel:
            code = opcode.code()
            name = opcode.opcode_name()

            self.assertIn(code, op.hasjrel)
            self.assertEqual(name, op.opname[code])

    def test_has_jabs(self):
        for opcode in assembler.hasjabs:
            code = opcode.code()
            name = opcode.opcode_name()

            self.assertIn(code, op.hasjabs)
            self.assertEqual(name, op.opname[code])

    def test_has_local(self):
        for opcode in assembler.haslocal:
            code = opcode.code()
            name = opcode.opcode_name()

            self.assertIn(code, op.haslocal)
            self.assertEqual(name, op.opname[code])

    def test_has_compare(self):
        for opcode in assembler.hascompare:
            code = opcode.code()
            name = opcode.opcode_name()

            self.assertIn(code, op.hascompare)
            self.assertEqual(name, op.opname[code])

    def test_has_free(self):
        for opcode in assembler.hasfree:
            code = opcode.code()
            name = opcode.opcode_name()

            self.assertIn(code, op.hasfree)
            self.assertEqual(name, op.opname[code])

