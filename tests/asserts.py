class AssertRaises(object):
    def __init__(self, exception_type):
        self.exception_type = exception_type

    def __enter__(self):
        return self

    def __exit__(self, t, value, traceback):
        if isinstance(value, self.exception_type):
            return True

        return False
