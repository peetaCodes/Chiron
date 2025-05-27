import importlib
import inspect
import pathlib

def generate_all_for_module(module_name: str, output_path: pathlib.Path):
    """
    Genera un file __all__.py che contiene solo classi e funzioni pubbliche
    definite nel modulo (esclude quelle importate da altri moduli).
    """
    module = importlib.import_module(module_name)
    names = []

    for name, obj in inspect.getmembers(module):
        if name.startswith('_'):
            continue

        # Includi solo funzioni e classi
        if inspect.isfunction(obj) or inspect.isclass(obj):
            # Escludi se non definito nel modulo stesso (cioè importato)
            if getattr(obj, '__module__', None) != module.__name__:
                continue
            names.append(name)

    names.sort()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('# -*- coding: utf-8 -*-\n')
        f.write('# Questo file è generato automaticamente da generate_all_for_module()\n\n')
        f.write('__all__ = [\n')
        for n in names:
            f.write(f"    '{n}',\n")
        f.write(']\n')

if __name__ == '__main__':
    module_name = 'std.io.io'
    out = pathlib.Path('std/io/__all__.py')
    generate_all_for_module(module_name, out)
    print(f'__all__.py generato in: {out}')
