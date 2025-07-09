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
    def __init__(self, stdlib_file:bool = False,devMode:bool = False):
        self.global_env = Environment()

        self.devMode = devMode
        self.cwd = os.getcwd()
        self.stdlib_dir = 'chiron_runtime/stdlib'
        self.abs_stdlib_dir = f'{self.cwd}{os.sep}{self.stdlib_dir}/std'
        if not stdlib_file: self.setup_stdlib()

    def debug(self, *args, **kwargs):
        if self.devMode:
            print("[INTERPRETER DEBUG]", *args, **kwargs)

    def setup_stdlib(self):

        from chiron_runtime.loader import load_chiron_module
        builtins_path = os.path.join(self.stdlib_dir, "std/common.chy")
        try:
            # load_chiron_module torna un Environment
            mod_env = load_chiron_module(builtins_path)
        except ImportError:
            return

        # “Inietta” tutto dal modulo common.chy nel global_env corrente:
        for name, val in mod_env.vars.items():
            self.global_env.define_var(name, val)
        for name, fn in mod_env.funcs.items():
            self.global_env.define_func(name, fn)

    def resolve_chiron_module(self, path_segments:list):
        """
        Risolve la lista di segmenti di modulo Chiron ['std','math'] -> percorso file .chy
        Cerca prima nella cwd, poi in self.stdlib_dir.
        """
        # Costruisci nome file relativo
        rel_path = os.path.join(*path_segments) + '.chy'
        # Prova prima in working dir
        self.debug("path_segments, rel_path, cwd: ",path_segments, rel_path, self.cwd)
        for base in [self.cwd, self.abs_stdlib_dir]:
            full = os.path.normpath(os.path.join(base, rel_path))
            self.debug(f"[RESOLVING CHIRON MODULE] FULL: {full}")
            if os.path.isfile(full):
                return full
        raise RuntimeError(f"Modulo Chiron non trovato: {'.'.join(path_segments)} (cercato in {self.cwd} e {self.cwd + self.abs_stdlib_dir})")

    def resolve_stdlib_module(self, path_segments:list):
        self.debug(f"TRYING TO RESOLVE STDLIB MODULE "+str(path_segments))
        for f in os.listdir(self.abs_stdlib_dir):
            self.debug(f"[RESOLVING STDLIB MODULE] F: {f}")
            module_data = f.split('.')

            if len(module_data) < 0: continue # it's just a folder

            if module_data[0] == path_segments[1]:
                return self.stdlib_dir + '/' + "/".join(path_segments[0:2]) + '.' + module_data[1], self.abs_stdlib_dir + '/' + path_segments[1] + '.' + module_data[1]
        raise RuntimeError(f"Modulo della stdlib non trovato: {".".join(path_segments)}")

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
        if self.devMode:self.dump_env()

    def safe_execute(self, node, env):
        try:
            return self.exec_statement(node, env)
        except Exception as e:
            line = node.get('line', '?')
            col  = node.get('col', '?')
            raise RuntimeError(f"ChironError at line {line}, col {col}: {e}")

    def exec_statement(self, node, env):
        t = node['type']


        if   t == 'import':
            from chiron_runtime.loader import load_chiron_module
            for imp in node['modules']:
                path = imp['path'].split('.')  # list of identifiers
                alias = imp['alias'] or path[-1]
                if path[0] == 'py':
                    # Python stdlib import
                    py_mod = importlib.import_module('.'.join(path[1:]))
                    env.define_module(alias, py_mod)
                    self.debug(f"Imported python module {'.'.join(path[1:])} as {alias}")

                elif path[0] == 'std':
                    mod_path, abs_path = self.resolve_stdlib_module(path)
                    if mod_path.endswith('.chy'):
                        mod_env = load_chiron_module(abs_path)
                        env.define_module(alias, mod_env)
                        self.debug(f"Imported chiron module {'.'.join(path)} as {alias}")
                    else:
                        py_mod = importlib.import_module(mod_path.replace('/','.').replace('.py',''))
                        env.define_module(alias, py_mod)
                        self.debug(f"Imported python module {mod_path.replace('/','.')} as {alias}")
                else:
                    # Chiron module import
                    chy_path = self.resolve_chiron_module(path)
                    mod_env = load_chiron_module(chy_path)
                    env.define_module(alias, mod_env)
                    self.debug(f"Imported chiron module {'.'.join(path)} as {alias}")
            return None

        elif t == 'from_import':
            from chiron_runtime.loader import load_chiron_module
            module_path = node['module'].split('.')
            if module_path[0] == 'py':
                # Python module
                base = importlib.import_module('.'.join(module_path[1:]))

            elif module_path[0] == 'std':
                path, abs_path = self.resolve_stdlib_module(module_path)
                self.debug('[FROM IMPORTING] RESOLVED STD_PATH: '+path)
                if path.endswith('.chy'):
                    base = load_chiron_module(abs_path)
                else:
                    base = importlib.import_module(path.replace('/','.').replace('.py',''))

            else:
                # Chiron module
                chy_path = self.resolve_chiron_module(module_path)
                base = load_chiron_module(chy_path)
            for entry in node['names']:
                name = entry['name']
                alias = entry['alias'] or name
                if name == '*':
                    # wildcard import
                    if module_path[0] == 'py':
                        for attr in dir(base):
                            env.define_var(attr, getattr(base, attr))
                    else:
                        for attr, val in base.vars.items():
                            env.define_var(attr, val)
                        for f, fn in base.funcs.items():
                            env.define_func(f, fn)
                        for mod_name, mod_env in base.modules.items():
                            env.define_module(mod_name, mod_env)
                else:
                    if module_path[0] == 'py':
                        val = getattr(base, name)
                        # metto TUTTO in vars, così da farli trovare con env.get_var()
                        env.define_var(alias, val)
                        # (se qualcuno li chiama come funzione, funzioni lo stesso)
                        if callable(val):
                            env.define_func(alias, val)
                        self.debug(f"From python module imported {name} as {alias}")
                    else:
                        # Chiron module
                        if name in base.funcs:
                            env.define_func(alias, base.funcs[name])
                        elif name in base.vars:
                            env.define_var(alias, base.vars[name])
                        else:
                            raise RuntimeError(f"Nome '{name}' non trovato in modulo {module_path}")



        # ----- dichiarazione variabile: "tipo nome = espr;" -----
        elif t == 'declaration':
            self.debug(f"↪︎ [declaration] name='{node['name']}' type={node['var_type']} value node:", node['value'])
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

                self.debug(f"🔧 Overriding function '{name}'")
                self.debug(f"    formals = {formals}")

                def func_override(*args):
                    self.debug(f"▶️  Called override {name} with args={args}")
                    local_env = Environment(env)
                    # bind dei formali
                    for i, p in enumerate(formals):
                        local_env.define_var(p['name'], args[i])
                    self.debug(f"    local_env after binding = {local_env.vars}")

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

                self.debug(f"✅ Function '{name}' overridden\n")
                return None

            # —— property assignment generico (fallback) ——
            if target.get('type') == 'index_access':
                arr = self.eval_expression(target['object'], env)
                idx = self.eval_expression(target['index'], env)
                val = self.eval_expression(val_node, env)
                # se idx == len(arr), facciamo append, altrimenti sovrascriviamo
                if not isinstance(arr, list):
                    raise RuntimeError(f"Index‐assignment error: object is not an array/list")
                if idx == len(arr):
                    arr.append(val)
                elif 0 <= idx < len(arr):
                    arr[idx] = val
                else:
                    raise RuntimeError(f"Index‐assignment error: index {idx} out of range")
                return None

            # altrimenti assignment normale a variabile…
            value = self.eval_expression(val_node, env)
            var = target['name']
            if env.has_var(var):
                env.set_var(var, value)
            else:
                env.define_var(var, value)
            return None


        # ——— dichiarazione funzione ———
        elif t == 'declaration_callable':
            # Estrae il nome
            name = node['name']
            # Debug
            self.debug(f"Declarazione callable: {name}; body presente? {node.get('body') is not None}")

            # 1) Salva sempre il prototipo (forward-declaration + definizioni complete)
            env.save_func_decl(name, node)

            # Prendi i parametri dichiarati (anche se body==None)
            formals = node.get('params', [])

            # 2) Se è SOLO forward‐declaration (body assente), registra la firma senza corpo
            if node.get('body') is None:
                env.define_func(name, None)
                self.debug(f"Forward‐declaration salvata per {name}")
                return None

            # 3) Se è definizione completa, creiamo la closure vera e propria
            def func(*args):
                # Nuovo env lexico‐scope
                local_env = Environment(env)
                # Binding dei parametri nella closure
                for i, param in enumerate(formals):
                    local_env.define_var(param['name'], args[i])

                # Esegui ogni statement del corpo
                try:
                    for stmt in node['body']:
                        self.exec_statement(stmt, local_env)
                    return None
                except ReturnSignal as rs:
                    return rs.value
            # 4) Attacca metadata sui parametri
            func.args = list(formals)
            func._param_names = [p['name'] for p in formals]

            # 5) Registra la funzione eseguibile
            env.define_func(name, func)
            self.debug(f"Funzione completa registrata: {name} con params {func._param_names}")
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
                    self.exec_statement(stmt, env)
            elif node.get('else'):
                for stmt in node['else']:
                    self.exec_statement(stmt, env)
            return None

        # ----- while -----
        elif t == 'while':
            while self.eval_expression(node['condition'], env):
                for stmt in node['body']:
                    self.exec_statement(stmt, env)
            return None

        # ----- for each -----
        elif t == 'for_each':
            # Esempio: for_each var_name in iterable
            var_name = node['var_name']
            iterable = self.eval_expression(node['iterable'], env)
            # ci aspettiamo che iterable sia un array o simile
            length = iterable.__len__()  # o len(iterable) se supporti Python lists
            # Ciclo dall'indice 0 a length-1
            for i in range(length):
                # assegna l'elemento corrente alla var_name
                value = iterable[i]
                env.define_var(var_name, value)
                # esegui il corpo in questo environment
                for stmt in node['body']:
                    try:
                        self.exec_statement(stmt, env)
                    except ReturnSignal as rs:
                        raise rs
            return None

        # ----- for -----
        elif t == 'for':
            # init può essere dichiarazione di variabile o espressione
            self.exec_statement(node['init'], env)
            while self.eval_expression(node['condition'], env):
                for stmt in node['body']:
                    self.exec_statement(stmt, env)
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
        - map<K, V> → {}
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
        self.debug("↪︎ eval_expression got:", node)

        t = node['type']

        self.debug(t, t == 'assignment')

        if t == 'literal':
            self.debug("↪︎   literal →", node['value'])
            return node['value']

        elif t == 'identifier':
            name = node['name']

            if env.has_func(name):
                self.debug(f"↪︎   identifier '{node['name']}' →", env.get_func(name))
                return env.get_func(name)

            self.debug(f"↪︎   identifier '{node['name']}' →", env.get_var(name))

            return env.get_var(name)

        elif t == 'binary_op':
            self.debug(f"↪︎   binary_op {node['op']}")
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

        # ——— supporto per espressioni unarie logiche: 'not' ———
        if t == 'unary_logic':
            # node = { 'type':'unary_logic', 'op':'not', 'expr': <subexpr> }
            val = self.eval_expression(node['expr'], env)
            if node['op'] == 'not':
                return not bool(val)
            else:
                raise RuntimeError(f"Unknown logical unary operator '{node['op']}'")

        elif t == 'index_access':
            # object[index]
            obj = self.eval_expression(node['object'], env)
            idx = self.eval_expression(node['index'], env)
            try:
                return obj[idx]
            except Exception as e:
                raise RuntimeError(f"Index access error: {e}")



        elif t == 'call_callable':
            self.debug("↪︎   call_callable:", node)
            func = env.get_func(node['name'])
            self.debug("↪︎     resolved func:", func)
            pos_args = [ self.eval_expression(a, env)
                         for a in node['args'] if a.get('type') != 'kwarg' ]
            kw_args  = { a['key']: self.eval_expression(a['value'], env)
                         for a in node['args'] if a.get('type') == 'kwarg' }
            self.debug(f"→ Calling {node['name']} with pos={pos_args} kw={kw_args}")
            try:
                result = func(*pos_args, **kw_args)
            except ReturnSignal as rs:
                result = rs.value
            self.debug(f"→ {node['name']} returned {result}")
            return result

        # —— funzione anonima (blocchi {…}) ——
        elif t == 'anonymous_func':
            # costruiamo una chiusura uguale a come facciamo per le dichiarate
            body = node['body']
            def anon(*args):
                # chiudiamo sull' env corrente
                local_env = Environment(env)
                try:
                    for stmt in body:
                        self.exec_statement(stmt, local_env)
                    return None
                except ReturnSignal as rs:
                    return rs.value
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