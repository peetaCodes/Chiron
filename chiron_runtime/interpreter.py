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

    def interpret(self, ast):
        # Prima passata: dichiarazioni
        for stmt in ast:
            if stmt['type'] == 'declaration_callable':
                self.exec_statement(stmt, self.global_env)
            elif stmt['type'] == 'declaration':
                self.exec_statement(stmt, self.global_env)

        # Cerca l'entry point
        try:
            main_func = self.global_env.get_func('main')
            main_func()
        except RuntimeError:
            # Nessuna main: esegui il codice globale (escludendo dichiarazioni callable)
            for stmt in ast:
                if stmt['type'] not in ('declaration', 'declaration_callable'):
                    self.exec_statement(stmt, self.global_env)

    def exec_statement(self, node, env):
        t = node['type']

        if t == 'declaration':
            # auto/primitive var declarations
            val = self.eval_expression(node['value'], env)
            env.define_var(node['name'], val)

        elif t == 'declaration_callable':
            # Creo la chiusura funzione
            def closure(*args):
                # nuovo ambiente locale che chiude su env (definizione)
                local_env = Environment(env)
                # assegno parametri
                for i, param in enumerate(node['params']):
                    local_env.define_var(param['name'], args[i])
                # eseguo il corpo fino al return
                return self.exec_block(node['body'], local_env)
            env.define_func(node['name'], closure)

        elif t == 'return':
            # non dovrebbe capitare qui se parse_statement li estrae
            return self.eval_expression(node['expression'], env)

        elif t == 'call_callable':
            # chiamata funzione come statement a sé stante
            func = env.get_func(node['name'])
            args = [self.eval_expression(arg, env) for arg in node['args']]
            return func(*args)

        else:
            raise RuntimeError(f"Unknown statement type: {t}")

    def exec_block(self, stmts, env):
        # esegue una sequenza di statement dentro una funzione
        for stmt in stmts:
            if stmt['type'] == 'return':
                # gestisco il return qui
                return self.eval_expression(stmt['expression'], env)
            res = self.exec_statement(stmt, env)
            # se la chiamata a statement ha restituito qualcosa (callable in tail)
            if stmt['type'] == 'call_callable':
                return res
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