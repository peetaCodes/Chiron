# src/chiron_runtime/parser.py

from chiron_runtime.lexer import Token

class SyntaxError(Exception):
    pass

class Parser:
    def __init__(self, tokens):
        self.tokens = list(tokens)
        self.pos = 0

    def current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token('EOF', '')

    def peek(self, n: int) -> Token:
        idx = self.pos + n
        if idx < len(self.tokens):
            return self.tokens[idx]
        return Token('EOF', '')

    def goback(self):
        self.pos -= 1

    def advance(self):
        self.pos += 1

    def expect(self, ttype: str) -> Token:
        tok = self.current()
        if tok.type != ttype:
            raise SyntaxError(f"Expected {ttype} but got {tok}")
        self.advance()
        return tok

    def previous(self) -> Token:
        self.goback()
        tok = self.current()
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

        # ——— 6) assignment: riconosce sia x = … sia obj.prop = … ———
        if self._is_assignment_lhs():
            return self.parse_assignment()

        # ——— 6) dichiarazione (se inizia con tipo/modificatore) ———
        if tok.type == 'ID' and tok.value in (
            'const','static','global','local','auto',
            'int','float','bool','char','str','callable',
            'array','tuple','map'
        ):
            return self.parse_declaration()

        # ——— 7) espressione standalone terminata da ';' ———
        expr = self.parse_expression()
        # Consuma il ';' se c’è, altrimenti va bene comunque.
        if self.current().type == 'SEMICOLON':
            self.advance()
        return {'type':'expr_stmt', 'expr': expr}

    def _is_assignment_lhs(self) -> bool:
        """
        Ritorna True se da current() in avanti posso leggere
        ID (DOT ID)* seguito da '=' o ':='
        """
        idx = self.pos
        # deve iniziare con un ID
        if idx >= len(self.tokens) or self.tokens[idx].type != 'ID':
            return False
        idx += 1
        # poi zero o più .ID
        while idx < len(self.tokens) and self.tokens[idx].type == 'DOT':
            idx += 1
            if idx >= len(self.tokens) or self.tokens[idx].type != 'ID':
                return False
            idx += 1
        # ora ci aspettiamo COLON o EQUAL
        if idx < len(self.tokens) and self.tokens[idx].type in ('COLON', 'EQUAL'):
            return True
        return False

    # -----------------------------------------------------------------------
    # PARSER DELL’ASSIGNMENT (ID = expr; oppure ID := expr;)
    # -----------------------------------------------------------------------
    def parse_assignment(self):
        # — 1) parse lvalue: può essere ID o ID(.ID)* → restituiamo un node lvalue
        # iniziamo con un identifier
        base_name = self.expect('ID').value
        lhs_node = {'type': 'identifier', 'name': base_name}

        # gestiamo chain di ".prop"
        while self.match('DOT'):
            prop = self.expect('ID').value
            lhs_node = {
                'type': 'get_attr',
                'object': lhs_node,
                'name': prop
            }

        # — 2) consumiamo := oppure =
        if self.match('COLON'):
            self.expect('EQUAL')
        else:
            self.expect('EQUAL')

        # — 3) parse della espressione RHS
        value = self.parse_expression()

        # — 4) optional ';'
        if self.current().type == 'SEMICOLON':
            self.advance()

        return {
            'type': 'assignment',
            'target': lhs_node,
            'value': value
        }

    # -----------------------------------------------------------------------
    # PARSERS PER import / from_import
    # -----------------------------------------------------------------------
    def parse_import(self):
        # 'import' module_path ( 'as' alias)? (',' module_path ( 'as' alias)? )* ';'
        self.expect('ID')  # 'import'
        modules = []
        while True:
            path = self.parse_module_path()
            alias = None
            if self.match('ID') and self.previous().value == 'as':
                alias = self.expect('ID').value
            modules.append({'path': path, 'alias': alias})
            if not self.match('COMMA'):
                break
        self.expect('SEMICOLON')
        return {'type': 'import', 'modules': modules}

    def parse_from_import(self):
        # 'from' module_path 'import' name ( 'as' alias)? (',' name ( 'as' alias)? )* ';'
        self.expect('ID')  # 'from'
        module_path = self.parse_module_path()
        self.expect('ID')  # 'import'
        names = []
        while True:
            if self.current().type == 'STAR':
                self.advance()
                name = '*'
                alias = None
            else:
                name = self.expect('ID').value
                alias = None
                if self.match('ID') and self.previous().value == 'as':
                    alias = self.expect('ID').value
            names.append({'name': name, 'alias': alias})
            if not self.match('COMMA'):
                break
        self.expect('SEMICOLON')
        return {'type': 'from_import', 'module': module_path, 'names': names}

    def parse_module_path(self):
        # modulo annidato: ID ('.' ID)* → stringa tipo "std.io"
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
        # ——— raccogliamo SOLO modifiers veri ———
        modifier_tokens = ('const','static','global','local')
        mods = []
        while self.current().type == 'ID' and self.current().value in modifier_tokens:
            mods.append(self.current().value)
            self.advance()


        # ——— caso “callable” ———
        if self.current().type == 'ID' and self.current().value == 'callable':
            self.advance()
            name = self.expect('ID').value
            return self.parse_callable_decl(mods, name)

        # ——— ora leggiamo il tipo: "auto" o un vero type ———
        if self.current().type == 'ID' and self.current().value == 'auto':
            var_type = {'type':'simple','name':'auto'}
            self.advance()
        else:
            var_type = self.parse_type()

        # ——— quindi il nome della variabile ———
        name = self.expect('ID').value

        # ——— opzionale inizializzatore ———
        value = None
        if self.current().type in ('COLON', 'EQUAL'):
            # supportiamo ':=' oppure '='
            if self.match('COLON'):
                self.expect('EQUAL')
            else:
                self.expect('EQUAL')
            value = self.parse_expression()

        # ——— punto e virgola di chiusura ———
        self.expect('SEMICOLON')
        return {
            'type': 'declaration',
            'modifiers': mods,
            'var_type': var_type,
            'name': name,
            'value': value  # può restare None
        }

    def parse_callable_decl(self, mods, name):
        # siamo già “dentro” dopo aver letto “callable name”
        self.expect('LPAREN')
        params = []
        while self.current().type != 'RPAREN':
            ptype = self.expect('ID').value
            pname = self.expect('ID').value
            params.append({'type': ptype, 'name': pname})
            if self.match('COMMA'):
                continue
            else:
                break
        self.expect('RPAREN')

        self.expect('ARROW')
        return_type = self.expect('ID').value

        # corpo facoltativo
        if self.current().type == 'LBRACE':
            self.expect('LBRACE')
            body = self.parse_block()
            # Consuma un eventuale ';' di terminazione dopo la '}'
            if self.current().type == 'SEMICOLON':
                self.advance()
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
    # PARSER PER TYPE (semplici o generici)
    # -----------------------------------------------------------------------
    def parse_type(self):
        base = self.expect('ID').value
        # se è un generic, consuma '<' type (',' type)* '>'
        # se è un generic, consuma '<' type (',' type)* '>'
        if self.match('LT'):
            params = [ self.parse_type() ]
            while self.match('COMMA'):
                params.append(self.parse_type())
            self.expect('GT')
            # restrizione: array<T> deve avere un **solo** parametro
            if base == 'array' and len(params) != 1:
                raise SyntaxError(f"Generic 'array' expects exactly 1 type parameter, got {len(params)}")
            # restrizione: tuple<T1,T2,..> va sempre dichiarata con <..>, ma la _letterale_
            # tuple si usa solo con tonde ()—e non dobbiamo toccare qui, perché il parser
            # per il literal tuple è già vincolato agli LPAREN

        # Altrimenti era un tipo semplice
        return {'type':'simple', 'name': base}


    # -----------------------------------------------------------------------
    # PARSER PER BLOCKS: { …stmts… }
    # -----------------------------------------------------------------------
    def parse_block(self):
        stmts = []
        brace = 1
        self.advance()  # consumiamo '{'
        while brace > 0:
            tok = self.current()
            if tok.type == 'LBRACE':
                brace += 1
                self.advance()
            elif tok.type == 'RBRACE':
                brace -= 1
                self.advance()
                if brace == 0:
                    break
            else:
                stmts.append(self.parse_statement())
        return stmts


    # -----------------------------------------------------------------------
    # PARSER PER EXPRESSION-LEVEL
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

        # operatori logici 'and' / 'or'
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
        # pre‐incremento/decremento: ++:x oppure --:x
        if self.match('INCREMENT'):
            self.expect('COLON')
            expr = self.parse_unary()
            return {'type':'unary_op','op':'++_pre','expr':expr}
        if self.match('DECREMENT'):
            self.expect('COLON')
            expr = self.parse_unary()
            return {'type':'unary_op','op':'--_pre','expr':expr}

        node = self.parse_primary()

        # post‐incremento/decremento: x:++ oppure x:--
        if self.match('COLON'):
            if self.match('INCREMENT'):
                return {'type':'unary_op','op':'++_post','expr':node}
            if self.match('DECREMENT'):
                return {'type':'unary_op','op':'--_post','expr':node}

        return node


    def parse_primary(self):
        tok = self.current()

        # ——— NUMBER literal ———
        if tok.type == 'NUMBER':
            self.advance()
            val = float(tok.value) if '.' in tok.value else int(tok.value)
            node = {'type':'literal','value':val}

        # ——— STRING literal ———
        elif tok.type == 'STRING':
            self.advance()
            node = {'type':'literal','value': tok.value[1:-1]}

        # ——— CHAR literal ———
        elif tok.type == 'CHAR':
            self.advance()
            node = {'type':'literal','value': tok.value[1]}

        # ——— ARRAY literal ———
        elif tok.type == 'LBRACKET':
            self.advance()
            elements = []
            if self.current().type != 'RBRACKET':
                while True:
                    elements.append(self.parse_expression())
                    if self.current().type == 'COMMA':
                        self.advance()
                        continue
                    break
            self.expect('RBRACKET')
            node = {'type':'array_literal', 'elements': elements}

        # ——— MAP literal o FUNCTION anonima ———
        elif tok.type == 'LBRACE':
            second_tok = self.peek(1)
            third_tok  = self.peek(2)
            if (second_tok.type in ('STRING','CHAR','ID','NUMBER','LPAREN')
                    and third_tok.type == 'COLON'):
                # MAP literal
                self.advance()
                entries = []
                if self.current().type != 'RBRACE':
                    while True:
                        key_node = self.parse_expression()
                        self.expect('COLON')
                        val_node = self.parse_expression()
                        entries.append((key_node, val_node))
                        if self.match('COMMA'):
                            continue
                        break
                self.expect('RBRACE')
                node = {'type':'map_literal', 'entries': entries}
            else:
                # anonymous function
                self.advance()
                stmts = []
                depth = 1
                while depth > 0:
                    t2 = self.current()
                    if t2.type == 'LBRACE':
                        depth += 1; self.advance()
                    elif t2.type == 'RBRACE':
                        depth -= 1; self.advance()
                    else:
                        stmts.append(self.parse_statement())
                node = {'type':'anonymous_func', 'body': stmts}

        # ——— IDENTIFICATORE / chiamata ———
        # ——— IDENTIFICATORE / POSSIBILE chiamata ———
        elif tok.type == 'ID':
            name = tok.value
            self.advance()

            # se segue '(', è una chiamata di funzione
            if self.current().type == 'LPAREN':
                self.advance()  # consumiamo '('
                args = []

                # finché non troviamo ')', analizziamo un argomento
                while self.current().type != 'RPAREN':
                    # caso keyword argument: ID '=' expr
                    if self.current().type == 'ID' and self.peek(1).type == 'EQUAL':
                        key = self.current().value
                        self.advance()        # consumiamo la chiave
                        self.advance()        # consumiamo '='
                        val = self.parse_expression()
                        args.append({'type':'kwarg', 'key': key, 'value': val})
                    else:
                        # altrimenti è un argomento posizionale
                        args.append(self.parse_expression())

                    # se c'è la virgola, consumala e proseguiamo
                    if self.current().type == 'COMMA':
                        self.advance()
                        continue
                    break

                self.expect('RPAREN')
                return {'type':'call_callable', 'name': name, 'args': args}

            # altrimenti è un semplice identificatore
            return {'type':'identifier', 'name': name}


        # ——— TUPLE literal o grouping ———
        elif tok.type == 'LPAREN':
            # guardo i due token successivi
            second = self.peek(1)
            third = self.peek(2)
            # pattern: '(' ID ID (',' ID ID)* ')'
            if second.type == 'ID' and third.type == 'ID':
                self.advance()  # consumi '('
                params = []
                while True:
                    typ = self.expect('ID').value
                    name = self.expect('ID').value
                    params.append({'type': typ, 'name': name})
                    if self.match('COMMA'):
                        continue
                    break
                self.expect('RPAREN')
                return {'type': 'typed_params', 'params': params}

            # ——— Tuple‑literal oppure group ———
            # se invece non è typed‑params, ricadremo qui
            # se c’è subito una virgola, è tuple‑literal
            # altrimenti è solo grouping
            self.advance()
            first = self.parse_expression()
            if self.match('COMMA'):
                elements = [first]
                while True:
                    elements.append(self.parse_expression())
                    if self.match('COMMA'):
                        continue
                    break
                self.expect('RPAREN')
                return {'type': 'tuple_literal', 'elements': elements}
            else:
                self.expect('RPAREN')
                node = first

        else:
            raise SyntaxError(f"Unexpected token {tok} in expression")

        # -----------------------------
        # member‑access / method‑call chaining
        # -----------------------------
        while True:
            # 1) dot access / method:   object.prop   oppure   object.method(args)
            if self.match('DOT'):
                prop = self.expect('ID').value
                # se segue '(', è un metodo
                if self.match('LPAREN'):
                    args = []
                    while self.current().type != 'RPAREN':
                        args.append(self.parse_expression())
                        if not self.match('COMMA'):
                            break
                    self.expect('RPAREN')
                    node = {
                        'type': 'method_call',
                        'object': node,
                        'method': prop,
                        'args': args
                    }
                else:
                    # semplice property access
                    node = {
                        'type': 'prop_access',
                        'object': node,
                        'prop': prop
                    }
                continue

            # 2) colon‑access / colon‑method: object:prop  oppure  object:method(args)
            if self.match('COLON'):
                member = self.expect('ID').value
                if self.match('LPAREN'):
                    args = []
                    while self.current().type != 'RPAREN':
                        args.append(self.parse_expression())
                        if not self.match('COMMA'):
                            break
                    self.expect('RPAREN')
                    node = {
                        'type': 'colon_method_call',
                        'object': node,
                        'method': member,
                        'args': args
                    }
                else:
                    node = {
                        'type': 'colon_prop_access',
                        'object': node,
                        'prop': member
                    }
                continue

            break

        # --- fine della parte di chaining ---

        return node
