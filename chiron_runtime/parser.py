from chiron_runtime.lexer import Token

class SyntaxError(Exception):
    pass

class Parser:
    def __init__(self, tokens):
        self.tokens = list(tokens)
        self.pos = 0
        self.stmt_parsers = {
            'try':     self.parse_try,
            'return':  self.parse_return,
            'if':      self.parse_if,
            'while':   self.parse_while,
            'for':     self.parse_for,
        }

    def current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token('EOF', '')

    def advance(self):
        self.pos += 1

    def expect(self, ttype: str) -> Token:
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

    # ——— Blocchi ———
    def parse_block(self):
        self.expect('LBRACE')
        stmts = []
        while self.current().type != 'RBRACE':
            stmts.append(self.parse_statement())
        self.expect('RBRACE')
        return stmts

    # ——— Dispatch statement ———
    def parse_statement(self):
        tok = self.current()
        if tok.type == 'ID' and tok.value in self.stmt_parsers:
            return self.stmt_parsers[tok.value]()
        if tok.type == 'ID' and tok.value in (
            'const','static','global','local','auto',
            'int','float','bool','char','str','callable'
        ):
            return self.parse_declaration()
        expr = self.parse_expression()
        self.expect('SEMICOLON')
        return {'type':'expr_stmt','expr':expr}

    # ——— try/except/finally ———
    def parse_try(self):
        self.advance()        # 'try'
        body    = self.parse_block()
        handlers = []
        while self.current().type=='ID' and self.current().value=='except':
            self.advance()
            exc_type = self.expect('ID').value
            self.expect('ID')  # 'as'
            exc_var  = self.expect('ID').value
            handler_body = self.parse_block()
            handlers.append({'exception':exc_type,'var':exc_var,'body':handler_body})
        final_body = None
        if self.current().type=='ID' and self.current().value=='finally':
            self.advance()
            final_body = self.parse_block()
        return {'type':'try','body':body,'handlers':handlers,'finally':final_body}

    # ——— return ———
    def parse_return(self):
        self.advance()  # 'return'
        expr = None
        if self.current().type!='SEMICOLON':
            expr = self.parse_expression()
        self.expect('SEMICOLON')
        return {'type':'return','expression':expr}

    # ——— if/else ———
    def parse_if(self):
        self.advance()   # 'if'
        self.expect('LPAREN')
        cond = self.parse_expression()
        self.expect('RPAREN')
        body = self.parse_block()
        else_body = None
        if self.current().type=='ID' and self.current().value=='else':
            self.advance()
            else_body = self.parse_block()
        return {'type':'if','condition':cond,'body':body,'else':else_body}

    # ——— while ———
    def parse_while(self):
        self.advance()
        self.expect('LPAREN')
        cond = self.parse_expression()
        self.expect('RPAREN')
        body = self.parse_block()
        return {'type':'while','condition':cond,'body':body}

    # ——— for ———
    def parse_for(self):
        self.advance()
        self.expect('LPAREN')
        init      = self.parse_statement()
        condition = self.parse_expression()
        self.expect('SEMICOLON')
        update    = self.parse_expression()
        self.expect('RPAREN')
        body = self.parse_block()
        return {'type':'for','init':init,'condition':condition,'update':update,'body':body}

    # ——— dichiarazioni ———
    def parse_declaration(self):
        mods = []
        while (self.current().type=='ID' and
               self.current().value in ('const','static','global','local','auto')):
            mods.append(self.current().value)
            self.advance()

        if 'auto' in mods:
            var_type = 'auto'
            name     = self.expect('ID').value
        else:
            var_type = self.expect('ID').value
            name     = self.expect('ID').value

        if var_type=='callable':
            return self.parse_callable_declaration(mods,name)

        if self.match('COLON'):
            self.expect('EQUAL')
        else:
            self.expect('EQUAL')
        value = self.parse_expression()
        self.expect('SEMICOLON')
        return {'type':'declaration','modifiers':mods,'var_type':var_type,'name':name,'value':value}

    def parse_callable_declaration(self, mods, name):
        self.expect('LPAREN')
        params=[]
        while self.current().type!='RPAREN':
            ptype = self.expect('ID').value
            pname = self.expect('ID').value
            params.append({'type':ptype,'name':pname})
            if self.current().type=='COMMA': self.advance()
        self.expect('RPAREN')
        self.expect('ARROW')
        return_type = self.expect('ID').value

        body=None
        if self.current().type=='LBRACE':
            body = self.parse_block()
            self.expect('SEMICOLON')
        else:
            self.expect('SEMICOLON')

        return {
            'type':'declaration_callable',
            'modifiers':mods,'name':name,
            'params':params,'return_type':return_type,'body':body
        }

    # ——— Expression-level ———
    def parse_expression(self):
        return self.parse_comparison()

    def parse_comparison(self):
        node = self.parse_add_sub()
        # ** ATTENZIONE: qui uso i TIPO corretto dal lexer **
        while self.current().type in ('LT','GT','LE','GE','EQEQ','NEQ'):
            op = self.current().value
            self.advance()
            right = self.parse_add_sub()
            node = {'type':'binary_op','op':op,'left':node,'right':right}
        return node

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
            raise SyntaxError("':' must be followed by '++' or '--'")
        return node

    def parse_primary(self):
        tok = self.current()
        if tok.type=='NUMBER':
            self.advance()
            return {'type':'literal','value':int(tok.value) if tok.value.isdigit() else float(tok.value)}
        if tok.type=='STRING':
            self.advance()
            return {'type':'literal','value':tok.value[1:-1]}
        if tok.type=='CHAR':
            self.advance()
            return {'type':'literal','value':tok.value[1]}
        if tok.type=='ID':
            name=tok.value; self.advance()
            if self.current().type=='LPAREN':
                self.expect('LPAREN')
                args=[]
                while self.current().type!='RPAREN':
                    args.append(self.parse_expression())
                    if self.current().type=='COMMA': self.advance()
                self.expect('RPAREN')
                return {'type':'call_callable','name':name,'args':args}
            return {'type':'identifier','name':name}
        if tok.type=='LPAREN':
            self.advance()
            expr=self.parse_expression()
            self.expect('RPAREN')
            return expr
        raise SyntaxError(f"Unexpected token {tok} in expression")
