# src/chiron_runtime/interpreter.py

import os
import importlib
import sys

class RuntimeError(Exception):
    pass

class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value

class Environment:
    def __init__(self, parent=None):
        self.vars       = {}
        self.funcs      = {}
        self.func_decls = {}
        self.modules    = {}    # moduli caricati con import / from_import
        self.parent     = parent

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

    def has_var(self, name):
        return name in self.vars or (self.parent and self.parent.has_var(name))

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

    def save_func_decl(self, name, decl):
        self.func_decls[name] = decl

    def get_func_decl(self, name):
        if name in self.func_decls:
            return self.func_decls[name]
        elif self.parent:
            return self.parent.get_func_decl(name)
        else:
            raise RuntimeError(f"Dichiarazione della funzione '{name}' non trovata.")

    def has_func(self, name):
        return name in self.funcs

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

        if t == 'import':
            new_modules = []
            for module_fullname in node['modules']:
                if module_fullname.endswith('.chy'):
                    # import di un modulo Chiron, .chy file
                    # spostiamo qui dentro l’import “pesante” per evitare circular import
                    from chiron_runtime.loader import load_chiron_module
                    path = module_fullname  # o calcolalo da un search path
                    mod_env = load_chiron_module(path)
                    alias = os.path.splitext(os.path.basename(path))[0]
                    env.define_module(alias, mod_env)
                    new_modules.append(alias)
                else:
                    # import di modulo Python come prima
                    if module_fullname.startswith("std."):
                        full_py = 'chiron_runtime.stdlib.' + module_fullname
                    else:
                        full_py = module_fullname
                    mod = importlib.import_module(full_py)
                    alias = module_fullname.split('.')[-1]
                    env.define_var(alias, mod)
                    new_modules.append(alias)
            return None

        elif t == 'from_import':
            mod_name = node['module']
            alias_env = None

            # ——————————————————————————————
            # 1) Proviamo a importare un modulo Python/stdlib
            # ——————————————————————————————
            if mod_name.startswith("std.") or mod_name in sys.modules:
                py_mod = (mod_name.startswith("std.")
                          and 'chiron_runtime.stdlib.' + mod_name
                          or mod_name)
                try:
                    alias_env = importlib.import_module(py_mod)
                except ImportError:
                    alias_env = None

            # ——————————————————————————————
            # 2) Se non è un modulo Python, cerchiamo un .chy
            # ——————————————————————————————
            if alias_env is None:
                from chiron_runtime.loader import load_chiron_module
                chy_path = f'chiron_runtime.stdlib.{mod_name}'.replace('.', os.sep) + '.chy'
                if os.path.isfile(chy_path):
                    # load_chiron_module restituisce un Environment
                    alias_env = load_chiron_module(chy_path)

            if alias_env is None:
                raise RuntimeError(f"Cannot import module '{mod_name}'")

            # ——————————————————————————————
            # 3) Esportazione dei nomi richiesti
            # ——————————————————————————————
            for name in node['names']:
                if name == '*':
                    # “import *”: esporta tutto
                    if isinstance(alias_env, type(importlib)):
                        # modulo Python
                        for attr in dir(alias_env):
                            if not attr.startswith('_'):
                                obj = getattr(alias_env, attr)
                                if callable(obj):
                                    env.define_func(attr, obj)
                                else:
                                    env.define_var(attr, obj)
                    else:
                        # Environment Chiron
                        # tutte le variabili
                        for var_name, var_val in alias_env.vars.items():
                            env.define_var(var_name, var_val)
                        # tutte le funzioni
                        for fn_name, fn_val in alias_env.funcs.items():
                            env.define_func(fn_name, fn_val)
                else:
                    # “from X import A, B, …”
                    if isinstance(alias_env, type(importlib)):
                        # modulo Python
                        if not hasattr(alias_env, name):
                            raise RuntimeError(
                                f"Module '{mod_name}' has no member '{name}'"
                            )
                        obj = getattr(alias_env, name)
                        if callable(obj):
                            env.define_func(name, obj)
                        else:
                            env.define_var(name, obj)
                    else:
                        # Environment Chiron
                        if name in alias_env.vars:
                            env.define_var(name, alias_env.vars[name])
                        elif name in alias_env.funcs:
                            env.define_func(name, alias_env.funcs[name])
                        else:
                            raise RuntimeError(
                                f"Module '{mod_name}' has no member '{name}'"
                            )
            return None



        # ----- dichiarazione variabile: "tipo nome = espr;" -----
        elif t == 'declaration':
            print(f"↪︎ [declaration] name='{node['name']}' type={node['var_type']} value node:", node['value'])
            # se non c’è inizializzatore, scegliamo un default in base al tipo
            var_type = node['var_type']  # es. {'type':'simple','name':'int'} o generic
            if node['value'] is None:
                val = self.default_value_for(var_type)
            else:
                val = self.eval_expression(node['value'], env)

            # (eventuale) type checking, se lo fai
            try:
                self.type_check(var_type, val)
            except Exception as e:
                raise RuntimeError(f"Type error in declaration of '{node['name']}': {e}")

            env.define_var(node['name'], val)
            return None

        # ——— assignment ———
        elif t == 'assignment':
            target = node['target']
            val_node = node['value']

            # —— special case: multiply.args = (typed_params) ——
            if target['type'] == 'get_attr' and target['name'] == 'args' \
                    and val_node.get('type') == 'typed_params':
                name = target['object']['name']

                # 1) aggiorno la DECLARATION (firma) sempre
                decl = env.get_func_decl(name)
                decl['params'] = val_node['params']

                # 2) se la closure esiste già, setto i suoi attributi
                closure = env.funcs.get(name)
                if closure is not None:
                    closure.args = val_node['params']
                    closure._param_names = [p['name'] for p in val_node['params']]

                return None

            # —— property assignment generico (fallback) ——
            if target['type'] == 'get_attr':
                obj = self.eval_expression(target['object'], env)
                val = self.eval_expression(val_node, env)
                setattr(obj, target['name'], val)
                return None

            # override di un anonymous_func?
            if target.get('type') == 'identifier' \
                    and val_node \
                    and val_node.get('type') == 'anonymous_func':

                name = target['name']

                # → qui prendo i parametri dalla dichiarazione originaria
                try:
                    decl_node = env.get_func_decl(name)
                    formals = decl_node['params']
                except RuntimeError:
                    formals = []

                print(f"🔧 Overriding function '{name}'")
                print(f"    formals = {formals}")

                def func_override(*args):
                    print(f"▶️  Called override {name} with args={args}")
                    local_env = Environment(env)
                    # bind dei formali
                    for i, p in enumerate(formals):
                        local_env.define_var(p['name'], args[i])
                    print(f"    local_env after binding = {local_env.vars}")

                    # eseguo il body anonimo
                    last = None
                    for stmt in val_node['body']:
                        if stmt['type'] == 'return':
                            return self.eval_expression(stmt['expression'], local_env)
                        elif stmt['type'] == 'expr_stmt':
                            last = self.eval_expression(stmt['expr'], local_env)
                        else:
                            self.exec_statement(stmt, local_env)
                    return last

                func_override.args = formals
                func_override._param_names = [p['name'] for p in formals]
                env.define_func(name, func_override)

                print(f"✅ Function '{name}' overridden\n")
                return None

            # altrimenti assignment normale a variabile…
            value = self.eval_expression(val_node, env)
            varial = target['name']
            if env.has_var(varial):
                env.set_var(varial, value)
            else:
                env.define_var(varial, value)
            return None


        # ——— dichiarazione funzione ———
        elif t == 'declaration_callable':
            # se vogliamo supportare forward-declarations
            if node['body'] is None:
                # registriamo la firma, ma rimandiamo il corpo
                env.save_func_decl(node['name'], node)
                env.define_func(node['name'], None)
                return None

            # altrimenti definiamo subito la closure completa
            def func(*args):
                local_env = Environment(env)
                for i, param in enumerate(formals):
                    local_env.define_var(param['name'], args[i])
                last = None
                for stmt in node['body']:
                    res = self.exec_statement(stmt, local_env)
                    if isinstance(res, ReturnSignal):
                        return res.value
                    if stmt.get('type') == 'expr_stmt':
                        last = self.eval_expression(stmt['expr'], local_env)
                return last

            # Prendi la declaration_callable salvata in env e ne estrai i params
            decl = env.get_func_decl(node['name'])  # qui lanci get_func_decl — non dovrebbe fallire
            formals = decl.get('params', [])  # lista di {'type':..., 'name':...}

            func.args = list(formals)
            func._param_names = [p['name'] for p in formals]
            env.define_func(node['name'], func)
            env.save_func_decl(node['name'], node)
            return None

        # ——— chiamata funzione, return, try, if, while, for, expr_stmt, ecc. ———

        elif t == 'call_callable':
            func = env.get_func(node['name'])
            pos_args = []
            kw_args = {}
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

    def default_value_for(self, var_type):
        """
        Ritorna un valore “zero” per ogni tipo:
        - int   → 0
        - float → 0.0
        - bool  → False
        - str   → ""
        - array<T> → []
        - tuple<T1,…> → ()
        - map<K,V> → {}
        - auto → None
        """
        kind = var_type['type']
        name = var_type['name']
        if kind == 'simple':
            if name == 'int':   return 0
            if name == 'float': return 0.0
            if name == 'bool':  return False
            if name == 'str':   return ""
            if name == 'char':  return '\0'
            # auto: non sappiamo → None
            return None
        else:  # generic
            if name == 'array': return []
            if name == 'tuple': return ()
            if name == 'map':   return {}
            # altri generic → None
            return None


    def type_check(self, expected, value):
        """
        expected: {'type':'simple'|'generic', 'name':str, 'params':[...] }
        value: Python object from eval_expression
        """
        # tipi semplici: do nothing
        if expected['type'] == 'simple':
         return

        # generici
        name = expected['name']
        params = expected.get('params', [])
        if name == 'array':
         if not isinstance(value, list):
             raise RuntimeError(f"expected array, got {type(value).__name__}")
        # array<T> deve avere esattamente un parametro
        elem_type = params[0]
        for i, el in enumerate(value):
            try:
                self.type_check(elem_type, el)
            except RuntimeError as e:
                raise RuntimeError(f"array element at index {i}: {e}")
        return

        if name == 'tuple':
         if not isinstance(value, tuple):
             raise RuntimeError(f"expected tuple, got {type(value).__name__}")
        if len(params) != len(value):
            raise RuntimeError(f"tuple length mismatch: expected {len(params)}, got {len(value)}")
        for i,(subt, el) in enumerate(zip(params, value)):
            try:
                self.type_check(subt, el)
            except RuntimeError as e:
                raise RuntimeError(f"tuple element {i}: {e}")
        return

        if name == 'map':
         if not isinstance(value, dict):
             raise RuntimeError(f"expected map, got {type(value).__name__}")
        key_t, val_t = params
        for k,v in value.items():
            try:
                self.type_check(key_t, k)
            except RuntimeError as e:
                raise RuntimeError(f"map key {k!r}: {e}")
            try:
                self.type_check(val_t, v)
            except RuntimeError as e:
                raise RuntimeError(f"map value for key {k!r}: {e}")
        return

        # altri tipi generici (se ne aggiungeranno)…
        return



    # -----------------------------------------------------------------------
    # EVALUATOR DI EXPRESSION-NODE (compresi i nuovi array/tuple/map)
    # -----------------------------------------------------------------------
    def eval_expression(self, node, env):
        print("↪︎ eval_expression got:", node)

        t = node['type']

        print(t, t == 'assignment')

        if t == 'literal':
            print("↪︎   literal →", node['value'])
            return node['value']

        elif t == 'identifier':
            name = node['name']

            if env.has_func(name):
                print(f"↪︎   identifier '{node['name']}' →", env.get_func(name))
                return env.get_func(name)

            print(f"↪︎   identifier '{node['name']}' →", env.get_var(name))

            return env.get_var(name)

        elif t == 'binary_op':
            print(f"↪︎   binary_op {node['op']}")
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
            print("↪︎   call_callable:", node)
            func = env.get_func(node['name'])
            print("↪︎     resolved func:", func)
            if not callable(func):
                raise RuntimeError(f"'{node['name']}' non è una funzione.")
            pos_args = []
            kw_args  = {}
            for arg in node['args']:
                if arg.get('type') == 'kwarg':
                    kw_args[arg['key']] = self.eval_expression(arg['value'], env)
                else:
                    pos_args.append(self.eval_expression(arg, env))
            print(f"→ Calling {node['name']} with pos={pos_args} kw={kw_args}")
            result = func(*pos_args, **kw_args)
            print(f"→ {node['name']} returned", result)
            return func(*pos_args, **kw_args)

        # —— funzione anonima (blocchi {…}) ——
        elif t == 'anonymous_func':
            # costruiamo una chiusura uguale a come facciamo per le dichiarate
            body = node['body']
            def anon(*args):
                # chiudiamo sull'env corrente
                local_env = Environment(env)
                last = None
                for stmt in body:
                    # gestiamo return espliciti
                    try:
                        res = self.exec_statement(stmt, local_env)
                        if isinstance(res, ReturnSignal):
                            return res.value
                    except ReturnSignal as rs:
                        return rs.value
                    # expr_stmt → salviamo il valore
                    if stmt.get('type') == 'expr_stmt':
                        last = self.eval_expression(stmt['expr'], local_env)
                return last
            return anon

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

        elif t == 'get_attr':
            # recupera l'oggetto
            obj = self.eval_expression(node['object'], env)
            try:
                return getattr(obj, node['name'])
            except AttributeError:
                raise RuntimeError(f"Oggetto di tipo {type(obj)} non ha attributo '{node['name']}'")

        elif t == 'call_method':
            # valuta l'oggetto e recupera il bound‐method
            obj = self.eval_expression(node['object'], env)
            meth = getattr(obj, node['method'], None)
            if not callable(meth):
                raise RuntimeError(f"'{node['method']}' non è un metodo di {obj}")
            # valuta args posizionali
            args = [self.eval_expression(a, env) for a in node['args']]
            return meth(*args)

        elif t == 'prop_access':
            obj = self.eval_expression(node['object'], env)
            return getattr(obj, node['prop'])

        elif t in ('method_call', 'colon_method_call'):
            obj = self.eval_expression(node['object'], env)
            method = getattr(obj, node['method'])
            args = [self.eval_expression(a, env) for a in node['args']]
            return method(*args)

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