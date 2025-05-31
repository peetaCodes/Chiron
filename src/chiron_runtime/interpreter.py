# src/chiron_runtime/interpreter.py

import os
import importlib

class RuntimeError(Exception):
    pass

class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value

class Environment:
    def __init__(self, parent=None):
        self.vars    = {}
        self.funcs   = {}
        self.modules = {}    # moduli caricati con import / from_import
        self.parent  = parent

    # ----- gestione variabili -----
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

    # ----- gestione funzioni -----
    def define_func(self, name, closure):
        self.funcs[name] = closure

    def get_func(self, name):
        if name in self.funcs:
            return self.funcs[name]
        elif self.parent:
            return self.parent.get_func(name)
        else:
            raise RuntimeError(f"Function '{name}' not defined")

    # ----- gestione moduli (import) -----
    def define_module(self, name, env):
        self.modules[name] = env

    def get_module(self, name):
        if name in self.modules:
            return self.modules[name]
        elif self.parent:
            return self.parent.get_module(name)
        else:
            raise RuntimeError(f"Module '{name}' not imported")


class Interpreter:
    def __init__(self):
        self.global_env = Environment()
        self.setup_stdlib()

    def setup_stdlib(self):
        # Per esempio, se si vuole registrare subito print() e input() dalla stdlib scritta in Python:
        try:
            stdio = importlib.import_module('chiron_runtime.stdlib.std.io.io')
            # in stdio.py abbiamo definito:
            #   def print_(*args): …
            #   def input_(prompt): …
            self.global_env.define_func('print', getattr(stdio, 'print_'))
            self.global_env.define_func('input', getattr(stdio, 'input_'))
        except ImportError:
            # se non esistono, proseguiamo senza stdlib
            pass

    def interpret(self, ast):
        # 1) Primo passaggio: registrare tutte le dichiarazioni di funzione
        entry_point = None
        for stmt in ast:
            if stmt['type'] == 'declaration_callable':
                self.exec_statement(stmt, self.global_env)
                if stmt['name'] == 'main':
                    entry_point = stmt

        # 2) Se non c'è main(), eseguo solo il codice globale
        if not entry_point:
            for stmt in ast:
                if stmt['type'] != 'declaration_callable':
                    self.exec_statement(stmt, self.global_env)
        else:
            # altrimenti eseguo main()
            func = self.global_env.get_func('main')
            func()

        # alla fine, per debug, stampo l’ambiente globale
        self.dump_env()

    def safe_execute(self, node, env):
        try:
            return self.exec_statement(node, env)
        except Exception as e:
            line = node.get('line', '?')
            col  = node.get('col', '?')
            raise RuntimeError(f"ChironError at line {line}, col {col}: {e}")

    def exec_statement(self, node, env):
        t = node['type']

        # ----- import di interi moduli: "import X, Y;" -----
        if t == 'import':
            for module_fullname in node['modules']:
                # modulo può essere "std.io" → lo cerchiamo in chiron_runtime.stdlib
                if module_fullname.startswith("std."):
                    full_py_mod = 'chiron_runtime.stdlib.' + module_fullname
                else:
                    full_py_mod = module_fullname
                try:
                    module = importlib.import_module(full_py_mod)
                except ImportError as e:
                    raise RuntimeError(f"Cannot import module '{module_fullname}': {e}")
                # registro l'intero modulo come variabile
                alias = module_fullname.split('.')[-1]
                env.define_var(alias, module)
            return None

        # ----- from-import: "from X import A, B, *;" -----
        elif t == 'from_import':
            mod_name = node['module']
            if mod_name.startswith("std."):
                full_py_mod = 'chiron_runtime.stdlib.' + mod_name
            else:
                full_py_mod = mod_name
            try:
                module = importlib.import_module(full_py_mod)
            except ImportError as e:
                raise RuntimeError(f"Cannot import module '{mod_name}': {e}")

            for item in node['names']:
                if item == '*':
                    # import all
                    for attr in dir(module):
                        if not attr.startswith("_"):
                            obj = getattr(module, attr)
                            if callable(obj):
                                env.define_func(attr, obj)
                            else:
                                env.define_var(attr, obj)
                else:
                    name = item
                    alias = item
                    obj = getattr(module, name)
                    if callable(obj):
                        env.define_func(alias, obj)
                    else:
                        env.define_var(alias, obj)
            return None

        # ----- dichiarazione variabile: "tipo nome = espr;" -----
        elif t == 'declaration':
            # node['var_type'] contiene il tipo (svuotato dallo schema, non lo usiamo al runtime dinamico)
            val = self.eval_expression(node['value'], env)
            env.define_var(node['name'], val)
            return None

        # ----- dichiarazione funzione: "callable f(params) -> type { body };" -----
        elif t == 'declaration_callable':
            def func(*args):
                local_env = Environment(env)
                # bind parametri
                for i, param in enumerate(node['params']):
                    local_env.define_var(param['name'], args[i])
                try:
                    for stmt in node.get('body', []):
                        result = self.exec_statement(stmt, local_env)
                        if isinstance(result, ReturnSignal):
                            return result.value
                except ReturnSignal as rs:
                    return rs.value
                return None

            env.define_func(node['name'], func)
            return None

        # ----- chiamata funzione: "f(arg1, arg2, key=val, ...)" -----
        elif t == 'call_callable':
            func = env.get_func(node['name'])
            pos_args = []
            kw_args  = {}
            for arg in node['args']:
                if arg.get('type') == 'kwarg':
                    kw_args[arg['key']] = self.eval_expression(arg['value'], env)
                else:
                    pos_args.append(self.eval_expression(arg, env))
            return func(*pos_args, **kw_args)

        # ----- return -----
        elif t == 'return':
            val = self.eval_expression(node['expression'], env)
            raise ReturnSignal(val)

        # ----- try/except/finally -----
        elif t == 'try':
            try:
                for stmt in node['body']:
                    self.exec_statement(stmt, env)
            except Exception as e:
                handled = False
                for handler in node.get('handlers', []):
                    if handler['exception'] in (type(e).__name__, 'Exception'):
                        local_env = Environment(env)
                        local_env.define_var(handler['var'], str(e))
                        for stmt in handler['body']:
                            self.exec_statement(stmt, local_env)
                        handled = True
                        break
                if not handled:
                    raise e
            finally:
                for stmt in node.get('finally', []):
                    self.exec_statement(stmt, env)
            return None

        # ----- if -----
        elif t == 'if':
            cond = self.eval_expression(node['condition'], env)
            if cond:
                for stmt in node['body']:
                    self.safe_execute(stmt, env)
            elif node.get('else'):
                for stmt in node['else']:
                    self.safe_execute(stmt, env)
            return None

        # ----- while -----
        elif t == 'while':
            while self.eval_expression(node['condition'], env):
                for stmt in node['body']:
                    self.safe_execute(stmt, env)
            return None

        # ----- for -----
        elif t == 'for':
            # init può essere dichiarazione di variabile o espressione
            self.exec_statement(node['init'], env)
            while self.eval_expression(node['condition'], env):
                for stmt in node['body']:
                    self.safe_execute(stmt, env)
                # update è un’espressione standalone
                self.eval_expression(node['update'], env)
            return None

        # ----- espressione-standalone -----
        elif t == 'expr_stmt':
            self.eval_expression(node['expr'], env)
            return None

        else:
            raise RuntimeError(f"Unknown statement type: {t}")


    # -----------------------------------------------------------------------
    # EVALUATOR DI EXPRESSION-NODE (compresi i nuovi array/tuple/map)
    # -----------------------------------------------------------------------
    def eval_expression(self, node, env):
        t = node['type']

        if t == 'literal':
            return node['value']

        elif t == 'identifier':
            return env.get_var(node['name'])

        elif t == 'binary_op':
            left  = self.eval_expression(node['left'], env)
            right = self.eval_expression(node['right'], env)
            op = node['op']
            if op == '+':   return left + right
            if op == '-':   return left - right
            if op == '*':   return left * right
            if op == '/':   return left / right
            if op == '%':   return left % right
            if op == '<':   return left < right
            if op == '>':   return left > right
            if op == '<=':  return left <= right
            if op == '>=':  return left >= right
            if op == '==':  return left == right
            if op == '!=':  return left != right
            raise RuntimeError(f"Unknown binary operator '{op}'")

        elif t == 'logic':
            left  = self.eval_expression(node['left'], env)
            right = self.eval_expression(node['right'], env)
            if node['op'] == 'and':
                return bool(left) and bool(right)
            elif node['op'] == 'or':
                return bool(left) or bool(right)
            else:
                raise RuntimeError(f"Unknown logical operator '{node['op']}'")

        elif t == 'unary_op':
            expr = node['expr']
            name = expr.get('name')
            if node['op'] == '++_pre':
                v = env.get_var(name) + 1
                env.set_var(name, v)
                return v
            if node['op'] == '--_pre':
                v = env.get_var(name) - 1
                env.set_var(name, v)
                return v
            if node['op'] == '++_post':
                old = env.get_var(name)
                env.set_var(name, old + 1)
                return old
            if node['op'] == '--_post':
                old = env.get_var(name)
                env.set_var(name, old - 1)
                return old
            raise RuntimeError(f"Unknown unary op '{node['op']}'")

        elif t == 'call_callable':
            func = env.get_func(node['name'])
            pos_args = []
            kw_args  = {}
            for arg in node['args']:
                if arg.get('type') == 'kwarg':
                    kw_args[arg['key']] = self.eval_expression(arg['value'], env)
                else:
                    pos_args.append(self.eval_expression(arg, env))
            return func(*pos_args, **kw_args)

        elif t == 'array_literal':
            return [ self.eval_expression(elem, env) for elem in node['elements'] ]

        elif t == 'tuple_literal':
            return tuple(self.eval_expression(elem, env) for elem in node['elements'])

        elif t == 'map_literal':
            d = {}
            for (key_node, val_node) in node['entries']:
                key = self.eval_expression(key_node, env)
                val = self.eval_expression(val_node, env)
                d[key] = val
            return d

        else:
            raise RuntimeError(f"Unknown expression type '{t}'")


    # -----------------------------------------------------------------------
    # PER DEBUG: stampa l’ambiente globale dopo l’esecuzione
    # -----------------------------------------------------------------------
    def dump_env(self):
        print("\n=== Ambiente finale ===")
        for name, val in self.global_env.vars.items():
            print(f"{name} = {val}")
        for name in self.global_env.funcs:
            print(f"Function: {name}()")