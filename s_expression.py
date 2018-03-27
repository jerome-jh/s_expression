#!/usr/bin/python3
import sys

if __name__ == '__main__':
    def debug(*args):
        print(*args, file=sys.stderr)
else:
    def debug(*args):
        pass

class Atom:
    def __init__(self, token, depth=0):
        self.token = token
        self.depth = depth

    def dump(self, initial_depth=None):
        if type(initial_depth) == type(None):
            initial_depth = self.depth
        return Expression.depth_str(self.depth - initial_depth) + type(self).__name__ + ': ' + str(self) + '\n'

    def value(self):
        """ The value of the atom can be any type """
        return self.token

    def to_list(self):
        return self.value()

    def __str__(self):
        return self.token

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

class ParserState:
    ## First state in list is start state
    state_name = [ 'EXPRESSION', 'TOKEN', 'QUOTED_STRING', 'HEX_STRING', 'ESCAPE', 'NUMBER' ]

    def __init__(self):
        ## Current parser state
        self.state = 0
        ## Accumulator string when parsing an atom
        self.string = None
        ## Current expression
        self.expr = None
        ## Root node
        self.root = None
        ## Current line number
        self.lineno = 0
        ## Current column number
        self.colno = 0
        ## Current depth: useless during parsing
        ## It is used in the __str__ methods. May have other uses.
        self.depth = 0

    def number():
        return len(ParserState.state_name)

    def name(self):
        return ParserState.state_name[self.state]

## Define parser states
for i, s in enumerate(ParserState.state_name):
    setattr(ParserState, s, i)

class Parser:

    def whitespace(self, c):
        cp = ord(c)
        return (cp >= 9 and cp < 14) or cp == 32

    def control(self, c):
        cp = ord(c)
        return (cp >= 0 and cp <= 31) or cp == 127

    def pseudo_alphabetic(self, c):
        return c in [ '-', '.', '/', '_', ':', '*', '+', '=' ]

    def alphabetic(self, c):
        cp = ord(c)
        return (cp >= 65 and cp < 91) or (cp >= 97 and cp < 123) or self.pseudo_alphabetic(c)

    def expr_delim(self, c):
        return c in [ '(', ')' ]

    def quote(self, c):
        return c == '"'

    def escape(self, c):
        return c == '\\'

    def reserved(self, c):
        return c in [ '[', ']', '{', '}', '|', '#', '&' ]

    def verbatim(self, c):
        return c in [ '!', '%', '^', '~', ';', "'", ',', '<', '>', '?' ]

    def utf8(self, c):
        return ord(c) >= 128

    def digit(self, c):
        cp = ord(c)
        return cp >= ord('0') and cp <= ord('9')

    def digit_nz(self, c):
        cp = ord(c)
        return cp >= ord('1') and cp <= ord('9')

    def zero(self, c):
        return c == '0'

    def any_char(self, c):
        return True

    ## Characters classes should be disjunct

    def __init__(self):
        self.state = ParserState()

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
        return self.end_of_input()

    def loads(self, s):
        ## Assume only one line
        self.parseline(s)
        return self.end_of_input()

    def skip(self, c):
        return True

    def syn_error(self, c='', msg=None):
        if type(msg) != type(None):
            raise SyntaxError('Syntax Error: %s\nLine: %d Col: %d' % (msg, self.state.lineno, self.state.colno + 1))
        else:
            raise SyntaxError('Syntax Error\nLine: %d Col: %d Char: %c' % (self.state.lineno, self.state.colno + 1, c))

    def error(self, msg):
        raise Exception('%s\nLine: %d Col: %d' % (msg, self.state.lineno, self.state.colno + 1))

    def reserved(self, c):
        return True

    def expr(self, c):
        st = self.state
        if c == '(':
            ## Expression start
            if st.depth == 0:
                st.expr = Expression()
            else:
                st.expr = Expression(parent=st.expr, depth=st.depth)
            st.depth += 1
        elif c == ')':
            ## Expression end
            st.depth -= 1
            if st.expr.parent:
                st.expr.parent.cons(st.expr)
            else:
                ## Set root node at the end
                assert(st.depth == 0)
                st.root = st.expr
            st.expr = st.expr.parent
        else:
            ## Should not occur
            self.error('Program bug: unexpected character %c'%c)
        return True

    def start_token(self, c):
        st = self.state
        st.string = '%c'%c
        st.state = ParserState.TOKEN
        return True

    def end_token(self, c):
        st = self.state
        a = Atom(st.string, depth=st.depth)
        st.string = None
        if st.expr:
            st.expr.cons(a)
        else:
            assert(st.depth == 0)
            if st.root:
                self.error('Root must be a token or a list')
            st.root = a
        st.state = ParserState.EXPRESSION
        return False

    def end_number(self, c):
        st = self.state
        i = int(st.string)
        ##TODO subclass Atom
        a = Atom(st.string, depth=st.depth)
        st.string = None
        if st.expr:
            st.expr.cons(a)
        else:
            assert(st.depth == 0)
            if st.root:
                self.error('Root must be a token or a list')
            st.root = a
        st.state = ParserState.EXPRESSION
        return False

    def end_hex(self, c):
        return True

    def start_num(self, c):
        st = self.state
        st.string = c
        st.state = ParserState.NUMBER
        return True

    def start_quote(self, c):
        st = self.state
        st.string = ''
        st.state = ParserState.QUOTED_STRING
        return True

    def start_escape(self, c):
        self.state.state = ParserState.ESCAPE
        return True

    def acc_escape(self, c):
        ## Only single char escapes supported for now
        st = self.state
        ch = 'btvnfr"\'\r\n'
        ech = [ '\b', '\t', '\v', '\n', '\f', '\r', '"', "'", '', '' ]
        try:
            i = ch.index(c)
            st.string += ech[i]
            self.state.state = ParserState.QUOTED_STRING
        except ValueError:
            syn_error(self, c)
        return True

    def end_quote(self, c):
        st = self.state
        a = Atom(st.string, depth=st.depth)
        st.string = None
        if st.expr:
            st.expr.cons(a)
        else:
            assert(st.depth == 0)
            if st.root:
                self.error('Root must be a token or a list')
            st.root = a
        st.state = ParserState.EXPRESSION
        return True

    def acc(self, c):
        self.state.string += c
        return True

    transition = [ 0 ] * ParserState.number()
    transition[ParserState.EXPRESSION] = [[ whitespace, skip ], [ digit_nz, start_num ],
            [ zero, start_num ], #TODO: should be start octal
            [ alphabetic, start_token ], [ expr_delim, expr ], [ quote, start_quote ], [ any_char, syn_error ]]
    transition[ParserState.TOKEN] = [[ whitespace, end_token ], [ alphabetic, acc ], [ expr_delim, end_token ],
            [ any_char, syn_error]]
    transition[ParserState.QUOTED_STRING] = [[ escape, start_escape ], [ control, syn_error ], [ quote, end_quote ],
            [ any_char, acc ]]
    transition[ParserState.ESCAPE] = [[ any_char, acc_escape ]]
    transition[ParserState.NUMBER] = [[ whitespace, end_number], [digit, acc], [expr_delim, end_number],
            [any_char, syn_error]]

    def parseline(self, s):
        st = self.state
        st.lineno += 1
        n = len(s)
        st.colno = 0
        while (st.colno < len(s)):
            ## atom and string are both != None or both == None
            assert((st.state >= ParserState.TOKEN and st.string != None) or not (st.state >= ParserState.TOKEN or st.string != None))
            r = None
            c = s[st.colno]
            for t in self.transition[st.state]:
                if t[0](self, c):
                    debug(st.name(), c, t[0].__name__, t[1].__name__)
                    r = t[1](self, c)
                    break
            if r == None:
                self.error('Program bug: \'%c\' has no character class'%c)
            if r:
                st.colno += 1
            #else: recirculate char

    def end_of_input(self):
        if self.state.depth != 0:
            self.syn_error('', 'Missing closing parenthesis')
        
        return self.state.root

if __name__ == '__main__':
    r = Parser().loadf(sys.argv[1])
    print(r.dump())
    print(str(r))

