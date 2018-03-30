#!/usr/bin/python3
import sys
import unicodedata

def no_debug(*args):
    pass

if __name__ == '__main__':
    def debug(*args):
        print(*args, file=sys.stderr)
else:
    debug = no_debug

class Atom:
    def __init__(self, string, value, depth=0):
        ## This is the original string as it was parsed
        self.string = string
        ## Value is the interpretation of the string
        ## It can be any Python basic type
        self.__value = value
        self.depth = depth

    def dump(self, initial_depth=None):
        if type(initial_depth) == type(None):
            initial_depth = self.depth
        return Expression.depth_str(self.depth - initial_depth) + type(self).__name__ + ': ' + str(self) + '\n'

    def value(self):
        return self.__value

    def to_list(self):
        return self.value()

    def __str__(self):
        return self.string

class Token(Atom):
    pass

class QuotedString(Atom):
    pass

class NumberDecimal(Atom):
    pass

class NumberBinary(Atom):
    pass

class NumberOctal(Atom):
    pass

class NumberHexadecimal(Atom):
    pass

class Expression:
    def __init__(self, parent=None, depth=0):
        self.parent = parent
        self.child = list()
        self.depth = depth

    def cons(self, expression):
        self.child.append(expression)

    def depth_str(depth):
        s = ''
        for i in range(depth):
            s += ' '
        return s

    def dump(self, initial_depth=None):
        """ Print a sub-tree below that point """
        if type(initial_depth) == type(None):
            initial_depth = self.depth
        s = Expression.depth_str(self.depth - initial_depth) + type(self).__name__ + ':\n'
        for e in self.child:
            s += e.dump(initial_depth)
        return s

    def to_list(self):
        """ Return a list of list of the sub-tree rooted at self """
        r = list()
        for e in self.child:
            r.append(e.to_list())
        return r

    def __str__(self):
        s = '('
        delim = ''
        for e in self.child:
            s += delim + str(e)
            delim = ' '
        s += ')'
        return s

class State:
    """ The parser states """
    state_name = [ 'EXPRESSION', 'TOKEN', 'QUOTED_STRING', 'HEX_STRING', 'ESCAPE',
        'LEAD_ZERO', 'NUMBER_BIN', 'NUMBER_OCT', 'NUMBER_DEC', 'NUMBER_HEX',
        'NUMBER_BIN_C1', 'NUMBER_OCT_C1', 'NUMBER_DEC_C1', 'NUMBER_DEC_C1', 'NUMBER_HEX_C1'
    ]

    def number():
        return len(State.state_name)

    def name(state):
        return State.state_name[state]

    def make_state():
        """ Define the parser states """
        for i, s in enumerate(State.state_name):
            setattr(State, s, i)

State.make_state()

class Character:
    """ Character classes """
    def whitespace(c):
        cp = ord(c)
        return (cp >= 9 and cp < 14) or cp == 32

    def control(c):
        cp = ord(c)
        return (cp >= 0 and cp <= 31) or cp == 127

    def id_start(c):
        """ Implementing https://docs.python.org/3/reference/lexical_analysis.html#identifiers """
        return unicodedata.category(c) in ['Lu', 'Ll', 'Lt', 'Lm', 'Lo', 'Nl'] \
                or c == '_' or ord(c) in Character.Other_ID_Start

    def id_continue(c):
        """ Implementing https://docs.python.org/3/reference/lexical_analysis.html#identifiers """
        return Character.id_start(c) \
                or unicodedata.category(c) in ['Mn', 'Mc', 'Nd', 'Pc'] \
                or ord(c) in Character.Other_ID_Continue

    def xid_start(c):
        """ Implementing https://docs.python.org/3/reference/lexical_analysis.html#identifiers """
        if not Character.id_start(c):
            return False
        cn = Character.normalize(c)
        if not Character.id_start(cn[0]):
            return False
        for cf in cn[1:]:
            if not Character.id_continue(cf):
                return False
        return True

    def xid_continue(c):
        """ Implementing https://docs.python.org/3/reference/lexical_analysis.html#identifiers """
        if not Character.id_continue(c):
            return False
        cn = Character.normalize(c)
        for cf in cn:
            if not Character.id_continue(cf):
                return False
        return True

    def start_expr(c):
        return c == '('

    def end_expr(c):
        return c == ')'

    EOF_char = '\0'
    def EOF(c):
        return c == Character.EOF_char

    def expr(c):
        return Character.start_expr(c) or Character.end_expr(c) or Character.EOF(c)

    def quote(c):
        return c == '"'

    def escape(c):
        return c == '\\'

    escaped_char = 'btvnfr"\'\r\n'

    def escape_char(c):
        return c in Character.escaped_char

#    def reserved(c):
#        return c in [ '[', ']', '{', '}', '|', '#', '&' ]

    def digit(c):
        cp = ord(c)
        return cp >= ord('0') and cp <= ord('9')

    def sign(c):
        return c == '-' or c == '+'

    def digit_bin(c):
        return c in [ '0', '1' ]

    def digit_oct(c):
        cp = ord(c)
        return cp >= ord('0') and cp <= ord('7')

    def digit_hex(c):
        cp = ord(c)
        return Character.digit(c) or (cp >= ord('a') and cp <= ord('f')) or (cp >= ord('A') and cp <= ord('F'))

    def digit_nz(c):
        cp = ord(c)
        return cp >= ord('1') and cp <= ord('9')

    def zero(c):
        return c == '0'

    def radix_bin(c):
        return c == 'b'

    def radix_oct(c):
        return c == 'o'

    def radix_hex(c):
        return c == 'x'

    def any(c):
        return True

    ## Below that point: unicode utility stuff
    def normalize(c):
        """ Normalize as done for Python identifiers """
        return unicodedata.normalize('NFKC', c)

    """ Codepoints for property 'Other_ID_Start'.
        See http://www.unicode.org/Public/9.0.0/ucd/PropList.txt """
    Other_ID_Start = [ 0x1885, 0x1886, 0x2118, 0x212E, 0x309B, 0x309C ]

    """ Codepoints for property 'Other_ID_Continue'.
        See http://www.unicode.org/Public/9.0.0/ucd/PropList.txt """
    Other_ID_Continue = [ 0x00B7, 0x0387, 0x19DA ]
    Other_ID_Continue.extend(range(0x1369, 0x1371 + 1))

class Lexer:
    """ Lexer class accumulates the characters of the current atom and
        calculate its internal representation on the fly """
    def __init__(self):
        self.reset()

    def reset(self):
        ## This the input token, unprocessed
        self.string = None
        ## This is the token value
        self.value = None
        ## This is the sign when parsing a number
        self.sign = None

    def skip(self, c):
        pass

    def start_token(self, c):
        self.string = c
        self.value = Character.normalize(c)

    def cont_token(self, c):
        self.string += c
        self.value += Character.normalize(c)

    def start_dec(self, c):
        self.string = c
        self.value = int(c)

    def start_signed_dec(self, c):
        self.string = c
        self.value = 0
        self.sign = int(c + '1')

    def cont_num(self, c, radix):
        self.string += c
        if type(self.sign) != type(None):
            self.value = self.sign * (self.value * radix + int(c, base=radix))
        else:
            self.value = self.value * radix + int(c, base=radix)

    def cont_dec(self, c):
        self.cont_num(c, 10)

    def cont_bin(self, c):
        self.cont_num(c, 2)
        return True

    def cont_oct(self, c):
        self.cont_num(c, 8)
        return True

    def cont_hex(self, c):
        self.cont_num(c, 16)
        return True

    def radix(self, c):
        self.string += c

    def start_quote(self, c):
        self.string = c
        self.value = ''

    def cont_quote(self, c):
        self.string += c
        self.value += c

    def end_quote(self, c):
        self.string += c

    def start_escape(self, c):
        self.string += c

    def cont_escape(self, c):
        ch = Character.escaped_char
        ech = [ '\b', '\t', '\v', '\n', '\f', '\r', '"', "'", '', '' ]
        try:
            i = ch.index(c)
            self.string += c
            self.value += ech[i]
        except ValueError:
            raise Exception('Program bug')

class AST:
    def __init__(self):
        ## Current expression
        self.expr = None
        ## Root node
        self.root = None
        ## Current depth: useless during parsing
        ## It is used in the __str__ methods. May have other uses.
        self.depth = 0

    def parse_error(self, msg):
        ## The exception is caught by the Parser
        raise Exception(msg)

    def start_expr(self, string, value):
        """ Expression start """
        if self.depth == 0:
            self.expr = Expression()
        else:
            self.expr = Expression(parent=self.expr, depth=self.depth)
        self.depth += 1

    def end_expr(self, string, value):
        """ Expression end """
        if self.depth == 0:
            self.parse_error('Too many closing parenthesis')
        self.depth -= 1
        if self.expr.parent:
            self.expr.parent.cons(self.expr)
        else:
            ## Set root node at the end
            assert(self.depth == 0)
            self.root = self.expr
        self.expr = self.expr.parent

    def add_atom(self, a):
        if self.expr:
            self.expr.cons(a)
        else:
            assert(self.depth == 0)
            if self.root:
                self.parse_error('Root must be an atom or a list')
            self.root = a

    def end_token(self, string, value):
        a = Token(string, value, depth=self.depth)
        self.add_atom(a)

    def end_quote(self, string, value):
        a = QuotedString(string, value, depth=self.depth)
        self.add_atom(a)

    def end_dec(self, string, value):
        ## decimal number or lone zero
        a = NumberDecimal(string, value, depth=self.depth)
        self.add_atom(a)

    def end_bin(self, string, value):
        a = NumberBinary(string, value, depth=self.depth)
        self.add_atom(a)

    def end_oct(self, string, value):
        a = NumberOctal(string, value, depth=self.depth)
        self.add_atom(a)

    def end_hex(self, string, value):
        a = NumberHexadecimal(string, value, depth=self.depth)
        self.add_atom(a)

    def end_of_input(self, string, value):
        if self.depth != 0:
            self.parse_error('Missing closing parenthesis')

class Parser:
    def __init__(self):
        ## Current parser state
        self.state = State.EXPRESSION
        ## Current line number
        self.lineno = 0
        ## Current column number
        self.colno = 0
        ## Reference to Character class (no pun intended)
        self.cc = Character
        ## Our lexer
        self.lex = Lexer()
        ## The Abstract Syntax Tree
        self.ast = AST()
        assert(State.number() == len(Parser.transition))

    def loadf(self, filename):
        f = open(filename, 'r', encoding='utf-8')
        try:
            s = f.readline()
            while s:
                self.parseline(s)
                s = f.readline()
        except Exception as e:
            f.close()
            raise e
        f.close()
        self.parseline((Character.EOF_char,))
        assert(type(self.ast.root) != type(None))
        return self.ast.root

    def loads(self, s):
        ## Assume only one line
        self.parseline(s)
        self.parseline((Character.EOF_char,))
        assert(type(self.ast.root) != type(None))
        return self.ast.root

    def print_char(self, c):
        """ Return a string representing c for human cunsumption, i.e.
            control characters are escaped """
        s = str(c.encode(encoding='utf-8', errors='backslashreplace'))
        ## Strip string prefix and quotes
        return s[2:-1]

    def syn_error(self, c='', msg=None):
        """ Syntax error while parsing """
        if type(msg) != type(None):
            raise SyntaxError("unexpected char '%s' while parsing %s\n"
                    "Line: %d Col: %d\n%s"\
                    %(self.print_char(c), State.name(self.state),\
                    self.lineno, self.colno + 1, msg))
        else:
            raise SyntaxError("unexpected char '%s' while parsing %s\n"
                    "Line: %d Col: %d"\
                    %(self.print_char(c), State.name(self.state),\
                    self.lineno, self.colno + 1))

    def parse_error(self, e):
        raise Exception('Parse Error\nLine: %d Col: %d\n%s'%(self.lineno, self.colno + 1, str(e)))

    transition = [ 0 ] * State.number()
    ## Format of transition table is:
    ## transition[<parser state>] = [
    ##  [ <Character method>, [<lexer or self method>], <Boolean>, <optional: new parser state> ] ]
    ## Boolean: if True, character is consumed
    ## New parser state: if present, change to that state
    transition[State.EXPRESSION] = [
        ['whitespace', 'lex.skip', True],
        ['digit_nz', 'lex.start_dec', True, State.NUMBER_DEC],
        ['zero', 'lex.start_dec', True, State.LEAD_ZERO],
        ['sign', 'lex.start_signed_dec', True, State.NUMBER_DEC_C1],
        ['xid_start', 'lex.start_token', True, State.TOKEN],
        ['start_expr', 'ast.start_expr', True],
        ['end_expr', 'ast.end_expr', True],
        ['quote', 'lex.start_quote', True, State.QUOTED_STRING],
        ['EOF', 'ast.end_of_input', True],
    ]
    transition[State.TOKEN] = [
        ['whitespace', 'ast.end_token', True, State.EXPRESSION],
        ['xid_continue', 'lex.cont_token', True],
        ['expr', 'ast.end_token', False, State.EXPRESSION],
    ]
    transition[State.QUOTED_STRING] = [
        ['escape', 'lex.start_escape', True, State.ESCAPE],
        ['quote', ['lex.end_quote', 'ast.end_quote'], True, State.EXPRESSION],
        ['control', 'syn_error'],
        ['any', 'lex.cont_quote', True]
    ]
    ## Only single char escapes supported for now
    transition[State.ESCAPE] = [
        ['escape_char', 'lex.cont_escape', True, State.QUOTED_STRING]
    ]
    transition[State.LEAD_ZERO] = [
        ['whitespace', 'ast.end_dec', True, State.EXPRESSION],
        ['digit', 'lex.cont_dec', True, State.NUMBER_DEC],
        ['radix_bin', 'lex.radix', True, State.NUMBER_BIN_C1],
        ['radix_oct', 'lex.radix', True, State.NUMBER_OCT_C1],
        ['radix_hex', 'lex.radix', True, State.NUMBER_HEX_C1],
        ['expr', 'ast.end_dec', False, State.EXPRESSION],
    ]
    transition[State.NUMBER_BIN_C1] = [
        ['digit_bin', 'lex.cont_bin', True, State.NUMBER_BIN]
    ]
    transition[State.NUMBER_OCT_C1] = [
        ['digit_oct', 'lex.cont_oct', True, State.NUMBER_OCT]
    ]
    transition[State.NUMBER_DEC_C1] = [
        ['digit', 'lex.cont_dec', True, State.NUMBER_DEC]
    ]
    transition[State.NUMBER_HEX_C1] = [
        ['digit_hex', 'lex.cont_hex', True, State.NUMBER_HEX]
    ]
    transition[State.NUMBER_BIN] = [
        ['whitespace', 'ast.end_bin', True, State.EXPRESSION],
        ['digit_bin', 'lex.cont_bin', True],
        ['expr', 'ast.end_bin', False, State.EXPRESSION],
    ]
    transition[State.NUMBER_OCT] = [
        ['whitespace', 'ast.end_oct', True, State.EXPRESSION],
        ['digit_oct', 'lex.cont_oct', True],
        ['expr', 'ast.end_oct', False, State.EXPRESSION],
    ]
    transition[State.NUMBER_DEC] = [
        ['whitespace', 'ast.end_dec', True, State.EXPRESSION],
        ['digit', 'lex.cont_dec', True],
        ['expr', 'ast.end_dec', False, State.EXPRESSION],
    ]
    transition[State.NUMBER_HEX] = [
        ['whitespace', 'ast.end_hex', True, State.EXPRESSION],
        ['digit_hex', 'lex.cont_hex', True],
        ['expr', 'ast.end_hex', False, State.EXPRESSION],
    ]

    def parseline(self, s):
        self.lineno += 1
        n = len(s)
        self.colno = 0
        while (self.colno < len(s)):
            ## atom and string are both != None or both == None
            assert((self.state == State.EXPRESSION and self.lex.string == None) \
                    or (self.state != State.EXPRESSION and self.lex.string != None))
            c = s[self.colno]
            trans = None
            for t in self.transition[self.state]:
                check_method, act_method = t[0:2]
                f = getattr(self.cc, check_method)
                if f(c):
                    ## Make act_method iterable
                    ## TODO: tuple
                    if type(act_method) != type(list()):
                        act_method = (act_method,)
                    ## Call all actions
                    for a in act_method:
                        debug(State.name(self.state), c, check_method, a)
                        f = eval('self.' + a)
                        if a.startswith('lex.'):
                            f(c)
                        elif a.startswith('ast.'):
                            try:
                                f(self.lex.string, self.lex.value)
                            except Exception as e:
                                self.parse_error(e)
                            self.lex.reset()
                    trans = t
                    break
            if not trans:
                self.syn_error(c)
            if trans[2]:
                ## Consume char
                self.colno += 1
            if len(trans) > 3:
                ## State transition
                self.state = trans[3]

if __name__ == '__main__':
    r = Parser().loadf(sys.argv[1])
    assert(type(r) != type(None))
    print(r.dump())
    print(str(r))
    print(r.to_list())
    debug = no_debug
    r2 = Parser().loads(str(r))
    assert(type(r2) != type(None))
    assert(str(r) == str(r2))
