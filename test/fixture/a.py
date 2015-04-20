import unittest


class A(object):
    def __init__(self):
        self.a = 0

    def computar(self):
        self.a = self.a + 1

a = A()
a.computar()
print(a.a)