from chiron_runtime.lexer import Token
import importlib

class SyntaxError(Exception):
    pass

class Parser:
    def __init__(self, tokens):
        self.tokens = list(tokens)
        self.pos = 0

        # dispatch table per statement-level
        self.stmt_parsers = {
            'try':     self.parse_try,
            'return':  self.parse_return,
            'if':      self.parse_if,
            'while':   self.parse_while,
            'for':     self.parse_for,
            'import':  self.parse_import,
            'from':    self.parse_from_import,
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

    # ——— Statement-level dispatcher ———

    def parse_statement(self):
        tok = self.current()

        # 1) keyword dispatch
        if tok.type == 'ID' and tok.value in self.stmt_parsers:
            return self.stmt_parsers[tok.value]()

        # 2) dichiarazione
        if tok.type == 'ID' and tok.value in (
                'const','static','global','local','auto',
                'int','float','bool','char','str','callable'):
            return self.parse_declaration()

        # 3) espressione standalone
        expr = self.parse_expression()
        self.expect('SEMICOLON')
        return {'type':'expr_stmt','expr':expr}

    # ——— Try / Except / Finally ———

    def parse_try(self):
        self.advance()                # consume 'try'
        self.expect('LBRACE')
        try_body = self.parse_block()
        handlers = []
        while self.current().type == 'ID' and self.current().value == 'except':
            self.advance()            # 'except'
            exc_type = self.expect('ID').value
            self.expect('ID')         # 'as'
            exc_var = self.expect('ID').value
            self.expect('LBRACE')
            handler_body = self.parse_block()
            handlers.append({
                'exception': exc_type,
                'var':       exc_var,
                'body':      handler_body
            })
        final_body = None
        if self.current().type == 'ID' and self.current().value == 'finally':
            self.advance()            # 'finally'
            self.expect('LBRACE')
            final_body = self.parse_block()
        return {
            'type':     'try',
            'body':     try_body,
            'handlers': handlers,
            'finally':  final_body
        }

    # ——— Return ———

    def parse_return(self):
        self.advance()                # consume 'return'
        expr = None
        if self.current().type != 'SEMICOLON':
            expr = self.parse_expression()
        self.expect('SEMICOLON')
        return {'type': 'return', 'expression': expr}

    # ——— If / While / For ———

    def parse_if(self):
        self.advance()                # 'if'
        self.expect('LPAREN')
        cond = self.parse_expression()
        self.expect('RPAREN')
        self.expect('LBRACE')
        body = self.parse_block()
        else_body = None
        if self.current().type == 'ID' and self.current().value == 'else':
            self.advance()
            self.expect('LBRACE')
            else_body = self.parse_block()
        return {'type':'if', 'condition':cond, 'body':body, 'else':else_body}

    def parse_while(self):
        self.advance()                # 'while'
        self.expect('LPAREN')
        cond = self.parse_expression()
        self.expect('RPAREN')
        self.expect('LBRACE')
        body = self.parse_block()
        return {'type':'while', 'condition':cond, 'body':body}

    def parse_for(self):
        self.advance()                # 'for'
        self.expect('LPAREN')
        init = self.parse_statement()
        condition = self.parse_expression()
        self.expect('SEMICOLON')
        update = self.parse_expression()
        self.expect('RPAREN')
        self.expect('LBRACE')
        body = self.parse_block()
        return {
            'type':      'for',
            'init':      init,
            'condition': condition,
            'update':    update,
            'body':      body
        }

    # ——— Import / From-Import ———

    def parse_import(self):
        # import modulo [as alias] ;
        self.expect('ID')  # 'import'
        module_name = self.expect('ID').value  # es. std
        # supporta nested modules es. std.io
        while self.current().type == 'DOT':
            self.advance()
            module_name += '.' + self.expect('ID').value

        alias = None
        if self.current().type == 'ID' and self.current().value == 'as':
            self.advance()
            alias = self.expect('ID').value

        self.expect('SEMICOLON')
        return {
            'type':        'import',
            'module':      module_name,
            'alias':       alias
        }

    def parse_from_import(self):
        # from modulo import name [, name2, ...] [as alias] ;
        self.expect('ID')  # 'from'
        module_name:str = self.expect('ID').value
        while self.current().type == 'DOT':
            self.advance()
            module_name += '.' + self.expect('ID').value
            module_name += module_name.replace('std','')


        self.advance()

        names = []

        if  self.current().type == 'STAR':
            module = importlib.import_module('chiron_runtime.stdlib.'+module_name)
            objects = module.__all__
            names = [(x, x) for x in objects]


        elif self.current().type == 'ID':
            names = []
            while True:
                name = self.current().value
                print(name)
                as_alias = None
                if self.current().type == 'ID' and self.current().value == 'as':
                    self.advance()
                    as_alias = self.expect('ID').value
                names.append( (name, as_alias) )
                if self.current().type == 'COMMA':
                    self.advance()
                    continue
                break

        self.advance()

        self.expect('SEMICOLON')
        return {
            'type':    'from_import',
            'module':  module_name,
            'names':   names  # list of (name, alias)
        }


    # ——— Declarations ———

    def parse_declaration(self):
        # raccogli modifiers
        mods = []
        while self.current().type == 'ID' and self.current().value in (
                'const','static','global','local','auto'):
            mods.append(self.current().value)
            self.advance()

        # tipo e nome
        if 'auto' in mods:
            var_type = 'auto'
            name     = self.expect('ID').value
        else:
            var_type = self.expect('ID').value
            name     = self.expect('ID').value

        # callable?
        if var_type == 'callable':
            return self.parse_callable_declaration(mods, name)

        # altrimenti variable declaration / assignment
        if self.match('COLON'):
            self.expect('EQUAL')
        else:
            self.expect('EQUAL')
        value = self.parse_expression()
        self.expect('SEMICOLON')
        return {
            'type':      'declaration',
            'modifiers': mods,
            'var_type':  var_type,
            'name':      name,
            'value':     value
        }

    def parse_callable_declaration(self, mods, name):
        self.expect('LPAREN')
        params = []
        while self.current().type != 'RPAREN':
            ptype = self.expect('ID').value
            pname = self.expect('ID').value
            params.append({'type':ptype,'name':pname})
            if self.current().type == 'COMMA':
                self.advance()
        self.expect('RPAREN')

        self.expect('ARROW')
        return_type = self.expect('ID').value

        # corpo opzionale
        if self.current().type == 'LBRACE':
            self.expect('LBRACE')
            body = self.parse_block()
            self.expect('SEMICOLON')
        else:
            body = None
            self.expect('SEMICOLON')

        return {
            'type':        'declaration_callable',
            'modifiers':   mods,
            'name':        name,
            'params':      params,
            'return_type': return_type,
            'body':        body
        }

    # ——— Block parser ———

    def parse_block(self):
        stmts = []
        brace = 1
        while brace > 0:
            tok = self.current()
            if tok.type == 'LBRACE':
                brace += 1
                self.advance()
            elif tok.type == 'RBRACE':
                brace -= 1
                self.advance()
            else:
                stmts.append(self.parse_statement())
        return stmts

    # ——— Expression-level ———

    def parse_expression(self):
        return self.parse_comparison()

    def parse_comparison(self):
        node = self.parse_add_sub()
        while self.current().type in ('LT', 'GT', 'LE', 'GE', 'EQEQ', 'NEQ'):
            op_tok = self.current()
            self.advance()
            right = self.parse_add_sub()
            node = {
                'type': 'binary_op',
                'op': op_tok.value,  # ad esempio '==', '<=', '>'…
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
            name = tok.value
            self.advance()
            if self.current().type == 'LPAREN':
                self.advance()
                args = []
                while self.current().type != 'RPAREN':
                    args.append(self.parse_expression())
                    if self.current().type == 'COMMA':
                        self.advance()
                self.expect('RPAREN')
                return {'type':'call_callable','name':name,'args':args}
            return {'type':'identifier','name':name}
        if tok.type == 'LPAREN':
            self.advance()
            expr = self.parse_expression()
            self.expect('RPAREN')
            return expr

        raise SyntaxError(f"Unexpected token {tok} in expression")
