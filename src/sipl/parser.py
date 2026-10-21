from lark import Lark, Token, Tree
from pathlib import Path
from lark.exceptions import UnexpectedInput, UnexpectedToken, UnexpectedCharacters
from src.sipl.ast import (
    Number, BinaryOperation, SourceSpan, Variable, CompareOperation,
    LogicalOrNode, NotNode, AssignStmt, SeqStmt, IfStmt,
    WhileStmt, BlockStmt, SkipStmt, Program
)

class SIPLSyntaxError(Exception):
    def __init__(self, message: str, line: int = None, column: int = None):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column


def _make_span(meta):
    if not hasattr(meta, 'line') or meta.line is None:
        return None

    return SourceSpan(
        start_line=meta.line,
        start_column=meta.column,
        end_line=meta.end_line,
        end_column=meta.end_column,
        start_position=meta.start_pos,
        end_position=meta.end_pos
    )


def build_ast(node):
    if isinstance(node, Token):
        return node

    if not isinstance(node, Tree):
        return node

    children = [build_ast(child) for child in node.children]
    rule_name = node.data
    span = _make_span(node.meta)

    if rule_name == 'number':
        return Number(value=int(children[0]), span=span)

    elif rule_name == 'variable':
        return Variable(name=str(children[0]), span=span)

    elif rule_name == 'paren_expr' or rule_name == 'paren_cond':
        inner_node = children[0]
        inner_node.span = span
        return inner_node

    elif rule_name == 'add':
        return BinaryOperation(left=children[0], op='+', right=children[1], span=span)

    elif rule_name == 'sub':
        return BinaryOperation(left=children[0], op='-', right=children[1], span=span)

    elif rule_name == 'mult':
        return BinaryOperation(left=children[0], op='*', right=children[1], span=span)

    elif rule_name == 'eq':
        return CompareOperation(op='=', left=children[0], right=children[1], span=span)

    elif rule_name == 'gr':
        return CompareOperation(op='>', left=children[0], right=children[1], span=span)

    elif rule_name == 'logic_or':
        return LogicalOrNode(left=children[0], right=children[1], span=span)

    elif rule_name == 'logic_not':
        return NotNode(expression=children[0], span=span)

    elif rule_name == 'assignment':
        return AssignStmt(var=str(children[0]), expression=children[1], span=span)

    elif rule_name == 'sequential_execution':
        return SeqStmt(left=children[0], right=children[1], span=span)

    elif rule_name == 'if_statement':
        return IfStmt(condition=children[0], then_action=children[1], else_action=children[2], span=span)

    elif rule_name == 'while_cycle':
        return WhileStmt(condition=children[0], do_action=children[1], span=span)

    elif rule_name == 'block':
        return BlockStmt(body=children[0], span=span)

    elif rule_name == 'skip':
        return SkipStmt(span=span)

    elif rule_name == 'program':
        return Program(statement=children[0], span=span)

    else:
        raise ValueError(f"Unhandled grammar rule: '{rule_name}'")

grammar_path = Path(__file__).resolve().parent.parent.parent / "grammar" / "grammar.lark"

def load_grammar(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        grammar = f.read()
    return Lark(grammar, start="prog", parser="earley", propagate_positions=True)

parser = load_grammar(grammar_path)

def parse(code) -> Program:
    try:
        raw_tree = parser.parse(code)
    except UnexpectedInput as err:
        line = getattr(err, "line", None)
        column = getattr(err, "column", None)
        location_str = f"line {line}, column {column}" if line and column else "end of input"

        if isinstance(err, UnexpectedToken):
            token_val = repr(str(err.token)) if err.token.type != "$END" else "EOF"
            expected_tokens = sorted(err.expected)
            msg = f"Unexpected token {token_val}"
            if expected_tokens:
                msg += f" Expected one of: {', '.join(expected_tokens)}"
        elif isinstance(err, UnexpectedCharacters):
            char = repr(code[err.pos_in_stream]) if err.pos_in_stream < len(code) else "EOF"
            msg = f"Unexpected character {char}"
        else:
            msg = "Unexpected end of file"

        context = err.get_context(code, span=35).rstrip()
        error_message = f"Syntax error at {location_str}: {msg}\n{context}"
        raise SIPLSyntaxError(error_message, line=line, column=column) from err

    ast = build_ast(raw_tree)
    if not isinstance(ast, Program):
        raise RuntimeError("Parser failed to produce a valid root Program node")
    return ast