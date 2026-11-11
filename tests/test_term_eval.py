import json
import pytest
from src.sipl.ast import Program, SkipStmt
from src.sipl.interpreter.interpreter import Interpreter
from src.sipl.parser import parse
from src.sipl.semantics.builder import build_term
from src.sipl.semantics.term_eval import (
    EvaluationResult, TermEvaluator, SIPLSemanticError, evaluate
)
from src.sipl.semantics.sem_observer import SemanticObserver, SemanticTraceObserver
from src.sipl.semantics.terms import Apply, Assign, Const, Id, If, Name, While, Paren


def run(code, state=None, **limits):
    observer = SemanticTraceObserver()
    result = evaluate(build_term(parse(code)), state, observer, **limits)
    return result, observer.events


def rules(events):
    return [e["rule"] for e in events if e["event"] == "rule_applied"]


def test_homework_power_of_five_term_and_evaluation():
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
    program = parse(code)
    term = build_term(program)

    expected_term_str = (
        "AS^R(5) . WH(S^2(gr, X=>, 1), "
        "(AS^R(S^2(mult, R=>, 5)) . AS^X(S^2(sub, X=>, 1))))"
    )
    assert str(term) == expected_term_str

    observer = SemanticTraceObserver()
    result = evaluate(term, initial_state={"X": 3}, observer=observer)

    assert result.defined
    assert result.state == {"X": 1, "R": 125}

    loop_checks = [e for e in observer.events if e["event"] == "loop_check"]
    assert len(loop_checks) == 3
    assert [(c["iteration"], c["condition"]) for c in loop_checks] == [
        (0, True),
        (1, True),
        (2, False)
    ]

    assigns = [e for e in observer.events if e.get("rule") == "NS_Stm_As"]
    assert len(assigns) == 5

    assert assigns[0]["state_after"] == {"X": 3, "R": 5}
    assert assigns[1]["state_after"] == {"X": 3, "R": 25}
    assert assigns[2]["state_after"] == {"X": 2, "R": 25}
    assert assigns[3]["state_after"] == {"X": 2, "R": 125}
    assert assigns[4]["state_after"] == {"X": 1, "R": 125}


def test_assignment_rule_order_and_result():
    result, events = run("begin x := x + 1 end", {"x": 2})
    assert result.defined and result.state == {"x": 3}
    assert rules(events) == ["NS_A_Var", "NS_A_Num", "NS_A_Add", "NS_Stm_As"]
    values = [e["value"] for e in events if e["event"] == "rule_applied" and e["kind"] != "stmt"]
    assert values == [2, 1, 3]


def test_skip_is_identity():
    result, events = run("begin skip end", {"x": 5})
    assert result.state == {"x": 5}
    assert rules(events) == ["NS_Stm_skip"]


def test_composition_applies_left_then_right():
    result, events = run("begin x := 1; y := x + 1 end")
    assert result.state == {"x": 1, "y": 2}
    assert rules(events) == [
        "NS_A_Num", "NS_Stm_As", "NS_A_Var", "NS_A_Num", "NS_A_Add", "NS_Stm_As", "NS_Stm_Seq"
    ]


def test_if_evaluates_only_chosen_branch():
    code = "begin if x > 0 then y := 1 else y := 2 end"
    pos, ev_pos = run(code, {"x": 5})
    neg, ev_neg = run(code, {"x": 0})
    assert pos.state["y"] == 1 and neg.state["y"] == 2
    assert rules(ev_pos) == ["NS_A_Var", "NS_A_Num", "NS_B_gr", "NS_A_Num", "NS_Stm_As", "NS_Stm_If"]
    assert rules(ev_neg)[3:] == ["NS_A_Num", "NS_Stm_As", "NS_Stm_If"]


def test_block_rule():
    result, events = run("begin begin x := 1 end end")
    assert result.state == {"x": 1}
    assert rules(events)[-1] == "NS_Stm_BE"


def test_negation_and_or_rules():
    result, events = run("begin if not (x = 0) or y > 0 then f := 1 else f := 0 end", {"x": 0, "y": 1})
    assert result.state["f"] == 1
    assert {"NS_B_neg", "NS_B_or", "NS_B_eq", "NS_B_gr"} <= set(rules(events))


def test_while_trace_and_loop_checks():
    result, events = run("begin while x > 0 do x := x - 1 end", {"x": 2})
    assert result.state == {"x": 0}
    checks = [e for e in events if e["event"] == "loop_check"]
    assert [(c["iteration"], c["condition"]) for c in checks] == [(0, True), (1, True), (2, False)]
    assert rules(events)[-1] == "NS_Stm_Wh"
    assert rules(events).count("NS_Stm_As") == 2


def test_event_envelope_and_depth():
    result, events = run("begin x := 1 end")
    assert [e["event"] for e in events] == ["eval_start", "rule_applied", "rule_applied", "eval_end"]
    assert [e["depth"] for e in events[1:3]] == [1, 0]
    assert [e["step"] for e in events[1:3]] == [1, 2]
    assert events[-1]["status"] == "defined" and events[-1]["steps"] == 2
    assert events[1]["span"] is not None


CORPUS = [
    ("begin R := 1; while Y > 0 do begin R := R * X; Y := Y - 1 end end", {"X": 3, "Y": 4}),
    ("begin while not (M = N) do if M > N then M := M - N else N := N - M end", {"M": 21, "N": 6}),
    ("begin if val > 0 then s := 1 else if val = 0 then s := 0 else s := -1 end", {"val": -7}),
    ("begin a := 0 - 1; b := a * 0; c := a - (0 - 2) end", {}),
    ("begin begin skip end end", {"z": 0, "n": -1}),
    ("begin if not (x = 0) or y > 0 then f := 1 else f := 0 end", {"x": 0, "y": 0}),
]


@pytest.mark.parametrize("code,state", CORPUS)
def test_agrees_with_interpreter_on_defined_programs(code, state):
    program = parse(code)
    expected = Interpreter().execute(program, dict(state))
    result = evaluate(program, state)
    assert result.defined and result.state == expected


def test_both_engines_give_up_on_divergence():
    program = parse("begin while 1 = 1 do skip end")
    with pytest.raises(RuntimeError, match="iteration limit"):
        Interpreter(max_iterations=5).execute(program)
    result = evaluate(program, max_iterations=5)
    assert not result.defined and result.reason == "iteration_limit"


def test_or_is_strict_unlike_the_short_circuit_interpreter():
    program = parse("begin if x > 0 or y > 0 then r := 1 else r := 0 end")
    assert Interpreter().execute(program, {"x": 1})["r"] == 1
    result = evaluate(program, {"x": 1})
    assert result.status == "undefined" and result.reason == "unassigned_variable"


def test_unassigned_variable_is_undefined_not_an_error():
    result, events = run("begin x := y + 1 end")
    assert result.status == EvaluationResult.UNDEFINED
    assert result.state is None and result.reason == "unassigned_variable"
    assert "'y'" in result.message
    assert events[-1]["event"] == "eval_end" and events[-1]["status"] == "undefined"
    assert events[-1]["state"] is None
    assert "NS_Stm_As" not in rules(events)


def test_iteration_limit_gives_undefined_with_partial_trace():
    result, events = run("begin while x > 0 do x := x + 1 end", {"x": 1}, max_iterations=3)
    assert result.reason == "iteration_limit" and not result.defined
    assert events[-1]["reason"] == "iteration_limit"
    assert [e["iteration"] for e in events if e["event"] == "loop_check"] == [0, 1, 2, 3]


def test_step_limit_gives_undefined():
    result, events = run("begin while 1 = 1 do skip end", max_steps=10)
    assert result.reason == "step_limit" and result.steps == 10
    assert len(rules(events)) == 10


def test_result_to_dict_and_repr():
    ok = evaluate(build_term(parse("begin x := 1 end")))
    bad = evaluate(build_term(parse("begin x := y end")))
    assert ok.to_dict() == {"status": "defined", "state": {"x": 1}, "reason": None, "message": None, "steps": 2}
    assert bad.to_dict()["reason"] == "unassigned_variable"
    assert "defined" in repr(ok) and "undefined" in repr(bad)


def test_sipl_semantic_error_fields():
    exc = SIPLSemanticError("why", "because")
    assert exc.reason == "why" and exc.message == "because" and str(exc) == "because"


def test_evaluate_accepts_ast_and_rejects_junk():
    assert evaluate(Program(SkipStmt())).defined
    with pytest.raises(RuntimeError, match="No semantic rule"):
        evaluate(None)


def test_malformed_terms_raise_runtime_error():
    with pytest.raises(RuntimeError, match="Unsupported function: 'div'"):
        evaluate(Assign("x", Apply("div", (Const(1), Const(2)))))
    with pytest.raises(RuntimeError, match="only defined for two integer"):
        evaluate(Assign("x", Apply("add", (Const(1), Apply("eq", (Const(1), Const(1)))))))
    with pytest.raises(RuntimeError, match="only defined for two boolean"):
        evaluate(Assign("x", Apply("or", (Const(1), Const(2)))))
    with pytest.raises(RuntimeError, match="only defined for one boolean"):
        evaluate(Assign("x", Apply("neg", (Const(1),))))
    with pytest.raises(RuntimeError, match="Cannot assign non-integer"):
        evaluate(Assign("x", Apply("eq", (Const(1), Const(1)))))
    with pytest.raises(RuntimeError, match="IF term must evaluate to a boolean"):
        evaluate(If(Const(1), Id(), Id()))
    with pytest.raises(RuntimeError, match="WH term must evaluate to a boolean"):
        evaluate(While(Const(1), Id()))


def test_error_still_reports_end_event():
    observer = SemanticTraceObserver()
    with pytest.raises(RuntimeError):
        evaluate(If(Const(1), Id(), Id()), observer=observer)
    assert observer.events[-1]["event"] == "eval_end"
    assert observer.events[-1]["status"] == "error"


def test_hand_built_apply_without_rule_gets_default_rule():
    observer = SemanticTraceObserver()
    evaluate(Assign("x", Apply("add", (Const(1), Const(2)))), observer=observer)
    assert "NS_A_Add" in rules(observer.events)


def test_initial_state_validation_and_constructor_limits():
    term = build_term(parse("begin skip end"))
    with pytest.raises(RuntimeError, match="Initial state must be a dictionary"):
        evaluate(term, (0, 0))
    with pytest.raises(RuntimeError, match="must have an integer value"):
        evaluate(term, {"x": True})
    with pytest.raises(RuntimeError, match="non-empty string"):
        evaluate(term, {" ": 0})
    with pytest.raises(RuntimeError, match="Invalid max_steps"):
        TermEvaluator(max_steps=0)
    with pytest.raises(RuntimeError, match="Invalid max_iterations"):
        TermEvaluator(max_iterations=-1)
    assert evaluate(term, max_steps=None, max_iterations=None).defined


def test_input_state_is_not_mutated_and_event_states_are_snapshots():
    state = {"x": 1}
    result, events = run("begin x := x + 1; x := x + 1 end", state)
    assert state == {"x": 1} and result.state == {"x": 3}
    assigns = [e for e in events if e.get("rule") == "NS_Stm_As"]
    assert [a["state_after"]["x"] for a in assigns] == [2, 3]
    assert assigns[0]["state_before"] == {"x": 1}


def test_trace_is_json_serialisable_and_resets_between_runs():
    observer = SemanticTraceObserver()
    evaluator = TermEvaluator(observer=observer)
    term = build_term(parse("begin x := 1 end"))
    evaluator.evaluate(term)
    evaluator.evaluate(term)
    assert [e["event"] for e in observer.events].count("eval_start") == 1
    assert json.loads(observer.to_json())[0]["event"] == "eval_start"
    assert observer.to_list() is observer.events


def test_base_observer_and_detach_and_partial_observers():
    base = SemanticObserver()
    base.on_eval_start(None, {})
    base.on_rule_applied(1, 0, "NS_Stm_skip", "stmt", None, {}, {}, None)
    base.on_loop_iteration(0, None, 0, True, {})
    base.on_eval_end("defined", 1, {})

    class OnlyEnd:
        def __init__(self):
            self.status = None

        def on_eval_end(self, status, *args, **kwargs):
            self.status = status

    only_end, trace = OnlyEnd(), SemanticTraceObserver()
    evaluator = TermEvaluator(observer=only_end)
    evaluator.attach_observer(trace)
    evaluator.evaluate(Id())
    assert only_end.status == "defined" and trace.events
    evaluator.detach_observer(trace)
    evaluator.detach_observer(trace)
    trace.events = []
    evaluator.evaluate(Paren(Id()))
    assert trace.events == []