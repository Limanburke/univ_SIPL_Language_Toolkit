import pytest
from src.sipl.parser import parse, SIPLSyntaxError
from src.sipl.ast import (
    Program, AssignStmt, BinaryOperation, Number, Variable,
    IfStmt, WhileStmt, SkipStmt, LogicalOrNode, NotNode, CompareOperation,
    BlockStmt, SeqStmt, SourceSpan
)

def test_ast_simple_assignment():
    code = "begin x := 1 end"
    ast = parse(code)
    assert isinstance(ast, Program)
    assert isinstance(ast.statement, AssignStmt)
    assert ast.statement.var == "x"
    assert ast.statement.expression == Number(1)
    span = ast.span
    assert span.start_line == 1
    assert span.start_column == 1
    assert code[span.start_position:span.end_position] == code


def test_ast_arithmetic_precedence():
    code = "begin x := 1 + 2 * 3 end"
    ast = parse(code)
    assign = ast.statement
    expr = assign.expression
    assert isinstance(expr, BinaryOperation)
    assert expr.op == "+"
    assert expr.left == Number(1)
    assert isinstance(expr.right, BinaryOperation)
    assert expr.right.op == "*"
    assert expr.right.left == Number(2)
    assert expr.right.right == Number(3)


def test_ast_parentheses_span():
    code = "begin x := (1 + 2) * 3 end"
    ast = parse(code)
    mult_op = ast.statement.expression
    add_op = mult_op.left
    add_span = add_op.span
    assert code[add_span.start_position:add_span.end_position] == "(1 + 2)"


def test_ast_condition_and_while():
    code = "begin while not (x > 0) do skip end"
    ast = parse(code)
    loop = ast.statement
    assert isinstance(loop, WhileStmt)
    assert isinstance(loop.condition, NotNode)
    assert isinstance(loop.condition.right, CompareOperation)
    assert loop.condition.right.op == ">"
    assert isinstance(loop.do_action, SkipStmt)


def test_syntax_error_diagnostics():
    bad_code = "begin x := end"
    with pytest.raises(SIPLSyntaxError) as exc_info:
        parse(bad_code)
    err = exc_info.value
    assert "Syntax error at line 1" in str(err)
    assert err.line == 1

def test_variable_node():
    code = "begin x := y end"
    ast = parse(code)
    assert isinstance(ast, Program)
    assert isinstance(ast.statement, AssignStmt)
    variable = ast.statement.expression
    assert isinstance(variable, Variable)
    assert variable.name == "y"
    assert variable.span is not None
    start = variable.span.start_position
    end = variable.span.end_position
    assert code[start:end] == "y"


def test_if_statement_both_branches():
    code = "begin if x > 0 then y := 1 else y := 2 end"
    ast = parse(code)
    statement = ast.statement
    assert isinstance(statement, IfStmt)
    assert isinstance(statement.condition, CompareOperation)
    assert statement.condition.op == ">"
    assert isinstance(statement.then_action, AssignStmt)
    assert statement.then_action.var == "y"
    assert statement.then_action.expression == Number(1)
    assert isinstance(statement.else_action, AssignStmt)
    assert statement.else_action.var == "y"
    assert statement.else_action.expression == Number(2)


def test_logical_or_node():
    code = "begin if x > 0 or y = 0 then skip else skip end"
    ast = parse(code)
    condition = ast.statement.condition
    assert isinstance(condition, LogicalOrNode)
    assert condition.op == "or"
    assert isinstance(condition.left, CompareOperation)
    assert condition.left.op == ">"
    assert isinstance(condition.right, CompareOperation)
    assert condition.right.op == "="


def test_logical_or_with_symbol_operator():
    code = "begin if x > 0 ∨ y = 0 then skip else skip end"
    ast = parse(code)
    condition = ast.statement.condition
    assert isinstance(condition, LogicalOrNode)
    assert condition.left.op == ">"
    assert condition.right.op == "="


def test_logical_not_with_both_spellings():
    for operator in ("not", "¬"):
        code = (
            f"begin if {operator} (x > 0) "
            "then skip else skip end"
        )
        ast = parse(code)
        condition = ast.statement.condition
        assert isinstance(condition, NotNode)
        assert isinstance(condition.right, CompareOperation)


def test_nested_if_statement():
    code = (
        "begin if x > 0 then "
        "if y > 0 then skip else skip "
        "else skip end"
    )
    ast = parse(code)
    outer = ast.statement
    assert isinstance(outer, IfStmt)
    assert isinstance(outer.then_action, IfStmt)
    assert isinstance(outer.else_action, SkipStmt)


def test_sequential_execution():
    code = "begin x := 1; y := 2 end"
    ast = parse(code)
    statement = ast.statement
    assert isinstance(statement, SeqStmt)
    assert isinstance(statement.left, AssignStmt)
    assert isinstance(statement.right, AssignStmt)
    assert statement.left.var == "x"
    assert statement.right.var == "y"


def test_nested_block():
    code = "begin begin skip end end"
    ast = parse(code)
    assert isinstance(ast.statement, BlockStmt)
    assert isinstance(ast.statement.body, SkipStmt)


def test_subtraction_and_negative_number():
    code = "begin x := 5 - 2 end"
    ast = parse(code)
    expression = ast.statement.expression
    assert isinstance(expression, BinaryOperation)
    assert expression.op == "-"
    assert expression.left == Number(5)
    assert expression.right == Number(2)
    negative_ast = parse("begin x := -2 end")
    assert negative_ast.statement.expression == Number(-2)


def test_parenthesized_expression_span():
    code = "begin x := ((1 + 2)) end"
    ast = parse(code)
    expression = ast.statement.expression
    assert isinstance(expression, BinaryOperation)
    assert expression.op == "+"
    span = expression.span
    assert code[span.start_position:span.end_position] == "((1 + 2))"


def test_variable_and_number_spans():
    code = "begin x := 123 end"
    ast = parse(code)
    assignment = ast.statement
    number = assignment.expression
    assert code[assignment.span.start_position:assignment.span.end_position] == "x := 123"
    assert code[number.span.start_position:number.span.end_position] == "123"


def test_source_span_equality_includes_positions():
    span1 = SourceSpan(1, 1, 1, 2, 0, 1)
    span2 = SourceSpan(1, 1, 1, 2, 0, 1)
    span3 = SourceSpan(1, 1, 1, 2, 4, 5)
    assert span1 == span2
    assert span1 != span3


def test_different_ast_node_types_are_not_equal():
    assert Number(1) != Variable("x")
    assert Number(1) != Number(2)


def test_missing_expression_reports_syntax_error():
    with pytest.raises(SIPLSyntaxError) as exc_info:
        parse("begin x := end")
    error = exc_info.value
    assert error.line is not None
    assert error.column is not None
    assert "Syntax error" in str(error)


def test_unexpected_character_reports_syntax_error():
    with pytest.raises(SIPLSyntaxError) as exc_info:
        parse("begin x := @ end")
    error = exc_info.value
    assert error.line == 1
    assert error.column is not None
    assert "Unexpected character" in str(error)


def test_missing_end_reports_syntax_error():
    with pytest.raises(SIPLSyntaxError) as exc_info:
        parse("begin skip")
    error = exc_info.value
    assert error.line is not None
    assert error.column is not None
    assert "Syntax error" in str(error)


def test_reserved_word_is_not_a_variable():
    with pytest.raises(SIPLSyntaxError):
        parse("begin if := 2 end")