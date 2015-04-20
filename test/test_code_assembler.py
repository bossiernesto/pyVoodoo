from unittest import *
from pyVoodoo.assembler import Code

class ByteCodeAssembler(TestCase):

    def setUp(self):
        code = Code()

    def test_write_simple_statement(self):
        self.assertTrue(True)

