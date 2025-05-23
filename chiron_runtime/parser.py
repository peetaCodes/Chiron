from collections import defaultdict
from lexer import Lexer

class Parser:
    def __init__(self, tokens):
        self.tokens = list(tokens)
        self.pos = 0
        self.symbol_table = {}

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def advance(self):
        tok = self.peek()
        self.pos += 1
        return tok

    def match(self, *token_types):
        tok = self.peek()
        if tok and tok.type in token_types:
            return self.advance()
        return None

    def parse(self):
        while self.peek():
            self.parse_declaration()

    def parse_declaration(self):
        qualifiers = []
        while True:
            tok = self.peek()
            if tok and tok.type in ('CONST', 'STATIC', 'GLOBAL', 'LOCAL'):
                qualifiers.append(tok.type.lower())
                self.advance()
            else:
                break

        typ_tok = self.match('INT', 'FLOAT', 'BOOL', 'CHAR', 'STR', 'AUTO', 'ARRAY', 'TUPLE', 'MAP')
        if not typ_tok:
            raise SyntaxError(f"Expected type at line {self.peek().line}")

        var_tok = self.match('ID')
        if not var_tok:
            raise SyntaxError(f"Expected identifier after type '{typ_tok.value}'")

        assign_tok = self.match('ASSIGN')
        if not assign_tok:
            raise SyntaxError(f"Expected assignment after identifier '{var_tok.value}'")

        expr = self.parse_expression()

        if not self.match('END'):
            raise SyntaxError(f"Missing semicolon at line {self.peek().line}")

        self.symbol_table[var_tok.value] = {
            'type': typ_tok.type.lower(),
            'qualifiers': tuple(qualifiers),
            'value': expr
        }

        print(f"[DECLARED] {var_tok.value} = {expr} ({typ_tok.type.lower()} | {tuple(qualifiers)})")

    def parse_expression(self):
        # Simple literal or identifier for now
        tok = self.advance()
        if tok.type in ('INT', 'FLOAT', 'CHAR', 'STRING', 'TRUE', 'FALSE', 'ID'):
            return tok.value
        elif tok.type == 'LBRACKET':  # parse array literal
            elements = []
            while True:
                if self.peek().type == 'RBRACKET':
                    self.advance()
                    break
                elements.append(self.parse_expression())
                if self.peek().type == 'COMMA':
                    self.advance()
            return elements
        else:
            raise SyntaxError(f"Unexpected token in expression: {tok}")

# === Example usage ===
if __name__ == '__main__':
    code = '''
    const global array myArray := [1, 2, 3];
    static map myMap := ["key", "value"];
    tuple myTuple := [1, "two", '3'];
    '''

    print("=== LEXING ===")
    lexer = Lexer(code)
    tokens = list(lexer.tokenize())
    for tok in tokens:
        print(tok)

    print("\n=== PARSING ===")
    parser = Parser(tokens)
    parser.parse()
    print("\n=== SYMBOL TABLE ===")
    from pprint import pprint
    pprint(parser.symbol_table)
