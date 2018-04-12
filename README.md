# s_expression

The purpose is to use S-expressions for data serialization. The code
only provides a parser. Output can be a list of lists of custom objects, a list
of list of Python basic data types, or if using str() another S-expressions
equivalent to the input.

I hope this will be tastier and healthier than your daily XML/JSON meal.

# Implementation details

Supported:
* An atom can be: a token, a quoted string, a binary, octal, decimal,
  hexadecimal integer
* There is no limit on integer size
* UTF-8 characters in tokens: same lexical rules as for Python identifiers (it
  is pretty complex)
* Quoted strings: any UTF-8 character except control characters, that must be
  escaped
* Numbers: same lexical rules as for Python, but relaxed concerning leading
  zeros: basically everything that is accepted by the builtin int()

The initial goal was to implement http://people.csail.mit.edu/rivest/Sexp.txt.
However I realized it does not define decimal numbers and I needed those. Also
raw bytes strings looked cool initially but won't mix well with Unicode unless
I implement my own decoding, which is not foreseen. So the format is currently
somewhat custom.

Parsing is done directly with a hand-written FSA. There is no formal grammar
or parser generator involved, and there is no dependency besides standard 
Python libraries. It has been developped and tested with Python3 ;)

# Example

```python
import s_expression

inp = """
((book (title "Au bord de l'eau") (author 施耐庵) (translator "Jacques Dars")
    (keywords brigand chine révolte)
    (year (1550 0x60e 0b11000001110))
    (borrowed)
))
"""

def read_book(exp):
    for e in exp:
        if len(e) > 2:
            print(e[0],':','/'.join(map(str,e[1:])))
        else:
            print(': '.join(map(str,e)))

if __name__ == '__main__':
    s = s_expression.Parser().loads(inp)
    for e in s.to_list():
        if e[0] == 'book':
            read_book(e[1:])
```

Output:

```
title: Au bord de l'eau
author: 施耐庵
translator: Jacques Dars
keywords : brigand/chine/révolte
year: [1550, 1550, 1550]
borrowed
```
