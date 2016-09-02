from types import FunctionType
import inspect

def getPublicMethods(cls):
    return [(x, y) for x, y in cls.__dict__.items() if (
                type(y) == FunctionType and
                not x.startswith('_')
                )]
# end def

def copyWrapAPI(cls_from, cls_to, attr_str='model'):
    """Use same `eval` trick as decorator module on PyPi to match
    function signatures
    see also: https://emptysqua.re/blog/copying-a-python-functions-signature/

    But this supports type annotations too now

    maybe try to use functools.update_wrapper in the future
    """
    to_name = cls_to.__qualname__
    module = cls_to.__module__
    self_attr_str = 'self.%s' % (attr_str)
    for name, f in getPublicMethods(cls_from):
        # 1. Copy call signature Python 3.5 only use getargspec, formatargspec for 2.7
        argspec_1 = inspect.signature(f)
        formatted_args_1 = str(argspec_1)
        # print(formatted_args_1)
        # strip annotations from parameters
        argspec_2 = list(argspec_1.parameters)
        argspec_2[0] = (self_attr_str, )    # swap in reference
        # print(argspec_2)
        formatted_args_2 = ', '.join([x[0] if isinstance(x, tuple) else x for x in argspec_2])

        # print(formatted_args_2)
        f_wrapper_str = 'def func_wrapper%s: \r\n    return func(%s)' % ( formatted_args_1,
                                                formatted_args_2)

        # print(f_wrapper_str)
        # 2. Create wrapper function
        code = compile(f_wrapper_str, '<string>', 'exec')
        ns = {'func': f}
        exec(code, ns)
        f_wrapper = ns['func_wrapper']

        # 3. set wrapper function attributes
        f_wrapper.__name__ = name
        f_wrapper.__qualname__ = '%s.%s' % (to_name, name)
        f_wrapper.__module__ = module
        for attr in ['__doc__', '__annotations__']:
            setattr(f_wrapper, attr, getattr(f, attr))
        # print("anno", f.__annotations__)
        # 4. Assign wrapper function to the class
        setattr(cls_to, name, f_wrapper)
# end def

if __name__ == '__main__':
    class Foo(object):

        def awesome(self, a: int):
            print(7777)

        def dope(self):
            return 9999

        def _soPrivate(self):
            pass

    class Bar(object):
        def __init__(self, model):
            self.model = model

    copyWrapAPI(Foo, Bar)
    print(getPublicMethods(Foo))
    print(getPublicMethods(Bar))
    print(Foo.dope(8))
