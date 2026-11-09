import json
import pytest
from src.sipl.parser import parse
from src.sipl.interpreter.interpreter import Interpreter
from src.sipl.observer import TraceObserver, ExecutionTraceObserver


def test_base_observer_empty_methods():
    obs = TraceObserver()
    obs.on_execution_start(None, {})
    obs.on_before_stmt(1, "SkipStmt", None, {})
    obs.on_after_stmt(1, "SkipStmt", {})
    obs.on_variable_change(1, "x", None, 1, {"x": 1})
    obs.on_condition_eval(1, "if", None, True, {})
    obs.on_execution_end(1, "completed", {}, None)


def test_trace_simple_assignment_and_json():
    observer = ExecutionTraceObserver()
    interp = Interpreter(observer=observer)
    prog = parse("begin x := 10 end")
    interp.execute(prog)

    events = observer.to_list()
    event_names = [e["event"] for e in events]
    assert event_names == [
        "execution_start",
        "before_stmt",
        "variable_change",
        "after_stmt",
        "execution_end"
    ]

    var_change = events[2]
    assert var_change["var"] == "x"
    assert var_change["old_val"] is None
    assert var_change["new_val"] == 10
    assert var_change["state"] == {"x": 10}

    json_str = observer.to_json()
    parsed = json.loads(json_str)
    assert isinstance(parsed, list)
    assert len(parsed) == 5
    assert parsed[-1]["status"] == "completed"


def test_before_after_step_ids_match():
    obs = ExecutionTraceObserver()
    Interpreter(observer=obs).execute(parse("begin x := 1; y := 2 end"))
    stack, pairs = [], 0
    for e in obs.events:
        if e["event"] == "before_stmt":
            stack.append(e["step"])
        elif e["event"] == "after_stmt":
            assert stack.pop() == e["step"]
            pairs += 1
    assert stack == [] and pairs == 3


def test_trace_if_statement_branching():
    obs = ExecutionTraceObserver()
    interp = Interpreter()
    interp.attach_observer(obs)

    code = "begin if x > 0 then y := 1 else y := 2 end"
    interp.execute(parse(code), initial_state={"x": 5})

    events = obs.to_list()
    cond_events = [e for e in events if e["event"] == "condition_eval"]
    assert len(cond_events) == 1
    assert cond_events[0]["context"] == "if"
    assert cond_events[0]["result"] is True
    assert cond_events[0]["span"] is not None
    span = cond_events[0]["span"]
    assert code[span["start_position"]:span["end_position"]] == "x > 0"


def test_while_condition_events_share_loop_step():
    obs = ExecutionTraceObserver()
    Interpreter(observer=obs).execute(parse("begin while x > 0 do x := x - 1 end"),
                                      initial_state={"x": 2})
    cond_events = [e for e in obs.events if e["event"] == "condition_eval"]
    assert len(cond_events) == 3
    assert [c["result"] for c in cond_events] == [True, True, False]
    steps = {e["step"] for e in cond_events}
    assert steps == {1}


def test_observer_reset_between_runs():
    obs = ExecutionTraceObserver()
    interp = Interpreter(observer=obs)
    prog = parse("begin x := 1 end")
    interp.execute(prog)
    interp.execute(prog)
    assert [e["event"] for e in obs.events].count("execution_start") == 1


def test_detach_observer():
    obs = ExecutionTraceObserver()
    interp = Interpreter(observer=obs)
    interp.detach_observer(obs)
    interp.execute(parse("begin skip end"))
    assert obs.events == []


def test_trace_execution_failure_events():
    obs1 = ExecutionTraceObserver()
    interp1 = Interpreter(max_steps=5, observer=obs1)
    with pytest.raises(RuntimeError, match="maximum step limit"):
        interp1.execute(parse("begin while 1 = 1 do skip end"))
    assert obs1.events[-1]["event"] == "execution_end"
    assert obs1.events[-1]["status"] == "failed_step_limit"

    obs2 = ExecutionTraceObserver()
    interp2 = Interpreter(max_iterations=3, observer=obs2)
    with pytest.raises(RuntimeError, match="loop iteration limit"):
        interp2.execute(parse("begin while 1 = 1 do skip end"))
    assert obs2.events[-1]["event"] == "execution_end"
    assert obs2.events[-1]["status"] == "failed_iteration_limit"

    obs3 = ExecutionTraceObserver()
    interp3 = Interpreter(observer=obs3)
    with pytest.raises(RuntimeError, match="referenced before assignment"):
        interp3.execute(parse("begin x := undef + 1 end"))
    assert obs3.events[-1]["event"] == "execution_end"
    assert obs3.events[-1]["status"] == "error"