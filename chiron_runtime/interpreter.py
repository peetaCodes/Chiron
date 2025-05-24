import os
from chiron_runtime.lexer import Lexer
from chiron_runtime.parser import Parser

import importlib

#TODO: fix the 'maximum recoursion depth exceeded'

class RuntimeError(Exception):
    pass

class Environment:
    def __init__(self, parent=None):
        self.vars    = {}
        self.funcs   = {}
        self.modules = {}      # <— moduli importati
        self.parent  = parent

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

    def define_module(self, name, env):
        self.modules[name] = env

    def get_module(self, name):
        if name in self.modules:
            return self.modules[name]
        elif self.parent:
            return self.parent.get_module(name)
        else:
            raise RuntimeError(f"Module '{name}' not imported")

class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value

class Interpreter:
    def __init__(self):
        self.global_env = Environment()
        self.setup_stdlib()

    def setup_stdlib(self):
        dev_mode = False  # cambia in False in produzione

        if dev_mode:
            try:
                stdio = importlib.import_module('chiron_runtime.stdlib.std.io.io')
                self.global_env.define_func('print', getattr(stdio, 'print_'))
                self.global_env.define_func('input', getattr(stdio, 'input_'))
            except ImportError:
                pass

    def interpret(self, ast):
        entry = None

        # 1. Prima esegue tutti gli import
        for stmt in ast:
            if stmt['type'] in ('import', 'from_import'):
                self.exec_statement(stmt, self.global_env)

        # 2. Poi registra tutte le funzioni
        for stmt in ast:
            if stmt['type'] == 'declaration_callable':
                self.exec_statement(stmt, self.global_env)
                if stmt['name'] == 'main':
                    entry = stmt

        # 3. Infine, o esegue main() o il codice globale
        if entry:
            self.global_env.get_func('main')()
        else:
            for stmt in ast:
                if stmt['type'] not in ('declaration_callable', 'import', 'from_import'):
                    self.exec_statement(stmt, self.global_env)

        self.dump_env()

    def safe_execute(self, node, env):
        try:
            return self.exec_statement(node, env)
        except Exception as e:
            line = node.get('line', '?')
            col = node.get('col', '?')
            raise RuntimeError(f"ChironError at line {line}, col {col}: {e}")

    def exec_statement(self, node, env):
        t = node['type']

        if t == 'import':
            mod_name = node['module']
            alias = node.get('alias') or mod_name.split('.')[-1]

            try:
                # Prima prova come libreria Chiron
                full_chiron_mod = 'chiron_runtime.stdlib.' + mod_name.replace('.', '.')
                module = importlib.import_module(full_chiron_mod)
            except ImportError:
                try:
                    # Altrimenti è un modulo PyPI
                    module = importlib.import_module(mod_name)
                except ImportError as e:
                    raise RuntimeError(f"Cannot import module '{mod_name}': {e}")

            env.define_var(alias, module)
            return None

        elif t == 'from_import':
            mod_name = node['module']
            try:
                # Prima prova come stdlib Chiron
                full_chiron_mod = 'chiron_runtime.stdlib.' + mod_name.replace('.', '.')
                module = importlib.import_module(full_chiron_mod)
            except ImportError:
                try:
                    # Altrimenti modulo PyPI
                    module = importlib.import_module(mod_name)
                except ImportError as e:
                    raise RuntimeError(f"Cannot import module '{mod_name}': {e}")

            for name, alias in node['names']:
                obj = getattr(module, name)
                if callable(obj):
                    env.define_func(alias or name, obj)
                else:
                    env.define_var(alias or name, obj)
            return None

        elif t == 'declaration':
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

        elif t == 'if':
            condition = self.eval_expression(node['condition'], env)
            if condition:
                for stmt in node['body']:
                    self.safe_execute(stmt, env)
            elif node['else']:
                for stmt in node['else']:
                    self.safe_execute(stmt, env)

        elif t == 'while':
            while self.eval_expression(node['condition'], env):
                for stmt in node['body']:
                    self.safe_execute(stmt, env)

        elif t == 'for':
            self.exec_statement(node['init'], env)
            while self.eval_expression(node['condition'], env):
                for stmt in node['body']:
                    self.safe_execute(stmt, env)
                # l'aggiornamento può essere un'espressione standalone
                self.exec_statement({'type': 'expr_stmt', 'expr': node['update']}, env)

        elif t == 'expr_stmt':
            # espressione standalone terminata da ';'
            self.eval_expression(node['expr'], env)
            return None

        else:
            raise RuntimeError(f"Unknown statement type: {t}")

    def eval_expression(self, node, env):
        t = node['type']

        if t == 'literal':
            return node['value']

        elif t == 'identifier':
            return env.get_var(node['name'])

        elif t == 'binary_op':
            left = self.eval_expression(node['left'], env)
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
            raise RuntimeError(f"Unknown binary operator {op}")

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
            raise RuntimeError(f"Unknown unary op {node['op']}")

        elif t == 'call_callable':
            func = env.get_func(node['name'])
            args = [self.eval_expression(arg, env) for arg in node['args']]
            return func(*args)

        else:
            raise RuntimeError(f"Unknown expression type {t}")

    def handle_import(self, node, env):
        modname = node['module']
        alias   = node['alias']
        # cerchiamo foo.chy in std/ o nella cwd
        path = f"std/{modname}.chy"
        if not os.path.exists(path):
            path = f"{modname}.chy"
        with open(path) as f:
            code = f.read()
        # lex + parse + interpret in un env separato
        mod_env = Environment()
        mod_ast = Parser(Lexer(code).tokenize()).parse()
        Interpreter()._interpret_in_env(mod_ast, mod_env)
        env.define_module(alias, mod_env)

    def handle_from_import(self, node, env):
        mod = env.get_module(node['module'])
        for name in node['names']:
            if name == '*':
                # importa tutto: variabili + funzioni
                for v, val in mod.vars.items():
                    env.define_var(v, val)
                for f, fn in mod.funcs.items():
                    env.define_func(f, fn)
            else:
                # importa solo name
                if name in mod.vars:
                    env.define_var(name, mod.vars[name])
                elif name in mod.funcs:
                    env.define_func(name, mod.funcs[name])
                else:
                    raise RuntimeError(f"No symbol '{name}' in module '{node['module']}'")

    def _interpret_in_env(self, ast, env):
        # versione interna di interpret che usa l'env fornito
        for stmt in ast:
            if stmt['type']=='declaration_callable':
                self.exec_statement(stmt, env)
        for stmt in ast:
            if stmt['type']!='declaration_callable':
                self.exec_statement(stmt, env)

    def dump_env(self):
        print("\n=== Ambiente finale ===")
        for name, val in self.global_env.vars.items():
            print(f"{name} = {val}")
        for name in self.global_env.funcs:
            print(f"Function: {name}()")