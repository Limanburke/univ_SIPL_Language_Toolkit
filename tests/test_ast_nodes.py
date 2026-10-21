from src.sipl.ast import (
    SourceSpan, Node, Number, Variable, BinaryOperation,
    CompareOperation, LogicalOrNode, NotNode, AssignStmt,
    SeqStmt, IfStmt, WhileStmt, BlockStmt, SkipStmt, Program
)


def test_source_span_repr_and_inequality():
    span = SourceSpan(1, 2, 3, 4, 10, 20)
    assert "SourceSpan(line=1:2..column=3:4, pos=10..20)" in repr(span)
    assert span != "not_a_span"
    assert span != 123


def test_base_node_repr():
    node = Node()
    assert repr(node) == "Node(span=None)"


def test_number_repr_and_inequality():
    n = Number(42)
    assert repr(n) == "Number(value=42, span=None)"
    assert n != "42"
    assert n != 42


def test_variable_repr_and_inequality():
    v = Variable("count")
    assert repr(v) == "Variable(name='count', span=None)"
    assert v != "count"


def test_binary_operation_repr_and_inequality():
    op = BinaryOperation(Number(1), "+", Number(2))
    assert "BinaryOperation" in repr(op)
    assert op != 100
    assert op != BinaryOperation(Number(1), "-", Number(2))


def test_compare_operation_repr_and_inequality():
    cmp_node = CompareOperation("=", Variable("x"), Number(0))
    assert "CompareOperation" in repr(cmp_node)
    assert cmp_node != "x = 0"
    assert cmp_node != CompareOperation(">", Variable("x"), Number(0))


def test_logical_or_repr_and_inequality():
    or_node = LogicalOrNode(Variable("a"), Variable("b"))
    assert "LogicalOrNode" in repr(or_node)
    assert or_node != False
    assert or_node != LogicalOrNode(Variable("a"), Variable("c"))


def test_not_node_repr_and_inequality():
    not_node = NotNode(Variable("flag"))
    assert "NotNode" in repr(not_node)
    assert not_node != True
    assert not_node != NotNode(Variable("other"))


def test_assign_stmt_repr_and_inequality():
    assign = AssignStmt("x", Number(5))
    assert "AssignStmt" in repr(assign)
    assert assign != 5
    assert assign != AssignStmt("y", Number(5))


def test_seq_stmt_repr_and_inequality():
    seq = SeqStmt(SkipStmt(), SkipStmt())
    assert "SeqStmt" in repr(seq)
    assert seq != "skip; skip"
    assert seq != SeqStmt(SkipStmt(), AssignStmt("x", Number(1)))


def test_if_stmt_repr_and_inequality():
    stmt = IfStmt(Variable("cond"), SkipStmt(), SkipStmt())
    assert "IfStmt" in repr(stmt)
    assert stmt != "if"
    assert stmt != IfStmt(Variable("other"), SkipStmt(), SkipStmt())


def test_while_stmt_repr_and_inequality():
    stmt = WhileStmt(Variable("c"), SkipStmt())
    assert "WhileStmt" in repr(stmt)
    assert stmt != "while"
    assert stmt != WhileStmt(Variable("other"), SkipStmt())


def test_block_stmt_repr_and_inequality():
    blk = BlockStmt(SkipStmt())
    assert "BlockStmt" in repr(blk)
    assert blk != "block"
    assert blk != BlockStmt(AssignStmt("x", Number(1)))


def test_skip_stmt_repr_and_inequality():
    sk = SkipStmt()
    assert "SkipStmt" in repr(sk)
    assert sk != "skip"


def test_program_repr_and_inequality():
    prog = Program(SkipStmt())
    assert "Program" in repr(prog)
    assert prog != "program"
    assert prog != Program(AssignStmt("x", Number(1)))