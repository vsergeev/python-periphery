import inspect


STR_OKAY = " [\x1b[1;32m OK \x1b[0m]"
STR_FAIL = " [\x1b[1;31mFAIL\x1b[0m]"


def ptest():
    frame = inspect.stack()[1]
    function, lineno = frame[3], frame[2]
    print("\n\nStarting test {:s}():{:d}".format(function, lineno))


def pokay(msg):
    print("{:s}  {:s}".format(STR_OKAY, msg))


def passert(name, condition):
    frame = inspect.stack()[1]
    filename, function, lineno = frame[1].split('/')[-1], frame[3], frame[2]
    print("{:s}  {:s} {:s}():{:d}  {:s}".format(STR_OKAY if condition else STR_FAIL, filename, function, lineno, name))
    assert condition


class AssertRaises(object):
    def __init__(self, name, exception_type):
        self.name = name
        self.exception_type = exception_type

    def __enter__(self):
        return self

    def __exit__(self, t, value, traceback):
        frame = inspect.stack()[1]
        filename, function, lineno = frame[1].split('/')[-1], frame[3], frame[2]

        if not isinstance(value, self.exception_type):
            print("{:s}  {:s} {:s}():{:d}  {:s}".format(STR_FAIL, filename, function, lineno, self.name))
            return False

        print("{:s}  {:s} {:s}():{:d}  {:s}".format(STR_OKAY, filename, function, lineno, self.name))
        return True
