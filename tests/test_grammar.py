import pytest
from src.sipl.parser import parser
from lark.exceptions import UnexpectedInput

VALID_BASE_STATEMENTS = [
    "x := -1",
    "x := 0",
    "x := 1",
    "x := y",
    "x := x + y",
    "x := x - y",
    "x := x * y",
    "x := x * (y + z)",
    "x := x ; y := x",
    "skip",
    "begin skip end",
    "if x = 0 then skip else skip",
    "while x > 0 do skip"
]

@pytest.mark.parametrize("stmt", VALID_BASE_STATEMENTS)
def test_base_statement_in_block(stmt):
    text = f"begin {stmt} end"
    tree = parser.parse(text)
    assert tree is not None

VALID_SEQUENTIAL_OPERATORS = [
    "x := 0 ; y := 1 ; z := 2",
    "x := 0 ; skip",
    "x := 0 ; begin skip end",
    "x := 0 ; if x = 0 then skip else skip",
    "x := 0 ; while x > 0 do skip",
    "skip ; skip",
    "skip ; begin skip end",
    "skip ; if x = 0 then skip else skip",
    "skip ; while x > 0 do skip",
    "begin skip end ; begin skip end",
    "begin skip end ; if x = 0 then skip else skip",
    "begin skip end ; while x > 0 do skip",
    "if x = 0 then skip else skip ; if x = 0 then skip else skip",
    "if x = 0 then skip else skip ; while x > 0 do skip",
    "while x > 0 do skip ; while x > 0 do skip"
]
@pytest.mark.parametrize("stmt", VALID_SEQUENTIAL_OPERATORS)
def test_sequential_operators(stmt):
    text = f"begin {stmt} end"
    tree = parser.parse(text)
    assert tree is not None

VALID_IF_STATEMENTS = [
    "if x > 0 then skip else skip",
    "if not x = 0 then skip else skip",
    "if not x > 0 then skip else skip",
    "if x = 0 then begin skip end else begin skip end",
    "if x = 0 then if x = 0 then skip else skip else if x = 0 then skip else skip",
    "if x = 0 then x := 1 else x := x",
    "if x = 0 then while x > 0 do skip else while x > 0 do skip"
]
@pytest.mark.parametrize("stmt", VALID_IF_STATEMENTS)
def test_if_statements(stmt):
    text = f"begin {stmt} end"
    tree = parser.parse(text)
    assert tree is not None

RESERVED_KEYWORDS = [
    "begin",
    "end",
    "if",
    "then",
    "else",
    "while",
    "do",
    "skip",
    "or",
    "not"
]

@pytest.mark.parametrize("kw", RESERVED_KEYWORDS)
def test_reserved_keywords_as_variables(kw):
    invalid_assign = f"begin {kw} := 5 end"
    with pytest.raises(UnexpectedInput):
        parser.parse(invalid_assign)

    invalid_expr = f"begin x := {kw} + 1 end"
    with pytest.raises(UnexpectedInput):
        parser.parse(invalid_expr)

INVALID_STRUCTURES = [
    "x := 0",
    "begin end",
    "skip",
    "if x > 1 then skip else skip",
    "while x > 1 do skip",
    "x := 0; y := 1",
    "begi skip end",
    "begin ski end",
    "begin 0 end",
    "begin skip en",
    "begin x := 0; end",
    "begin x = 1 end",
    "begin x := 0.5 end",
    "begin x := 'abc' end",
    "begin := 5 end",
    "begin x := ; end",
    "begin x := end",
    "begin begin := 0 end",
    "begin if x := 0 then skip else skip end",
    "begin i x > 0 then skip else skip end",
    "begin if x > 0 skip else skip end",
    "begin if x > 0 then skip end",
    "begin if 1 then skip else skip end",
    "begin while x > 0 end",
    "begin while skip do skip end",
    "begin x := (1 + 2 end",
    "begin while x > 0 do end",
]

@pytest.mark.parametrize("code", INVALID_STRUCTURES)
def test_invalid_syntax_structures(code):
    with pytest.raises(UnexpectedInput):
        parser.parse(code)