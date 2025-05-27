#!/usr/bin/env python3
import sys
from chiron_runtime.lexer import Lexer
from chiron_runtime.parser import Parser
from chiron_runtime.interpreter import Interpreter

def run_file(path):
    with open(path) as f:
        code = f.read()
    tokens = Lexer(code).tokenize()
    ast = Parser(tokens).parse()
    interpreter = Interpreter()
    interpreter.interpret(ast)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: chiron <filename.chy>")
        sys.exit(1)
    run_file(sys.argv[1])