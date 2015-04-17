import inspect
import io
import glob #!
import random #!
from string import * #!
import dis

trash = 'abcdefghijklmnopqrstuvwxyz' #!
lengh = random.randrange(10, 20) #!


class Reflector:
    @staticmethod
    def who_am_i():
        return inspect.stack()[1][3]

    @staticmethod
    def who_called_me():
        return inspect.stack()[2][3]


if __name__ == '__main__':

    me = io.open(__file__, 'r')
    for code in me.readlines():
        print(code)

    import ast
    import codegen

    expr = """def foo():
            print("hello world")
    """
    p = ast.parse(expr)

    p.body[0].body = [ast.parse("return 42").body[0]] # Replace function body with "return 42"

    #print(codegen.to_source(p))

    a=dis.dis(Reflector)
    print(a)