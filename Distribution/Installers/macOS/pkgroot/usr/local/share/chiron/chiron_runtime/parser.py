# chiron_runtime/parser.py

from src.chiron_runtime.lexer import Token

class SyntaxError(Exception):
    pass

class Parser:
    def __init__(self, tokens, dev_mode=False):
        self.tokens   = list(tokens)
        self.pos      = 0
        self.dev_mode = dev_mode

    # ——— Core token methods ———

    def current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token('EOF', '')

    def peek(self, n=1) -> Token:
        i = self.pos + n
        if i < len(self.tokens):
            return self.tokens[i]
        return Token('EOF', '')

    def advance(self):
        if self.dev_mode:
            self.dbg(f"advance from {self.current()}")
        self.pos += 1

    def expect(self, ttype: str) -> Token:
        tok = self.current()
        if tok.type != ttype:
            raise SyntaxError(f"Expected {ttype} but got {tok}")
        self.advance()
        return tok

    def lookahead(self):
        self.advance(); next = self.current()
        self.pos -= 1
        return next

    def match(self, *ttypes):
        tok = self.current()
        if tok.type in ttypes:
            self.advance()
            return tok
        return None

    def dbg(self, msg: str):
        if self.dev_mode:
            print(f"[parse @ pos={self.pos}] {msg}")

    # ——— Entry point ———

    def parse(self):
        stmts = []
        while self.current().type != 'EOF':
            stmts.append(self.parse_statement())
        return stmts

    # ——— Statement-level ———

    def parse_statement(self):
        self.dbg("parse_statement")
        tok = self.current()

        # dispatch on leading keywords
        if tok.type == 'ID':
            if tok.value == 'if':
                return self.parse_if()
            if tok.value == 'while':
                return self.parse_while()
            if tok.value == 'for':
                return self.parse_for()
            if tok.value == 'try':
                return self.parse_try()
            if tok.value == 'return':
                return self.parse_return()
            if tok.value == 'import':
                return self.parse_import()
            if tok.value == 'from':
                return self.parse_from_import()

        # standalone call:  ID '(' ... ')' ';'
        if tok.type == 'ID' and self.peek().type == 'LPAREN':
            return self.parse_call_stmt()

        # declaration: modifiers/types
        if tok.type == 'ID' and tok.value in (
            'const','static','global','local','auto',
            'int','float','bool','char','str','callable'
        ):
            return self.parse_declaration()

        # fallback: expression statement
        expr = self.parse_expression()
        self.expect('SEMICOLON')
        return {'type':'expr_stmt','expr':expr}

    def parse_block(self):
        self.dbg("parse_block")
        self.expect('LBRACE')
        stmts = []
        while self.current().type != 'RBRACE':
            stmts.append(self.parse_statement())
        self.expect('RBRACE')
        return stmts

    # ——— Individual statements ———

    def parse_if(self):
        self.dbg("parse_if")
        self.expect('ID')              # 'if'
        self.expect('LPAREN')
        cond = self.parse_expression()
        self.expect('RPAREN')
        body = self.parse_block()
        else_body = None
        if self.current().type=='ID' and self.current().value=='else':
            self.advance()
            else_body = self.parse_block()
        return {'type':'if','condition':cond,'body':body,'else':else_body}

    def parse_while(self):
        self.dbg("parse_while")
        self.expect('ID')              # 'while'
        self.expect('LPAREN')
        cond = self.parse_expression()
        self.expect('RPAREN')
        body = self.parse_block()
        return {'type':'while','condition':cond,'body':body}

    def parse_for(self):
        self.dbg("parse_for")
        self.expect('ID')              # 'for'
        self.expect('LPAREN')
        init = self.parse_statement()
        cond = self.parse_expression()
        self.expect('SEMICOLON')
        update = self.parse_expression()
        self.expect('RPAREN')
        body = self.parse_block()
        return {'type':'for','init':init,'condition':cond,'update':update,'body':body}

    def parse_try(self):
        self.dbg("parse_try")
        self.expect('ID')              # 'try'
        try_body = self.parse_block()
        handlers = []
        while self.current().type=='ID' and self.current().value=='except':
            self.advance()
            exc_type = self.expect('ID').value
            self.expect('ID')          # 'as'
            exc_var  = self.expect('ID').value
            handler_body = self.parse_block()
            handlers.append({'exception':exc_type,'var':exc_var,'body':handler_body})
        final_body = None
        if self.current().type=='ID' and self.current().value=='finally':
            self.advance()
            final_body = self.parse_block()
        return {'type':'try','body':try_body,'handlers':handlers,'finally':final_body}

    def parse_return(self):
        self.dbg("parse_return")
        self.expect('ID')              # 'return'
        expr = None
        if self.current().type!='SEMICOLON':
            expr = self.parse_expression()
        self.expect('SEMICOLON')
        return {'type':'return','expression':expr}

    def parse_import(self):
        self.dbg("parse_import")
        self.expect('ID')  # 'import'
        modules = []

        while True:
            module = self.parse_module_path()
            alias = None
            if self.current().type == 'ID' and self.current().value == 'as':
                self.advance()
                alias = self.expect('ID').value
            modules.append((module, alias))

            if not self.match('COMMA'):
                break

        self.expect('SEMICOLON')
        return {'type': 'import', 'modules': modules}

    def parse_from_import(self):
        self.dbg("parse_from_import")
        self.expect('ID')  # 'from'
        module = self.parse_module_path()
        self.expect('ID')  # 'import'

        # Supporta 'from modulo import *' e 'from modulo import x, y'
        names = []
        if self.current().type == 'STAR':
            self.advance()
            names = ['*']
        else:
            names = [self.expect('ID').value]
            while self.match('COMMA'):
                names.append(self.expect('ID').value)

        self.expect('SEMICOLON')
        return {
            'type': 'from_import',
            'module': module,
            'names': names
        }

    # ——— Helper per nomi di modulo puntati ———
    def parse_module_path(self) -> str:
        """Legge ID(.ID)* e restituisce la stringa modulare, es. 'std.io'."""
        tok = self.expect('ID')
        parts = [tok.value]
        while self.match('DOT'):
            next_tok = self.expect('ID')
            parts.append(next_tok.value)
        path = '.'.join(parts)
        self.dbg(f"parsed module path: {path}")
        return path

    def parse_call_stmt(self):
        self.dbg("parse_call_stmt")
        name = self.expect('ID').value
        self.expect('LPAREN')
        args = []
        if self.current().type!='RPAREN':
            while True:
                args.append(self.parse_expression())
                if not self.match('COMMA'):
                    break
        self.expect('RPAREN')
        self.expect('SEMICOLON')
        return {'type':'call_callable','name':name,'args':args}

    # ——— Declarations ———

    def parse_declaration(self):
        self.dbg("parse_declaration")
        # collect modifiers
        mods = []
        while self.current().type=='ID' and self.current().value in ('const','static','global','local'):
            mods.append(self.current().value)
            self.advance()

        # type & name
        if 'auto' in mods:
            var_type = 'auto'
            name     = self.expect('ID').value
        else:
            var_type = self.expect('ID').value
            name     = self.expect('ID').value

        # callable vs var
        if var_type=='callable':
            return self.parse_callable_decl(mods,name)

        # variable: := or =
        if self.match('COLON'):
            self.expect('EQUAL')
        else:
            self.expect('EQUAL')

        value = self.parse_expression()
        self.expect('SEMICOLON')
        return {'type':'declaration','modifiers':mods,'var_type':var_type,'name':name,'value':value}

    def parse_callable_decl(self, mods, name):
        self.dbg("parse_callable_decl")
        self.expect('LPAREN')
        params = []
        if self.current().type!='RPAREN':
            while True:
                ptype = self.expect('ID').value
                pname = self.expect('ID').value
                params.append({'type':ptype,'name':pname})
                if not self.match('COMMA'):
                    break
        self.expect('RPAREN')
        self.expect('ARROW')
        return_type = self.expect('ID').value

        body = None
        if self.current().type=='LBRACE':
            body = self.parse_block()
            self.expect('SEMICOLON')
        else:
            self.expect('SEMICOLON')

        return {
            'type':'declaration_callable',
            'modifiers':mods,
            'name':name,
            'params':params,
            'return_type':return_type,
            'body':body
        }

    # ——— Expression-level (Pratt-ish) ———

    def parse_expression(self):
        self.dbg("parse_expression")
        return self.parse_or()

    def parse_or(self):
        node = self.parse_and()
        while self.current().type == 'ID' and self.current().value == 'or':
            op_tok = self.current()
            self.advance()
            right = self.parse_and()
            node = {'type': 'logic', 'op': 'or', 'left': node, 'right': right}
        return node

    def parse_and(self):
        node = self.parse_not()
        while self.current().type == 'ID' and self.current().value == 'and':
            op_tok = self.current()
            self.advance()
            right = self.parse_not()
            node = {'type': 'logic', 'op': 'and', 'left': node, 'right': right}
        return node

    def parse_not(self):
        if self.current().type == 'ID' and self.current().value == 'not':
            self.advance()
            expr = self.parse_not()
            return {'type': 'unary_logic', 'op': 'not', 'expr': expr}
        return self.parse_comparison()

    def parse_comparison(self):
        node = self.parse_add_sub()
        # includi le sigle esatte che il lexer restituisce
        while self.current().type in ('LT', 'GT', 'LE', 'GE', 'EQ', 'NE'):
            op_tok = self.current()
            self.advance()
            right = self.parse_add_sub()
            node = {
                'type': 'binary_op',
                'op': op_tok.value,
                'left': node,
                'right': right
            }
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
            if self.match('COLON'):
                expr = self.parse_unary()
                return {'type': 'unary_op', 'op': '++_pre', 'expr': expr}
            else:
                raise SyntaxError("Expected ':' after '++'")
        if self.match('DECREMENT'):
            if self.match('COLON'):
                expr = self.parse_unary()
                return {'type': 'unary_op', 'op': '--_pre', 'expr': expr}
            else:
                raise SyntaxError("Expected ':' after '--'")

        node = self.parse_primary()

        # accetta ':' anche se non seguito da ++ o -- (viene ignorato)
        if self.match('COLON'):
            if self.match('INCREMENT'):
                return {'type': 'unary_op', 'op': '++_post', 'expr': node}
            elif self.match('DECREMENT'):
                return {'type': 'unary_op', 'op': '--_post', 'expr': node}
            else:
                # interpretalo come "continuazione" e lascia passare
                pass

        return node

    def parse_primary(self):
        tok = self.current()
        if tok.type=='NUMBER':
            self.advance()
            val = float(tok.value) if '.' in tok.value else int(tok.value)
            return {'type':'literal','value':val}
        if tok.type=='STRING':
            self.advance()
            return {'type':'literal','value':tok.value[1:-1]}
        if tok.type=='CHAR':
            self.advance()
            return {'type':'literal','value':tok.value[1]}
        if tok.type == 'ID':
            node = {'type': 'identifier', 'name': tok.value}
            self.advance()

            # gestisce accessi a proprietà: a.b.c
            while self.match('DOT'):
                attr = self.expect('ID').value
                node = {'type': 'get_attr', 'object': node, 'attr': attr}

            # se c'è '(', è una chiamata
            if self.current().type == 'LPAREN':
                self.advance()
                args = []
                kwargs = {}
                while self.current().type != 'RPAREN':
                    if self.current().type == 'ID' and self.lookahead().type == 'EQUAL':
                        key = self.expect('ID').value
                        self.expect('EQUAL')
                        val = self.parse_expression()
                        kwargs[key] = val
                    else:
                        args.append(self.parse_expression())
                    if self.current().type == 'COMMA':
                        self.advance()
                self.expect('RPAREN')
                node = {'type': 'call_callable', 'name': node, 'args': args, 'kwargs': kwargs}
            return node
        if tok.type=='LPAREN':
            self.advance()
            expr = self.parse_expression()
            self.expect('RPAREN')
            return expr
        raise SyntaxError(f"Unexpected token {tok} in primary")
