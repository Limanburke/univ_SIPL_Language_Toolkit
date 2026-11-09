import json
from pathlib import Path
import pytest
from src.sipl.ast import BinaryOperation, CompareOperation, Node, Number, Program, SkipStmt
from src.sipl.parser import parse
from src.sipl.semantics.terms import (Term, Apply, Assign, Comp, Const, Id, If, Name, Paren, While)
from src.sipl.semantics.builder import build_term

GOLDEN = Path(__file__).parent / "golden" / "semantics"
CASES = sorted(p.stem for p in GOLDEN.glob("*.sipl"))

@pytest.mark.parametrize("name", CASES)
def test_golden_ascii(name):
    program = parse((GOLDEN / f"{name}.sipl").read_text(encoding="utf-8"))
    expected = (GOLDEN / f"{name}.term").read_text(encoding="utf-8").strip()
    assert str(build_term(program)) == expected


def test_golden_directory_is_not_empty():
    assert len(CASES) >= 10


def test_structure_of_term():
    term = build_term(parse("begin if x > 0 then y := 1 else skip end"))
    assert isinstance(term, If)
    assert term.cond == Apply("gr", (Name("x"), Const(0)))
    assert term.then_action == Assign("y", Const(1))
    assert term.else_action == Id()


def test_sequence_keeps_ast_nesting():
    term = build_term(parse("begin x := 1; y := 2; z := 3 end"))
    assert isinstance(term, Comp)
    nested_left = isinstance(term.left, Comp)
    nested_right = isinstance(term.right, Comp)
    assert nested_left != nested_right


def test_block_and_while_structure():
    term = build_term(parse("begin while x > 0 do begin x := x - 1 end end"))
    assert isinstance(term, While)
    assert isinstance(term.do_action, Paren)


def test_rules_are_recorded():
    term = build_term(parse("begin x := a - 1; if b = 0 then skip else skip end"))
    assert term.rule == "NS_Stm_Seq"
    assert term.left.rule == "NS_Stm_As"
    assert term.left.arg.rule == "NS_A_Sub"
    assert term.left.arg.args[0].rule == "NS_A_Var"
    assert term.left.arg.args[1].rule == "NS_A_Num"
    assert term.right.rule == "NS_Stm_If"
    assert term.right.cond.rule == "NS_B_eq"
    assert term.right.then_action.rule == "NS_Stm_skip"


def test_every_rule_id_from_course_is_reachable():
    code = (
        "begin x := 1 + 2 - 3 * y; "
        "while not (x = 0) or x > 1 do begin skip end; "
        "if x = 0 then skip else skip end"
    )
    seen = set()

    def walk(t):
        seen.add(t.rule)
        for c in t.children():
            walk(c)

    walk(build_term(parse(code)))
    assert seen >= {
        "NS_Stm_As", "NS_Stm_Seq", "NS_Stm_If", "NS_Stm_Wh", "NS_Stm_BE",
        "NS_Stm_skip", "NS_A_Num", "NS_A_Var", "NS_A_Add", "NS_A_Sub",
        "NS_A_Mult", "NS_B_eq", "NS_B_gr", "NS_B_or", "NS_B_neg"
    }


def test_span_links_back_to_source():
    code = "begin x := 1 + 2 end"
    term = build_term(parse(code))
    s = term.span
    assert code[s.start_position:s.end_position] == "x := 1 + 2"
    inner = term.arg.span
    assert code[inner.start_position:inner.end_position] == "1 + 2"


def test_term_equality_ignores_span_and_rule():
    a = build_term(parse("begin x := 1 end"))
    b = build_term(parse("begin\n   x   :=   1\nend"))
    assert a == b
    assert a != build_term(parse("begin x := 2 end"))


def test_to_dict_is_json_serialisable():
    data = build_term(parse("begin while x > 0 do x := x - 1 end")).to_dict()
    json.dumps(data)
    assert data["type"] == "While"
    assert data["rule"] == "NS_Stm_Wh"
    assert data["condition"]["func"] == "gr"
    assert data["condition"]["args"][0] == {
        "type": "Name",
        "rule": "NS_A_Var",
        "name": "x",
        "span": data["condition"]["args"][0]["span"],
    }
    assert data["do_action"]["var"] == "x"


def test_unknown_node_and_unsupported_operators():
    with pytest.raises(RuntimeError, match="No semantic rule"):
        build_term(Node())
    with pytest.raises(RuntimeError, match="Unsupported binary operator: '/'"):
        build_term(BinaryOperation(Number(1), "/", Number(2)))
    with pytest.raises(RuntimeError, match="Unsupported comparison operator: '<'"):
        build_term(CompareOperation("<", Number(1), Number(2)))


def test_manually_built_ast_is_supported():
    assert str(build_term(Program(SkipStmt()))) == "id"


def test_base_term_fallback_methods():
    t = Term()
    assert t.children() == ()
    with pytest.raises(NotImplementedError):
        str(t)

def test_terms_repr():
    t = Id()
    assert repr(t) == "id"
    assert repr(Const(5)) == "5"


def test_terms_inequality_and_not_implemented():
    id_term = Id()
    const_term = Const(1)
    name_term = Name("x")
    apply_term = Apply("add", (const_term, const_term))
    assign_term = Assign("x", const_term)
    comp_term = Comp(id_term, id_term)
    if_term = If(const_term, id_term, id_term)
    while_term = While(const_term, id_term)
    paren_term = Paren(id_term)

    terms = [
        id_term, const_term, name_term, apply_term,
        assign_term, comp_term, if_term, while_term, paren_term
    ]

    for t in terms:
        assert t != "not_a_term"
        assert t != 12345
        assert t is not None

    assert Const(1) != Const(2)
    assert Name("x") != Name("y")
    assert Apply("add", (Const(1),)) != Apply("sub", (Const(1),))
    assert Apply("add", (Const(1),)) != Apply("add", (Const(2),))
    assert Assign("x", Const(1)) != Assign("y", Const(1))
    assert Assign("x", Const(1)) != Assign("x", Const(2))
    assert Comp(Const(1), Const(2)) != Comp(Const(2), Const(2))
    assert Comp(Const(1), Const(1)) != Comp(Const(1), Const(2))
    assert If(Const(1), Id(), Id()) != If(Const(2), Id(), Id())
    assert If(Const(1), Id(), Id()) != If(Const(1), Const(1), Id())
    assert If(Const(1), Id(), Id()) != If(Const(1), Id(), Const(1))
    assert While(Const(1), Id()) != While(Const(2), Id())
    assert While(Const(1), Id()) != While(Const(1), Const(1))
    assert Paren(Const(1)) != Paren(Const(2))