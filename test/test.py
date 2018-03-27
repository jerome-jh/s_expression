import os
import stat
import unittest
import s_expression

def scandir(d):
    ## Developped on ptyhon3.4, no os.scandir()
    ls = os.listdir(d)
    return [ os.path.join(d, l) for l in ls ]

def is_file(s):
    ## Follow symlinks
    return stat.S_ISREG(os.stat(s).st_mode)

class TestSexpression(unittest.TestCase):
    def test_parse_success(self):
        directory = os.path.join('test', 'success')
        for filename in scandir(directory):
            if is_file(filename):
                threw = False
                r = None
                print(filename)
                try:
                    r = s_expression.Parser().loadf(filename)
                except Exception as e:
                    print('Threw', type(e), e)
                    threw = True
                self.assertTrue(type(r) != type(None) and not threw)

    def test_parse_failure(self):
        directory = os.path.join('test', 'failure')
        for filename in scandir(directory):
            if is_file(filename):
                threw = False
                r = None
                print(filename)
                try:
                    r = s_expression.Parser().loadf(filename)
                except Exception as e:
                    print('Threw', type(e), e)
                    threw = True
                ## TODO: should check exception type
                self.assertTrue(type(r) == type(None) and threw)

if __name__ == '__main__':
    unittest.main()
