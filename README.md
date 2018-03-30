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
* Numbers: same lexical rules as for Python (relaxed concerning leading zeros)

The initial goal was to implement http://people.csail.mit.edu/rivest/Sexp.txt.
However I realized it does not define decimal numbers and I needed those. Also
raw bytes strings looked cool initially but won't mix well with Unicode unless
I implement my own decoding, which is not foreseen. So the format is currently
somewhat custom.

Parsing is done directly with a hand-written FSA. There is no formal grammar
or parser generator involved, and there is no dependency besides standard 
Python libraries. It has been developped and tested with Python3 ;)
