# src/chiron_runtime/parser.py
from traceback import print_tb

from chiron_runtime.lexer import Token

class SyntaxError(Exception):
    pass

class Parser:
    def __init__(self, tokens):
        self.tokens = list(tokens)
        print(self.tokens)
        self.pos = 0

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

    # -----------------------------------------------------------------------
    # PUBLIC ENTRY POINT: parse() → restituisce l’AST (lista di statement)
    # -----------------------------------------------------------------------
    def parse(self):
        stmts = []
        while self.current().type != 'EOF':
            stmts.append(self.parse_statement())
        return stmts

    # -----------------------------------------------------------------------
    # PARSER STATEMENT-LEVEL
    # -----------------------------------------------------------------------
    def parse_statement(self):
        tok = self.current()

        # ——— 1) import / from import ———
        if tok.type == 'ID' and tok.value == 'import':
            return self.parse_import()
        if tok.type == 'ID' and tok.value == 'from':
            return self.parse_from_import()

        # ——— 2) try / except / finally ———
        if tok.type == 'ID' and tok.value == 'try':
            return self.parse_try()

        # ——— 3) return ———
        if tok.type == 'ID' and tok.value == 'return':
            return self.parse_return()

        # ——— 4) if / while / for ———
        if tok.type == 'ID' and tok.value == 'if':
            return self.parse_if()
        if tok.type == 'ID' and tok.value == 'while':
            return self.parse_while()
        if tok.type == 'ID' and tok.value == 'for':
            return self.parse_for()

        # ——— 5) dichiarazione (potrebbe iniziare con modificatori o con tipo) ———
        # Ora il set di “inizio dichiarazione” contiene solo veri modificatori oppure parole-chiave di tipo
        if tok.type == 'ID' and tok.value in (
            'const','static','global','local','auto',
            'callable',  # gestito in modo particolare
            'int','float','bool','char','str',
            'array','tuple','map'
        ):
            return self.parse_declaration()

        # ——— 6) espressione standalone terminata da ';' ———
        expr = self.parse_expression()
        self.expect('SEMICOLON')
        return {'type':'expr_stmt', 'expr': expr}


    # -----------------------------------------------------------------------
    # PARSERS PER import / from_import
    # -----------------------------------------------------------------------
    def parse_import(self):
        # 'import' module_path (, module_path)* ';'
        self.expect('ID')  # 'import'
        modules = [ self.parse_module_path() ]
        while self.match('COMMA'):
            modules.append(self.parse_module_path())
        self.expect('SEMICOLON')
        return {'type':'import', 'modules': modules}

    def parse_from_import(self):
        # 'from' module_path 'import' name (',' name)* ';'
        self.expect('ID')  # 'from'
        module = self.parse_module_path()
        self.expect('ID')  # 'import'
        names = []
        # il nome può essere '*' oppure ID
        if self.current().type == 'STAR':
            self.advance()
            names.append('*')
        else:
            names.append(self.expect('ID').value)
            while self.match('COMMA'):
                names.append(self.expect('ID').value)
        self.expect('SEMICOLON')
        return {'type':'from_import', 'module': module, 'names': names}

    def parse_module_path(self):
        # modulo annidato: ID ('.' ID)* → restituisce stringa con i puntini
        parts = [ self.expect('ID').value ]
        while self.match('DOT'):
            parts.append(self.expect('ID').value)
        return '.'.join(parts)


    # -----------------------------------------------------------------------
    # PARSERS PER try/except/finally
    # -----------------------------------------------------------------------
    def parse_try(self):
        # try { ... } (except ID as var { ... })* (finally { ... })?
        self.advance()  # 'try'
        self.expect('LBRACE')
        try_body = self.parse_block()

        handlers = []
        while self.current().type == 'ID' and self.current().value == 'except':
            self.advance()  # 'except'
            exc_type = self.expect('ID').value
            self.expect('ID')  # 'as'
            exc_var = self.expect('ID').value
            self.expect('LBRACE')
            hbody = self.parse_block()
            handlers.append({
                'exception': exc_type,
                'var':       exc_var,
                'body':      hbody
            })

        final_body = None
        if self.current().type == 'ID' and self.current().value == 'finally':
            self.advance()  # 'finally'
            self.expect('LBRACE')
            final_body = self.parse_block()

        return {
            'type':     'try',
            'body':     try_body,
            'handlers': handlers,
            'finally':  final_body
        }

    def parse_return(self):
        self.advance()  # 'return'
        expr = None
        if self.current().type != 'SEMICOLON':
            expr = self.parse_expression()
        self.expect('SEMICOLON')
        return { 'type': 'return', 'expression': expr }


    # -----------------------------------------------------------------------
    # PARSERS PER if / while / for
    # -----------------------------------------------------------------------
    def parse_if(self):
        # if '(' cond ')' '{' body '}' (else '{' else_body '}')?
        self.advance()  # consume 'if'
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

        return { 'type':'if', 'condition': cond, 'body': body, 'else': else_body }

    def parse_while(self):
        # while '(' cond ')' '{' body '}'
        self.advance()  # 'while'
        self.expect('LPAREN')
        cond = self.parse_expression()
        self.expect('RPAREN')
        self.expect('LBRACE')
        body = self.parse_block()
        return { 'type':'while', 'condition': cond, 'body': body }

    def parse_for(self):
        # for '(' init_stmt cond ';' update_expr ')' '{' body '}'
        self.advance()  # 'for'
        self.expect('LPAREN')
        init = self.parse_statement()       # parse_statement consuma fino al ';'
        cond = self.parse_expression()
        self.expect('SEMICOLON')
        update = self.parse_expression()
        self.expect('RPAREN')
        self.expect('LBRACE')
        body = self.parse_block()
        return {
            'type':'for',
            'init': init,
            'condition': cond,
            'update': update,
            'body': body
        }


    # -----------------------------------------------------------------------
    # PARSER PER dichiarazioni (variabili e funzioni)
    # -----------------------------------------------------------------------
    def parse_declaration(self):
        # ——— raccogliamo solo i veri modifiers ———
        mods = []
        while self.current().type == 'ID' and self.current().value in (
            'const', 'static', 'global', 'local', 'auto'
        ):
            mods.append(self.current().value)
            self.advance()

        # ——— caso “callable”: stiamo dichiarando una funzione ———
        if self.current().type == 'ID' and self.current().value == 'callable':
            mods.append('callable')
            self.advance()  # consumiamo “callable”
            name = self.expect('ID').value
            return self.parse_callable_decl(mods, name)

        # ——— caso “auto”: il tipo è implicito “auto” ———
        if 'auto' in mods:
            var_type = {'type': 'simple', 'name': 'auto'}
            name = self.expect('ID').value

        else:
            # ——— altrimenti dobbiamo leggere un tipo (semplice o generic) ———
            var_type = self.parse_type()
            name = self.expect('ID').value

        # ——— inizializzazione di variabile con “:=” o “=” ———
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

    def parse_callable_decl(self, mods, name):
        # siamo appena dopo ‘callable’ e abbiamo già letto il nome
        self.expect('LPAREN')
        params = []
        while self.current().type != 'RPAREN':
            # in questo contesto “ptype” è un ID semplice (non generic) per ora
            ptype = self.expect('ID').value
            pname = self.expect('ID').value
            params.append({'type': ptype, 'name': pname})
            if self.match('COMMA'):
                continue
            else:
                break
        self.expect('RPAREN')
        # parse arrow e tipo di ritorno
        self.expect('ARROW')
        return_type = self.expect('ID').value

        # corpo facoltativo
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


    # -----------------------------------------------------------------------
    # PARSER PER TYPE (semplici o generic)
    # -----------------------------------------------------------------------
    def parse_type(self):
        # read an ID (ad esempio “int”, “str”, “array”, “tuple”, “map”)
        base = self.expect('ID').value
        # se è un generic, consuma '<' type (',' type)* '>'
        print("PARSE_TYPE",self.current())
        if self.match('LT'):
            type_params = []
            type_params.append(self.parse_type())
            while self.match('COMMA'):
                type_params.append(self.parse_type())
            self.expect('GT')
            return {'type':'generic', 'name': base, 'params': type_params}
        else:
            return {'type':'simple', 'name': base}


    # -----------------------------------------------------------------------
    # PARSER PER BLOCKS: { …stmts… }
    # -----------------------------------------------------------------------
    def parse_block(self):
        # siamo subito dopo '{'
        stmts = []
        brace = 1
        self.advance()  # consumiamo '{'

        while brace > 0:
            tok = self.current()
            if tok.type == 'LBRACE':
                brace += 1
                stmts.append(self.parse_statement())
            elif tok.type == 'RBRACE':
                brace -= 1
                self.advance()
                # se brace scende a 0, abbiamo finito il blocco
                if brace == 0:
                    break
            else:
                stmts.append(self.parse_statement())
        return stmts


    # -----------------------------------------------------------------------
    # PARSER PER EXPRESSION-LEVEL (confronti aritmetici + logico + literali)
    # -----------------------------------------------------------------------
    def parse_expression(self):
        return self.parse_comparison()

    def parse_comparison(self):
        node = self.parse_add_sub()
        # confronti: <, >, <=, >=, ==, !=
        while self.current().type in ('LT','GT','LE','GE','EQEQ','NEQ'):
            op_tok = self.current()
            self.advance()
            right = self.parse_add_sub()
            node = {'type':'binary_op', 'op': op_tok.value, 'left': node, 'right': right}

        # aggiunta: operatori logici 'and', 'or'
        while self.current().type == 'ID' and self.current().value in ('and','or'):
            op_tok = self.current()
            self.advance()
            right = self.parse_add_sub()
            node = {'type':'logic', 'op': op_tok.value, 'left': node, 'right': right}

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
        # pre-incremento/decremento
        if self.match('INCREMENT'):
            self.expect('COLON')
            expr = self.parse_unary()
            return {'type':'unary_op','op':'++_pre','expr':expr}
        if self.match('DECREMENT'):
            self.expect('COLON')
            expr = self.parse_unary()
            return {'type':'unary_op','op':'--_pre','expr':expr}

        node = self.parse_primary()

        # post-incremento/decremento
        if self.match('COLON'):
            if self.match('INCREMENT'):
                return {'type':'unary_op','op':'++_post','expr':node}
            if self.match('DECREMENT'):
                return {'type':'unary_op','op':'--_post','expr':node}
            # NOTA: abbiamo tolto l’errore “':' must be followed by ++/--” per permettere l’uso di “:” in altri contesti
            # Se vedi solo “:” senza ++/--, lo ignoriamo.
        return node

    def parse_primary(self):
        tok = self.current()

        # ——— NUMBER literal ———
        if tok.type == 'NUMBER':
            self.advance()
            val = float(tok.value) if '.' in tok.value else int(tok.value)
            return {'type':'literal','value':val}

        # ——— STRING literal ———
        if tok.type == 'STRING':
            self.advance()
            return {'type':'literal','value': tok.value[1:-1]}

        # ——— CHAR literal ———
        if tok.type == 'CHAR':
            self.advance()
            return {'type':'literal','value': tok.value[1]}

        # ——— ARRAY literal ———: [ expr, expr, … ]
        if tok.type == 'LBRACKET':
            self.advance()  # consumiamo “[”
            elements = []
            if self.current().type != 'RBRACKET':
                while True:
                    elements.append(self.parse_expression())
                    if self.current().type == 'COMMA':
                        self.advance()
                        continue
                    break
            self.expect('RBRACKET')
            return {'type': 'array_literal', 'elements': elements}

        # ——— MAP literal ———: { key: value, … }
        if tok.type == 'LBRACE':     # '{'
            self.advance()
            entries = []
            if self.current().type != 'RBRACE':
                # almeno una coppia key:value
                key_node = self.parse_expression()
                val_node = self.parse_expression()
                entries.append((key_node, val_node))

                while self.match('COMMA'):
                    key_node = self.parse_expression()
                    val_node = self.parse_expression()
                    entries.append((key_node, val_node))

            self.expect('RBRACE')
            return {'type':'map_literal', 'entries': entries}

        # ——— IDENTIFICATORE / chiamata ———
        if tok.type == 'ID':
            name = tok.value
            self.advance()
            # Possibile chiamata a funzione (se segue '(')
            if self.current().type == 'LPAREN':
                self.expect('LPAREN')
                args = []
                while self.current().type != 'RPAREN':
                    # supporto keyword arguments: ID '=' expr
                    if self.current().type == 'ID':
                        saved_pos = self.pos
                        key_candidate = self.expect('ID').value
                        if self.match('EQUAL'):
                            val_node = self.parse_expression()
                            args.append({'type':'kwarg', 'key': key_candidate, 'value': val_node})
                        else:
                            # rollback: non era keyword, torna indietro e parse come espressione
                            self.pos = saved_pos
                            args.append(self.parse_expression())
                        if self.current().type == 'COMMA':
                            self.advance()
                        else:
                            continue
                    else:
                        args.append(self.parse_expression())
                        if self.current().type == 'COMMA':
                            self.advance()
                        else:
                            continue
                self.expect('RPAREN')
                return {'type':'call_callable', 'name': name, 'args': args}
            return {'type':'identifier', 'name': name}

        # ——— TUPLE literal oppure grouping con '(' ———
        if tok.type == 'LPAREN':
            self.advance()
            first_expr = self.parse_expression()
            if self.match('COMMA'):
                # almeno due elementi per essere una tupla
                elements = [ first_expr ]
                elements.append(self.parse_expression())
                while self.match('COMMA'):
                    elements.append(self.parse_expression())
                self.expect('RPAREN')
                return {'type':'tuple_literal', 'elements': elements}
            else:
                # altrimenti era semplicemente (expr)
                self.expect('RPAREN')
                return first_expr

        raise SyntaxError(f"Unexpected token {tok} in expression")


    # -----------------------------------------------------------------------
    # PARSER PER TYPE (semplici o generic)
    # -----------------------------------------------------------------------
    def parse_type(self):
        # Leggiamo un ID (es. “int”, “str”, “array”, “tuple”, “map”)
        base = self.expect('ID').value
        # Se segue '<', è generic: base '<' type (',' type)* '>'
        if self.match('LT'):
            type_params = []
            type_params.append(self.parse_type())
            while self.match('COMMA'):
                type_params.append(self.parse_type())
            self.expect('GT')
            return {'type':'generic', 'name': base, 'params': type_params}
        # Altrimenti era un tipo semplice
        return {'type':'simple', 'name': base}