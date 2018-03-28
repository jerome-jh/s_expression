# s_expression

The purpose is to use S-expressions for data serialization. The code
only provides a parser. Output can be a list of lists of custom objects, a list
of list of Python basic data types, or if using str() another S-expressions
equivalent to the input.

I hope this will be tastier and healthier than your daily XML/JSON meal.

The initial goal was to implement http://people.csail.mit.edu/rivest/Sexp.txt.
However I realized that document does not define decimal numbers and I needed
those. So the format is currently somewhat custom.

# Implementation details

Implementation is currently incomplete and have rough edges. Parsing is done
directly rather than through a formal grammar / parser generator. It has no
dependency. This is not a huge if/then/else either ;)

Compared to the original spec, this implementation supports UTF-8 characters in
quoted strings and binary, octal, decimal and hexadecimal numbers.
