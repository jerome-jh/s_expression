#!/usr/bin/python3
import sys
import itertools as it

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

    def __str__(self):
        s = Expression.depth_str(self.depth)
        return s + 'Token: ' + self.token + '\n'

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

    def __str__(self):
        s = Expression.depth_str(self.depth)
        s += 'Expr:\n'
        for e in self.child:
            if type(e) == type(Expression()):
                s += str(e)
            elif type(e) == type(Atom('a')):
                s += str(e)
            else:
                raise BaseException(str(type(e)))
        return s

class ParserState:
    EXPRESSION = 0
    TOKEN = 1
    QUOTED_STRING = 2
    HEX_STRING = 3
    ESCAPE = 4

    def __init__(self):
        ## Current parser state
        self.state = ParserState.EXPRESSION
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

class Parser:
    ## Characters classes should be disjunct
    whitespace = [ '%c'%c for c in it.chain(range(9, 14), [32]) ]
    numeric = [ '%c'%c for c in range(48, 58) ]
    pseudo_alphabetic = [ '-', '.', '/', '_', ':', '*', '+', '=' ]
    alphabetic = [ '%c'%c for c in it.chain(range(65, 91), range(97, 123)) ] + pseudo_alphabetic
    expr = [ '(', ')' ]
    quote = [ '"' ]
    escape = [ '\\' ]
    reserved = [ '[', ']', '{', '}', '|', '#', '&' ]
    verbatim = [ '!', '%', '^', '~', ';', "'", ',', '<', '>', '?' ]

    char_class = [ whitespace, numeric, alphabetic, expr, quote, escape, reserved, verbatim ]

    def __init__(self):
        self.state = ParserState()

    def loadf(self, f):
        s = f.readline()
        while s:
            self.parseline(s)
            s = f.readline()
        return self.state.root

    def loads(self, s):
        ## Assume only one line
        return self.parseline(s)

    def skip(self, c):
        return True

    def syn_error(self, c=''):
        raise SyntaxError('Syntax Error\nLine: %d Col: %d' % (self.state.lineno, self.state.colno + 1))

    def error(self, msg):
        raise BaseException('%s\nLine: %d Col: %d' % (msg, self.state.lineno, self.state.colno + 1))

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

    def end_hex(self, c):
        return True

    def start_num(self, c):
        return True

    def start_quote(self, c):
        st = self.state
        st.string = ''
        st.state = ParserState.QUOTED_STRING
        return True

    def escape(self, c):
        self.state.state = ParserState.ESCAPE
        return True

    def acc_escape(self, c):
        ## Only single char escapes supported for now
        st = self.state
        ch = 'btvnfr"\''
        ech = [ '\b', '\t', '\v', '\n', '\f', '\r', '"', "'" ]
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

    transition = [
        ## ParserState.ROOT
        ## Whitespace,numeric,    alphabetic, expr, quote, reserved,  verbatim
#        [ skip,      syn_error,       syn_error,   reserved,    syn_error ],
        ## ParserState.EXPRESSION
        [ skip,      start_num,   start_token,   expr, start_quote, syn_error, reserved,    syn_error ],
        ## ParserState.TOKEN
        [ end_token, syn_error,       acc,     expr, end_quote, syn_error, end_token,    syn_error ],
        ## ParserState.QUOTED_STRING
        [ acc, acc,         acc,     acc, end_quote, escape, reserved,    acc ],
        ## ParserState.HEX_STRING
        [ end_hex,   syn_error,       syn_error,   syn_error, syn_error, syn_error, reserved,    syn_error ],
        ## ParserState.ESCAPE
        [ acc_escape, acc_escape, acc_escape, acc_escape, acc_escape, acc_escape, acc_escape, acc_escape ],
    ]

    def parseline(self, s):
        st = self.state
        st.lineno += 1
        n = len(s)
        st.colno = 0
        while (st.colno < len(s)):
            ## atom and string are both != None or both == None
            assert((st.state >= ParserState.TOKEN and st.string != None) or not (st.state >= ParserState.TOKEN or st.string != None))
            r = None
            for j, cc in enumerate(Parser.char_class):
                if s[st.colno] in cc:
                    debug(st.state, j, s[st.colno], self.transition[st.state][j])
                    r = self.transition[st.state][j](self, s[st.colno])
                    break
            if r == None:
                self.error('Program bug: character classes wrongly defined')
            if r:
                st.colno += 1
            #else: recirculate char

#            if s[i] in Parser.alphabetic:
#                if not st.atom:
#                    ## Token starting
#                    st.atom = ParserState.TOKEN
#                    st.string = s[i]
#                else:
#                    ## Token continuing
#                    st.token += s[i]
#            else:
#                if st.token:
#                    ## Token finishing
#                    a = Atom(st.token, depth=st.depth)
#                    st.token = None
#                    if st.expr:
#                        st.expr.cons(a)
#                    else:
#                        raise SyntaxError('Line: %d Col: %d' % (st.lineno, i))
#                if s[i] in Parser.whitespace:
#                    pass
#                elif s[i] in Parser.reserved:
#                    if s[i] == '(':
#                        if not st.root:
#                            st.root = Expression(parent=st.expr)
#                            st.expr = st.root
#                        else:
#                            st.depth += 1
#                            st.expr = Expression(parent=st.expr, depth=st.depth)
#                    elif s[i] == ')':
#                        if st.expr.parent:
#                            st.expr.parent.cons(st.expr)
#                            st.depth -= 1
#                        st.expr = st.expr.parent
#                    else:
        if st.depth != 0:
            self.error('Missing closing parenthesis')
        
        return st.root

if __name__ == '__main__':
    p = Parser()
    print(p.loadf(open(sys.argv[1], 'r')))

