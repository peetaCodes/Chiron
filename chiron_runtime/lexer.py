import re
from collections import namedtuple

Token = namedtuple('Token', ['type', 'value', 'line', 'column'])

class Lexer:
    def __init__(self, code):
        self.code = code
        self.keywords = {
            'int', 'float', 'bool', 'char', 'str',
            'array', 'tuple', 'map',
            'auto', 'const', 'static', 'global', 'local',
            'true', 'false'
        }

        self.token_specification = [
            ('NEWLINE',    r'\n'),
            ('SKIP',       r'[ \t]+'),
            ('COMMENT',    r'//.*'),
            ('MLCOMMENT_START', r'//'),
            ('MLCOMMENT_END',   r'\.//'),
            ('FLOAT',      r'\d+\.\d+'),
            ('INT',        r'\d+'),
            ('CHAR',       r"\'(\\.|[^\\'])\'"),
            ('STRING',     r'"(\\.|[^\\"])*"'),
            ('ID',         r'[A-Za-z_][A-Za-z0-9_]*'),
            ('ASSIGN',     r':\s*=|:=|='),
            ('END',        r';'),
            ('OP',         r'[+\-*/]'),
            ('LPAREN',     r'\('),
            ('RPAREN',     r'\)'),
            ('LBRACKET',   r'\['),
            ('RBRACKET',   r'\]'),
            ('LBRACE',     r'\{'),
            ('RBRACE',     r'\}'),
            ('COMMA',      r','),
        ]

        self.master_pat = re.compile('|'.join(f'(?P<{tok}>{regex})' for tok, regex in self.token_specification))

    def tokenize(self):
        line_num = 1
        line_start = 0
        multiline_comment = False

        for mo in self.master_pat.finditer(self.code):
            kind = mo.lastgroup
            value = mo.group()
            column = mo.start() - line_start

            if multiline_comment:
                if kind == 'MLCOMMENT_END':
                    multiline_comment = False
                continue
            elif kind == 'MLCOMMENT_START':
                multiline_comment = True
                continue
            elif kind == 'NEWLINE':
                line_start = mo.end()
                line_num += 1
                continue
            elif kind == 'SKIP' or kind == 'COMMENT':
                continue
            elif kind == 'ID' and value in self.keywords:
                kind = value.upper()

            yield Token(kind, value, line_num, column)
