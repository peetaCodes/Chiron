from chiron_runtime.lexer import Lexer
from chiron_runtime.parser import Parser
from chiron_runtime.interpreter import Interpreter

def dumb_env(interpreter: Interpreter) -> None:
    """
    Stampa a schermo le variabili e i loro valori
    nell'ambiente globale dell'interprete.
    """
    env = interpreter.global_env
    print("\n=== DUMB ENVIRONMENT DUMP ===")
    for name, value in env.vars.items():
        print(f"{name} = {value}")
    for name, value in env.funcs.items():
        print(f"{name} = {value}")
    print("=== END DUMP ===\n")

def run_file(filename):
    with open(filename, "r", encoding="utf-8") as f:
        source_code = f.read()

    lexer = Lexer(source_code)
    tokens = lexer.tokenize()

    parser = Parser(tokens)
    ast = parser.parse()

    print('DEBUG ast: ', ast)

    interpreter = Interpreter()
    interpreter.interpret(ast)

    dumb_env(interpreter=interpreter)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python main.py file.chy")
        sys.exit(1)

    run_file(sys.argv[1])
