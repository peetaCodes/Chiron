from chiron_runtime.lexer import Lexer
from chiron_runtime.parser import Parser
from chiron_runtime.interpreter import Interpreter, Environment

def load_chiron_module(path: str) -> Environment:
    """
    Legge il file .chy in path, lo lex/parse/interpreta in un nuovo Environment
    e restituisce quell'ambiente con vars, funcs, func_decls popolati.
    """
    with open(path, 'r', encoding='utf‑8') as f:
        source = f.read()

    tokens = Lexer(source).tokenize()   # dal tuo lexer
    ast    = Parser(tokens).parse()     # dal tuo parser

    print("Loader's AST: " + str(ast))

    mod_env = Environment()             # namespace del modulo
    interp  = Interpreter()
    # Evitiamo di eseguire main(): vogliamo solo caricare definizioni

    # 1) Pre-registriamo tutte le dichiarazioni_callable nel mod_env.func_decls
    for node in ast:
        if node.get('type') == 'declaration_callable':
            # registra il prototipo anche se body==null o body!=null
            name = node['name']
            mod_env.func_decls[name] = node

    # 2) Eseguiamo poi tutte le dichiarazioni/assegnazioni tramite l’interprete
    for stmt in ast:
        if stmt['type'] == 'declaration_callable':
            interp.exec_statement(stmt, mod_env)
        elif stmt['type'] in ('declaration','assignment','from_import','import'):
            interp.exec_statement(stmt, mod_env)
        # skip expr_stmt, return, ecc.
    return mod_env
