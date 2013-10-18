import unittest
from pyVoodoo.InstanceCodeGenerator import *
from pyVoodoo.Reflector import *
from pyVoodoo.InstanceMutator import *

class TestReflector(unittest.TestCase):

    def test_who_am_i(self):
        self.assertEqual('test_who_am_i',Reflector.who_am_i())

    def test_who_called_me(self):
        def some_method():
            return Reflector.who_called_me()
        self.assertEqual('test_who_called_me',Reflector.who_am_i())

class TestCreateFunction(unittest.TestCase):

    def setUp(self):
        self.function_maker = InstanceCodeGenerator()
        self.instance=type('A', (), {})()

    def test_create_function(self):
        f=self.function_maker.create_function('meaning_of_life',1,'print 42')
        InstanceMutator.bind(f,self.instance,'meaning_of_life')
        self.assertEqual(42,self.instance.meaning_of_life())

