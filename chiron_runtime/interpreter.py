class RuntimeError(Exception): pass

class Interpreter:
    def __init__(self):
        # symbol_table: nome -> {'value': ..., 'modifiers': [...]}
        self.symbol_table = {
            'variables': {},
            'functions': {}
        }

    def interpret(self, ast):
        for stmt in ast:
            self.execute(stmt)
        self.dump_env()

    def execute(self, stmt):
        # Dichiariazione: stmt['type']=='declaration'
        if stmt['type'] == 'declaration':
            name = stmt['name']
            modifiers = stmt.get('modifiers', [])
            # Calcola il valore (può essere literal, variable, op, etc)
            val = self.evaluate(stmt['value'])
            # Inserisci in symbol table
            self.symbol_table[name] = {
                'value': val,
                'modifiers': modifiers
            }
            print(f"Declared {name} = {val}  ({', '.join(modifiers)})")
        else:
            # espressione standalone
            return self.evaluate(stmt)

    def evaluate(self, node):
        ntype = node['type']

        if ntype == 'declaration':
            # gestione dichiarazione variabile
            name = node['name']
            value = self.evaluate(node['value'])  # valuto l'espressione assegnata
            self.symbol_table['variables'][name] = value
            return value

        elif ntype == 'declaration_callable':
            # gestione dichiarazione funzione senza corpo per ora
            name = node['name']
            params = node['params']
            return_type = node['return_type']
            modifiers = node['modifiers']

            # Salvo solo le informazioni di firma nel dizionario funzioni
            self.symbol_table['functions'][name] = {
                'params': params,
                'return_type': return_type,
                'modifiers': modifiers,
                # per ora il corpo è assente o None
                'body': None
            }

            return None  # dichiarazione di funzione non restituisce valore

        elif ntype == 'binary_op':
            # esempio gestione operazioni binarie
            left = self.evaluate(node['left'])
            right = self.evaluate(node['right'])
            op = node['operator']

            if op == '+':
                return left + right
            elif op == '-':
                return left - right
            elif op == '*':
                return left * right
            elif op == '/':
                return left / right
            elif op == '%':
                return left % right
            else:
                raise RuntimeError(f"Unknown operator: {op}")

        elif ntype == 'number':
            # nodo numero
            return node['value']

        elif ntype == 'identifier':
            # nodo identificatore: cerco variabile
            name = node['value']
            if name in self.symbol_table['variables']:
                return self.symbol_table['variables'][name]
            else:
                raise RuntimeError(f"Undefined variable: {name}")

        else:
            raise RuntimeError(f"Unknown node type: {ntype}")

    def dump_env(self):
        for name, entry in self.symbol_table.items():
            print(f"{name} : {entry}")