from chiron_runtime.lexer import Token

class SyntaxError(Exception):
    pass

class Parser:
    def __init__(self, tokens):
        # tokens è una lista di Token
        self.tokens = list(tokens)
        self.pos = 0

    def current(self):
        # Torna un Token: o quello corrente, o EOF
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
        mods = []
        while self.current().type == 'ID' and self.current().value in ('const', 'static', 'global', 'local', 'auto'):
            mods.append(self.current().value)
            self.advance()

        # Tipo (può essere 'callable' oppure altri)
        typ_tok = self.expect('ID')
        var_type = typ_tok.value

        # Nome variabile
        name_tok = self.expect('ID')
        name = name_tok.value

        # Se il tipo è callable, supporta la sintassi: callable nome(parametri) to tipo_ritorno;
        if var_type == 'callable':
            # parentesi parametri
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

            # Aspetta il token ARROW '->' invece di 'to'
            self.expect('ARROW')

            return_type_tok = self.expect('ID')
            return_type = return_type_tok.value

            if self.current().type == 'LBRACE':
                self.expect('LBRACE')  # Consuma la '{' di apertura
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
                # Corpo parsato in body_tokens (puoi usarlo per un parsing più approfondito)

                # Dopo la parentesi graffa chiusa ci deve essere SEMICOLON
                if not self.match('SEMICOLON'):
                    raise SyntaxError("Expected ';' after callable function body")
                self.advance()

                return {
                    'type': 'declaration_callable',
                    'modifiers': mods,
                    'name': name,
                    'params': params,
                    'return_type': return_type,
                    'body': body_tokens  # o un AST se parser lo crea
                }
            else:
                # Solo dichiarazione (nessun corpo)
                if not self.match('SEMICOLON'):
                    raise SyntaxError("Expected ';' after callable declaration")
                self.advance()

                return {
                    'type': 'declaration_callable',
                    'modifiers': mods,
                    'name': name,
                    'params': params,
                    'return_type': return_type,
                    'body': None
                }

        else:
            # Altri tipi: dichiarazione variabile standard
            # supporto ":=" o "="
            if self.match('COLON'):
                self.expect('EQUAL')
            else:
                self.expect('EQUAL')

            value = self.parse_expression()

            if not self.match('SEMICOLON'):
                raise SyntaxError("Expected ';' after statement")
            self.advance()

            return {
                'type': 'declaration',
                'modifiers': mods,
                'var_type': var_type,
                'name': name,
                'value': value
            }

    # ——— Expression grammar ———

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
        # prefisso ++: x
        if self.match('INCREMENT'):
            self.expect('COLON')
            expr = self.parse_unary()
            return {'type':'unary_op','op':'++_pre','expr':expr}
        if self.match('DECREMENT'):
            self.expect('COLON')
            expr = self.parse_unary()
            return {'type':'unary_op','op':'--_pre','expr':expr}

        node = self.parse_primary()

        # postfisso x : ++
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
            return {'type':'variable','name':tok.value}

        if tok.type == 'LPAREN':
            self.advance()
            expr = self.parse_expression()
            self.expect('RPAREN')
            return expr

        if tok.type == 'LBRACKET':
            self.advance()
            elems = []
            while self.current().type != 'RBRACKET':
                elems.append(self.parse_expression())
                if self.current().type == 'COMMA':
                    self.advance()
                else:
                    break
            self.expect('RBRACKET')
            return {'type':'array','elements':elems}

        if tok.type == 'LBRACE':
            self.advance()
            pairs = []
            while self.current().type != 'RBRACE':
                key = self.parse_expression()
                self.expect('COLON')
                val = self.parse_expression()
                pairs.append((key,val))
                if self.current().type == 'COMMA':
                    self.advance()
                else:
                    break
            self.expect('RBRACE')
            return {'type':'map','pairs':pairs}

        raise SyntaxError(f"Unexpected token {tok} in primary")
