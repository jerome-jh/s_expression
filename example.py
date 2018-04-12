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
