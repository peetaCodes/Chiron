
from chiron_runtime.lexer import Token

class SyntaxError(Exception):
    pass

class Parser:
    def __init__(self, tokens):
        self.tokens = list(tokens)
        self.pos = 0

    def current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token('EOF', '')

    def advance(self):
        self.pos += 1

    def expect(self, ttype):
        tok = self.current()
        if tok.type != ttype:
            raise SyntaxError(f"Expected {ttype} but got {tok}")
        self.advance()
        return tok

    def match(self, *ttypes):
        tok = self.current()
        if tok.type in ttypes:
            self.advance()
            return tok
        return None

    def parse(self):
        stmts = []
        while self.current().type != 'EOF':
            stmts.append(self.parse_statement())
        return stmts

    def parse_statement(self):
        # ——— Chiamata standalone: ID '(' … ')' ';' ———
        # (deve venire prima di return e modificatori)
        if self.current().type == 'ID' and \
                self.pos + 1 < len(self.tokens) and \
                self.tokens[self.pos + 1].type == 'LPAREN':

            name = self.current().value
            self.advance()  # consumo ID
            self.expect('LPAREN')  # consumo '('

            args = []
            while self.current().type != 'RPAREN':
                args.append(self.parse_expression())
                if self.current().type == 'COMMA':
                    self.advance()
                else:
                    break
            self.expect('RPAREN')
            self.expect('SEMICOLON')

            return {
                'type': 'call_callable',
                'name': name,
                'args': args
            }

        # ——— Try/Except/Finally ———
        if self.current().type == 'ID' and self.current().value == 'try':
            # Consuma 'try'
            self.advance()
            # Corpo try
            self.expect('LBRACE')
            try_body_tokens = []
            brace = 1
            while brace > 0:
                tok = self.current()
                if tok.type == 'LBRACE':
                    brace += 1
                elif tok.type == 'RBRACE':
                    brace -= 1
                if brace > 0:
                    try_body_tokens.append(tok)
                self.advance()
            try_body = Parser(try_body_tokens).parse()

            # 1 o più except
            handlers = []
            while self.current().type == 'ID' and self.current().value == 'except':
                self.advance()
                # Tipo eccezione
                exc_type = self.expect('ID').value
                # 'as' nome variabile
                self.expect('ID')  # dovrebbe essere 'as'
                exc_var = self.expect('ID').value
                # Corpo handler
                self.expect('LBRACE')
                body_tokens = [];
                brace = 1
                while brace > 0:
                    tok = self.current()
                    if tok.type == 'LBRACE':
                        brace += 1
                    elif tok.type == 'RBRACE':
                        brace -= 1
                    if brace > 0: body_tokens.append(tok)
                    self.advance()
                handlers.append({
                    'exception': exc_type,
                    'var': exc_var,
                    'body': Parser(body_tokens).parse()
                })

            # Optional finally
            final_body = None
            if self.current().type == 'ID' and self.current().value == 'finally':
                self.advance()
                self.expect('LBRACE')
                body_tokens = [];
                brace = 1
                while brace > 0:
                    tok = self.current()
                    if tok.type == 'LBRACE':
                        brace += 1
                    elif tok.type == 'RBRACE':
                        brace -= 1
                    if brace > 0: body_tokens.append(tok)
                    self.advance()
                final_body = Parser(body_tokens).parse()

            return {
                'type': 'try',
                'body': try_body,
                'handlers': handlers,
                'finally': final_body
            }

        if self.current().type == 'ID' and self.current().value == 'return':
            self.advance()
            expr = None
            if self.current().type != 'SEMICOLON':
                expr = self.parse_expression()
            self.expect('SEMICOLON')
            return {'type': 'return', 'expression': expr}

        mods = []
        while self.current().type == 'ID' and self.current().value in ('const', 'static', 'global', 'local'):
            mods.append(self.current().value)
            self.advance()

        # ——— Tipo (può essere auto, callable o un tipo primitivo) ———
        typ_tok = self.expect('ID')
        var_type = typ_tok.value

        name_tok = self.expect('ID')
        name = name_tok.value

        if var_type == 'callable':
            self.expect('LPAREN')
            params = []
            while self.current().type != 'RPAREN':
                param_type_tok = self.expect('ID')
                param_type = param_type_tok.value
                param_name_tok = self.expect('ID')
                param_name = param_name_tok.value
                params.append({'type': param_type, 'name': param_name})
                if self.current().type == 'COMMA':
                    self.advance()
                else:
                    break
            self.expect('RPAREN')

            self.expect('ARROW')
            return_type_tok = self.expect('ID')
            return_type = return_type_tok.value

            if self.current().type == 'LBRACE':
                self.expect('LBRACE')
                brace_count = 1
                body_tokens = []
                while brace_count > 0:
                    tok = self.current()
                    if tok.type == 'EOF':
                        raise SyntaxError("Unexpected EOF while parsing function body")
                    if tok.type == 'LBRACE':
                        brace_count += 1
                    elif tok.type == 'RBRACE':
                        brace_count -= 1
                    if brace_count > 0:
                        body_tokens.append(tok)
                    self.advance()
                if not self.match('SEMICOLON'):
                    raise SyntaxError("Expected ';' after callable function body")
                return {
                    'type': 'declaration_callable',
                    'modifiers': mods,
                    'name': name,
                    'params': params,
                    'return_type': return_type,
                    'body': Parser(body_tokens).parse() if body_tokens else []
                }
            else:
                if not self.match('SEMICOLON'):
                    raise SyntaxError("Expected ';' after callable declaration")
                return {
                    'type': 'declaration_callable',
                    'modifiers': mods,
                    'name': name,
                    'params': params,
                    'return_type': return_type,
                    'body': None
                }
        else:
            # Dichiarazione variabile o assegnamento
            if self.match('COLON'):
                self.expect('EQUAL')
            else:
                self.expect('EQUAL')

            value = self.parse_expression()

            if not self.match('SEMICOLON'):
                raise SyntaxError("Expected ';' after statement")

            return {
                'type': 'declaration',
                'modifiers': mods,
                'var_type': var_type,
                'name': name,
                'value': value
            }

    # Expression grammar:

    def parse_expression(self):
        return self.parse_add_sub()

    def parse_add_sub(self):
        node = self.parse_mul_div()
        while True:
            if self.match('PLUS'):
                right = self.parse_mul_div()
                node = {'type':'binary_op','op':'+','left':node,'right':right}
            elif self.match('MINUS'):
                right = self.parse_mul_div()
                node = {'type':'binary_op','op':'-','left':node,'right':right}
            else:
                break
        return node

    def parse_mul_div(self):
        node = self.parse_unary()
        while True:
            if self.match('STAR'):
                right = self.parse_unary()
                node = {'type':'binary_op','op':'*','left':node,'right':right}
            elif self.match('SLASH'):
                right = self.parse_unary()
                node = {'type':'binary_op','op':'/','left':node,'right':right}
            elif self.match('PERCENT'):
                right = self.parse_unary()
                node = {'type':'binary_op','op':'%','left':node,'right':right}
            else:
                break
        return node

    def parse_unary(self):
        if self.match('INCREMENT'):
            self.expect('COLON')
            expr = self.parse_unary()
            return {'type':'unary_op','op':'++_pre','expr':expr}
        if self.match('DECREMENT'):
            self.expect('COLON')
            expr = self.parse_unary()
            return {'type':'unary_op','op':'--_pre','expr':expr}

        node = self.parse_primary()

        if self.match('COLON'):
            if self.match('INCREMENT'):
                return {'type':'unary_op','op':'++_post','expr':node}
            if self.match('DECREMENT'):
                return {'type':'unary_op','op':'--_post','expr':node}
            raise SyntaxError("':' must be followed by '++' or '--' in postfix")

        return node

    def parse_primary(self):
        tok = self.current()

        if tok.type == 'NUMBER':
            self.advance()
            val = float(tok.value) if '.' in tok.value else int(tok.value)
            return {'type':'literal','value':val}

        if tok.type == 'STRING':
            self.advance()
            return {'type':'literal','value':tok.value[1:-1]}

        if tok.type == 'CHAR':
            self.advance()
            return {'type':'literal','value':tok.value[1]}

        if tok.type == 'ID':
            self.advance()
            if self.current().type == 'LPAREN':
                self.advance()
                args = []
                while self.current().type != 'RPAREN':
                    args.append(self.parse_expression())
                    if self.current().type == 'COMMA':
                        self.advance()
                    else:
                        break
                self.expect('RPAREN')
                return {
                    'type': 'call_callable',
                    'name': tok.value,
                    'args': args
                }
            return {'type':'identifier','name':tok.value}

        if tok.type == 'LPAREN':
            self.advance()
            expr = self.parse_expression()
            self.expect('RPAREN')
            return expr

        raise SyntaxError(f"Unexpected token {tok} in expression")
