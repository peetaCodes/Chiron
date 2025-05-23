import re

class Token:
    def __init__(self, type_, value, line=0, col=0):
        self.type = type_
        self.value = value
        self.line = line
        self.col = col
    def __repr__(self):
        return f"Token({self.type!r}, {self.value!r})"

class Lexer:
    def __init__(self, code):
        self.code = code
        self.token_specification = [
            # Ordine importa: longer first
            ('INCREMENT', r'\+\+'),
            ('DECREMENT', r'--'),
            ('ARROW', r'->'),
            ('PLUS',      r'\+'),
            ('MINUS',     r'-'),
            ('STAR',      r'\*'),
            ('SLASH',     r'/'),
            ('PERCENT',   r'%'),
            ('LPAREN',    r'\('),
            ('RPAREN',    r'\)'),
            ('LBRACKET',  r'\['),
            ('RBRACKET',  r'\]'),
            ('LBRACE',    r'\{'),
            ('RBRACE',    r'\}'),
            ('COMMA',     r','),
            ('COLON',     r':'),
            ('SEMICOLON', r';'),
            ('EQUAL',     r'='),             # assignment and equality
            ('NUMBER',    r'\d+(\.\d*)?'),
            ('STRING',    r'"([^"\\]|\\.)*"'),
            ('CHAR',      r"'([^'\\]|\\.)'"),
            ('ID',        r'[A-Za-z_][A-Za-z0-9_]*'),
            ('NEWLINE',   r'\n'),
            ('SKIP',      r'[ \t]+'),
            ('MISMATCH',  r'.'),
        ]
        self.master_pat = re.compile(
            '|'.join(f'(?P<{name}>{pat})' for name,pat in self.token_specification)
        )

    def tokenize(self):
        line = 1; col = 1
        for mo in self.master_pat.finditer(self.code):
            kind = mo.lastgroup
            val = mo.group()
            if kind == 'NEWLINE':
                line += 1; col = 1
                continue
            if kind == 'SKIP':
                col += len(val)
                continue
            if kind == 'MISMATCH':
                raise RuntimeError(f'Unexpected {val!r} at {line}:{col}')
            token = Token(kind, val, line, col)
            yield token
            col += len(val)
