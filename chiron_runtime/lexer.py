import re

class Token:
    def __init__(self, type_, value, line=0, col=0):
        self.type = type_
        self.value = value
        self.line = line
        self.col = col
    def __repr__(self):
        return f"Token({self.type!r}, {self.value!r}, line={self.line}, col={self.col})"

class Lexer:
    def __init__(self, code):
        self.code = code
        self.token_specification = [
            ('COMMENT_MULTILINE_START', r'//'),
            ('COMMENT_MULTILINE_END', r'\.//'),
            ('COMMENT_SINGLELINE', r'#.*'),
            ('INCREMENT', r'\+\+'),
            ('DECREMENT', r'--'),
            ('ARROW', r'->'),
            ('PLUS', r'\+'),
            ('MINUS', r'-'),
            ('STAR', r'\*'),
            ('SLASH', r'/'),
            ('PERCENT', r'%'),
            ('LPAREN', r'\('),
            ('RPAREN', r'\)'),
            ('LBRACKET', r'\['),
            ('RBRACKET', r'\]'),
            ('LBRACE', r'\{'),
            ('RBRACE', r'\}'),
            ('COMMA', r','),
            ('COLON', r':'),
            ('SEMICOLON', r';'),
            ('EQUAL', r'='),
            ('NUMBER', r'\d+(\.\d*)?'),
            ('STRING', r'"([^"\\]|\\.)*"'),
            ('CHAR', r"'([^'\\]|\\.)'"),
            ('ID', r'[A-Za-z_][A-Za-z0-9_]*'),
            ('NEWLINE', r'\n'),
            ('SKIP', r'[ \t]+'),
            ('MISMATCH', r'.'),
        ]
        self.master_pat = re.compile(
            '|'.join(f'(?P<{name}>{pat})' for name,pat in self.token_specification)
        )

    def tokenize(self):
        line = 1
        col = 1
        in_multiline_comment = False
        for mo in self.master_pat.finditer(self.code):
            kind = mo.lastgroup
            val = mo.group()

            if in_multiline_comment:
                if kind == 'COMMENT_MULTILINE_END':
                    in_multiline_comment = False
                continue

            if kind == 'COMMENT_MULTILINE_START':
                in_multiline_comment = True
                continue

            if kind == 'COMMENT_SINGLELINE':
                continue

            if kind == 'NEWLINE':
                line += 1
                col = 1
                continue
            if kind == 'SKIP':
                col += len(val)
                continue
            if kind == 'MISMATCH':
                raise RuntimeError(f'Unexpected {val!r} at {line}:{col}')
            yield Token(kind, val, line, col)
            col += len(val)
