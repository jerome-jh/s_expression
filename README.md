# s_expression

This is an implementation of http://people.csail.mit.edu/rivest/Sexp.txt in
Python. The purpose is to use S-expressions for data serialization. The code
only provides a parser. I hope this will be tastier and healthier than your
daily XML/JSON meal.

# Implementation details

Implementation is currently incomplete and has rough edges. Parsing is done
directly rather than through a formal grammar / parser generator. This is not a
huge if/then/else either ;)

Compared to the original spec, this implementation supports UTF-8 characters in
quoted strings.
