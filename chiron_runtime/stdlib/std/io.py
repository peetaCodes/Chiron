# chiron_runtime/stdlib/std/io.py

# TODO: try coding the chiron stdlib in chiron itself rather than python

def print_(*args):
    """
    Chiron std.io.print: alias di print Python
    """
    # Converte tutto in stringa e stampa separato da spazio
    print(*args)

def input_(prompt: str = "") -> str:
    """
    Chiron std.io.input: alias di input Python
    """
    return input(prompt)