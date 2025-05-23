class Parser:
    def __init__(self, code):
        self.lexer = Lexer(code)
        self.tokens = self.lexer.tokenize()
        self.pos = 0

    def current_token(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def advance(self):
        self.pos += 1

    def expect(self, token_type):
        token = self.current_token()
        if token is None:
            raise SyntaxError(f"Atteso {token_type} ma trovato fine input")
        if token.type != token_type:
            raise SyntaxError(f"Atteso {token_type} ma trovato {token.type} ({token.value})")
        self.advance()
        return token

    def parse(self):
        statements = []
        while self.current_token() is not None:
            stmt = self.parse_statement()
            statements.append(stmt)
        return statements

    def parse_statement(self):
        token = self.current_token()

        # Riconosce dichiarazione/assegnazione con tipo o auto
        if token.type in ('AUTO', 'ID', 'INT_TYPE', 'FLOAT_TYPE', 'BOOL_TYPE', 'CHAR_TYPE', 'STR_TYPE'):
            return self.parse_var_declaration_or_assignment()

        # Altri statement ...

        raise SyntaxError(f"Comando non riconosciuto: {token.type} ({token.value})")

    def parse_var_declaration_or_assignment(self):
        # Può essere:
        # auto var [:= | = | : =] expr
        # int var [:= | = | : =] expr
        # ...

        # Leggi tipo o auto
        type_token = self.current_token()
        self.advance()

        # Leggi nome variabile
        var_token = self.expect('ID')

        # Leggi operatore di assegnazione (opzionale ':', '=') con spazi
        assign_token = self.current_token()
        if assign_token and assign_token.type in ('EQUAL', 'COLON'):
            self.advance()

            # Supporta ':=' o ': =' o '='
            if assign_token.type == 'COLON':
                # Se dopo ':' c'è '=' o spazio + '=', avanzare
                next_token = self.current_token()
                if next_token and next_token.type == 'EQUAL':
                    self.advance()
                elif next_token and next_token.type == 'SKIP':
                    # opzionale, ma nel lexer i 'SKIP' non sono token, quindi probabilmente no
                    pass

        else:
            raise SyntaxError("Assegnazione mancante (:=, =, : =)")

        # Ora aspettiamo un'espressione (per semplicità, qui solo un valore)
        expr_token = self.current_token()
        if expr_token is None:
            raise SyntaxError("Espressione mancante dopo assegnazione")
        self.advance()

        return ('var_decl', type_token.value, var_token.value, expr_token.value)
