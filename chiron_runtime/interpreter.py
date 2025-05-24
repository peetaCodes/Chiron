# interpreter.py

class RuntimeError(Exception):
    pass

class Environment:
    def __init__(self, parent=None):
        self.vars = {}
        self.funcs = {}
        self.parent = parent

    def define_var(self, name, value):
        self.vars[name] = value

    def get_var(self, name):
        if name in self.vars:
            return self.vars[name]
        elif self.parent:
            return self.parent.get_var(name)
        else:
            raise RuntimeError(f"Variable '{name}' not defined")

    def set_var(self, name, value):
        if name in self.vars:
            self.vars[name] = value
        elif self.parent:
            self.parent.set_var(name, value)
        else:
            raise RuntimeError(f"Variable '{name}' not defined")

    def define_func(self, name, closure):
        self.funcs[name] = closure

    def get_func(self, name):
        if name in self.funcs:
            return self.funcs[name]
        elif self.parent:
            return self.parent.get_func(name)
        else:
            raise RuntimeError(f"Function '{name}' not defined")

class Interpreter:
    def __init__(self):
        self.global_env = Environment()
        self.setup_stdlib()

    def setup_stdlib(self):
        self.global_env.define_func('print', lambda *args: print(*args))

    def interpret(self, ast):
        entry_point = None

        # Primo passaggio: registra tutte le dichiarazioni di funzione
        for stmt in ast:
            if stmt['type'] == 'declaration_callable':
                self.exec_statement(stmt, self.global_env)
                if stmt['name'] == 'main':
                    entry_point = stmt

        # Secondo passaggio: esegui solo il codice globale se non c'è main
        if not entry_point:
            for stmt in ast:
                if stmt['type'] != 'declaration_callable':
                    self.exec_statement(stmt, self.global_env)
        else:
            func = self.global_env.get_func('main')
            func()

        self.dump_env()

    def exec_statement(self, node, env):
        t = node['type']

        if t == 'declaration':
            val = self.eval_expression(node['value'], env)
            env.define_var(node['name'], val)

        elif t == 'declaration_callable':
            def func(*args):
                local_env = Environment(env)
                for i, param in enumerate(node['params']):
                    local_env.define_var(param['name'], args[i])
                try:
                    for stmt in node.get('body', []):
                        result = self.exec_statement(stmt, local_env)
                        if isinstance(result, ReturnSignal):
                            return result.value
                except ReturnSignal as rs:
                    return rs.value

            env.define_func(node['name'], func)

        elif t == 'call_callable':
            func = env.get_func(node['name'])
            args = [self.eval_expression(arg, env) for arg in node['args']]
            return func(*args)

        elif t == 'return':
            value = self.eval_expression(node['expression'], env)
            raise ReturnSignal(value)

        elif t == 'try':
            try:
                for stmt in node['body']:
                    self.exec_statement(stmt, env)
            except Exception as e:
                handled = False
                for handler in node.get('handlers', []):
                    if handler['exception'] in (type(e).__name__, 'Exception'):
                        local_env = Environment(env)
                        local_env.define_var(handler['var'], str(e))  # o l'oggetto eccezione stesso
                        for stmt in handler['body']:
                            self.exec_statement(stmt, local_env)
                        handled = True
                        break
                if not handled:
                    raise e
            finally:
                for stmt in node.get('finally', []):
                    self.exec_statement(stmt, env)


        else:
            raise RuntimeError(f"Unknown statement type: {t}")

    def exec_block(self, stmts, env):
        """
        Esegue la lista di statement nel blocco di una funzione.
        Il solo 'return' interrompe l’esecuzione restituendo un valore.
        Le chiamate a funzione vengono eseguite (side-effect ed eventuale return),
        ma non interrompono il flusso a meno che non siano un return esplicito.
        """
        for stmt in stmts:
            if stmt['type'] == 'return':
                # ritorno esplicito: restituisco subito l'espressione
                return self.eval_expression(stmt['expression'], env)
            # altrimenti eseguo lo statement:
            self.exec_statement(stmt, env)
            # fine del blocco senza return
        return None

    def eval_expression(self, node, env):
        t = node['type']

        if t == 'literal':
            return node['value']

        if t == 'identifier':
            return env.get_var(node['name'])

        if t == 'binary_op':
            l = self.eval_expression(node['left'], env)
            r = self.eval_expression(node['right'], env)
            op = node['op']
            if op == '+': return l + r
            if op == '-': return l - r
            if op == '*': return l * r
            if op == '/': return l / r
            if op == '%': return l % r
            raise RuntimeError(f"Unknown operator {op}")

        if t == 'unary_op':
            # ++_pre, --_pre, ++_post, --_post come dal parser
            expr = node['expr']
            if node['op'] == '++_pre':
                name = expr['name']
                v = env.get_var(name) + 1
                env.set_var(name, v)
                return v
            if node['op'] == '--_pre':
                name = expr['name']
                v = env.get_var(name) - 1
                env.set_var(name, v)
                return v
            if node['op'] == '++_post':
                name = expr['name']
                old = env.get_var(name)
                env.set_var(name, old+1)
                return old
            if node['op'] == '--_post':
                name = expr['name']
                old = env.get_var(name)
                env.set_var(name, old-1)
                return old
            raise RuntimeError(f"Unknown unary op {node['op']}")

        if t == 'call_callable':
            # chiamata in espressione
            func = env.get_func(node['name'])
            args = [self.eval_expression(arg, env) for arg in node['args']]
            return func(*args)

        raise RuntimeError(f"Unknown expression type {t}")

    def dump_env(self):
        print("\n=== Ambiente finale ===")
        for name, val in self.global_env.vars.items():
            print(f"{name} = {val}")
        for name in self.global_env.funcs:
            print(f"Function: {name}()")

class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value
