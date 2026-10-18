from lark import Lark
from pathlib import Path

grammar_path = Path(__file__).resolve().parent.parent.parent / "grammar" / "grammar.lark"

def load_grammar(file_path):
    with open(file_path, "r") as f:
        grammar = f.read()
    return Lark(grammar, start="prog", parser="earley")

parser = load_grammar(grammar_path)