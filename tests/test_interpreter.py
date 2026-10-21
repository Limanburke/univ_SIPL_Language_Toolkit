import pytest
from src.sipl.parser import parse
from src.sipl.interpreter import Interpreter
from src.sipl.ast import (
    Node, Program, AssignStmt, IfStmt, WhileStmt,
    Number, BinaryOperation, CompareOperation, SkipStmt
)

class UnknownDummyNode(Node):
    pass

def test_arithmetic_near_zero_and_signs():
    code = "begin a := 0 - 1; b := a * 0; c := a - (0 - 2) end"
    res = Interpreter().execute(parse(code))
    assert res == {"a": -1, "b": 0, "c": 1}

def test_addition_near_zero():
    code = "begin sum_zero := -1 + 1; sum_pos := 0 + 2 end"
    res = Interpreter().execute(parse(code))
    assert res == {"sum_zero": 0, "sum_pos": 2}


def test_chained_subtraction_sign_boundary():
    code = "begin diff := 0 - 1 - 1; inv := 1 - 1 - 1 end"
    res = Interpreter().execute(parse(code))
    assert res == {"diff": -2, "inv": -1}


def test_multiplication_with_boundary_values():
    code = "begin neg := -1 * 1; zero := -1 * 0; pos := -1 * -1 end"
    res = Interpreter().execute(parse(code))
    assert res == {"neg": -1, "zero": 0, "pos": 1}


def test_if_boundary_zero():
    code = """
    begin
        if val > 0 then
            sign := 1
        else
            if val = 0 then
                sign := 0
            else
                sign := -1
    end
    """
    ast = parse(code)
    interp = Interpreter()
    assert interp.execute(ast, initial_state={"val": -1})["sign"] == -1
    assert interp.execute(ast, initial_state={"val": 0})["sign"] == 0
    assert interp.execute(ast, initial_state={"val": 1})["sign"] == 1


def test_logic_boundary_truth_table():
    code = """
    begin
        if not (x = 0) or y > 0 then
            flag := 1
        else
            flag := 0
    end
    """
    ast = parse(code)
    interp = Interpreter()
    assert interp.execute(ast, initial_state={"x": 0, "y": 0})["flag"] == 0
    assert interp.execute(ast, initial_state={"x": 0, "y": 1})["flag"] == 1
    assert interp.execute(ast, initial_state={"x": -1, "y": 0})["flag"] == 1


def test_while_crossing_zero_to_negative():
    code = """
    begin
        while counter > 0 do
            counter := counter - 1
    end
    """
    ast = parse(code)
    assert Interpreter().execute(ast, initial_state={"counter": 2})["counter"] == 0
    assert Interpreter().execute(ast, initial_state={"counter": -1})["counter"] == -1


def test_power_of_5():
    code = """
    begin
        R := 5;
        while X > 1 do
        begin
            R := R * 5;
            X := X - 1
        end
    end
    """
    ast = parse(code)
    interp = Interpreter()
    assert interp.execute(ast, initial_state={"X": 1})["R"] == 5
    assert interp.execute(ast, initial_state={"X": 2})["R"] == 25


def test_gcd():
    code = """
    begin
        while not (M = N) do
            if M > N then
                M := M - N
            else
                N := N - M
    end
    """
    ast = parse(code)
    res = Interpreter().execute(ast, initial_state={"M": 7, "N": 5})
    assert res["M"] == 1 and res["N"] == 1


def test_skip_with_zero_state():
    code = "begin begin skip end end"
    res = Interpreter().execute(parse(code), initial_state={"zero": 0, "neg": -1})
    assert res == {"zero": 0, "neg": -1}


def test_infinite_loop_max_iterations():
    code = "begin while 0 = 0 do skip end"
    interp = Interpreter(max_iterations=15)
    with pytest.raises(RuntimeError, match="Execution exceeded loop iteration limit"):
        interp.execute(parse(code))


def test_global_step_limit_halt():
    code = "begin while 0 = 0 do skip end"
    interp = Interpreter(max_steps=20)
    with pytest.raises(RuntimeError, match="Execution exceeded maximum step limit"):
        interp.execute(parse(code))


def test_constructor_limit_validation():
    with pytest.raises(RuntimeError, match="Invalid max_iterations"):
        Interpreter(max_iterations=0)
    with pytest.raises(RuntimeError, match="Invalid max_iterations"):
        Interpreter(max_iterations=-1)
    with pytest.raises(RuntimeError, match="Invalid max_steps"):
        Interpreter(max_steps=0)
    with pytest.raises(RuntimeError, match="Invalid max_steps"):
        Interpreter(max_steps=-1)


def test_uninitialized_variable_near_zero():
    ast = parse("begin target := undef - 0 end")
    with pytest.raises(RuntimeError, match="referenced before assignment"):
        Interpreter().execute(ast)


def test_initial_state_type_guards():
    interp = Interpreter()
    prog = parse("begin skip end")
    with pytest.raises(RuntimeError, match="Initial state must be a dictionary"):
        interp.execute(prog, initial_state=(0, 0))
    with pytest.raises(RuntimeError, match="must have an integer value"):
        interp.execute(prog, initial_state={"x": 0.0})
    with pytest.raises(RuntimeError, match="must have an integer value"):
        interp.execute(prog, initial_state={"x": False})
    with pytest.raises(RuntimeError, match="Variable name in state must be a non-empty string"):
        interp.execute(prog, initial_state={" ": 0})


def test_invalid_ast_payload():
    with pytest.raises(RuntimeError, match="Expected a Program AST node"):
        Interpreter().execute(None)


def test_unknown_ast_node_triggers_generic_visit():
    interp = Interpreter()
    fake_program = Program(statement=UnknownDummyNode())
    with pytest.raises(RuntimeError, match="No visit_unknowndummynode method defined"):
        interp.execute(fake_program)


def test_unsupported_binary_operator():
    interp = Interpreter()
    bad_expr = BinaryOperation(left=Number(10), op="/", right=Number(2))
    prog = Program(statement=AssignStmt(var="res", expression=bad_expr))
    with pytest.raises(RuntimeError, match="Unsupported binary operator: '/'"):
        interp.execute(prog)


def test_arithmetic_operations_non_integer_values():
    interp = Interpreter()
    bad_expr = BinaryOperation(left=Number(1), op="+", right=Number(2))
    prog = Program(statement=AssignStmt(var="res", expression=bad_expr))
    original_visit_number = interp.visit_number
    interp.visit_number = lambda node: "not_a_number"
    try:
        with pytest.raises(RuntimeError, match="Arithmetic operations are only defined for integer values"):
            interp.execute(prog)
    finally:
        interp.visit_number = original_visit_number


def test_unsupported_comparison_operator():
    interp = Interpreter()
    bad_cond = CompareOperation(op="<", left=Number(1), right=Number(2))
    prog = Program(statement=IfStmt(condition=bad_cond, then_action=SkipStmt(), else_action=SkipStmt()))
    with pytest.raises(RuntimeError, match="Unsupported comparison operator: '<'"):
        interp.execute(prog)


def test_cannot_assign_non_integer_value():
    interp = Interpreter()
    prog = Program(statement=AssignStmt(var="x", expression=Number(0)))
    interp.visit_number = lambda node: 3.14
    with pytest.raises(RuntimeError, match="Cannot assign non-integer value to variable 'x'"):
        interp.execute(prog)


def test_if_condition_not_boolean():
    interp = Interpreter()
    prog = Program(statement=IfStmt(condition=Number(1), then_action=SkipStmt(), else_action=SkipStmt()))
    with pytest.raises(RuntimeError, match="The condition of an if-statement must evaluate to a boolean"):
        interp.execute(prog)


def test_while_condition_not_boolean():
    interp = Interpreter()
    prog = Program(statement=WhileStmt(condition=Number(1), do_action=SkipStmt()))
    with pytest.raises(RuntimeError, match="The condition of a while-statement must evaluate to a boolean"):
        interp.execute(prog)