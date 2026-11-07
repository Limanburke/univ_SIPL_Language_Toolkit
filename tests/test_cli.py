import json
import subprocess
import sys
from pathlib import Path
from src.sipl.cli import main

ROOT = Path(__file__).resolve().parent.parent


def write_file(tmp_path, code, name="prog.sipl"):
    file_path = tmp_path / name
    file_path.write_text(code, encoding="utf-8")
    return str(file_path)


def run_cli_json(capsys, argv):
    exit_code = main(argv + ["--json"])
    captured = capsys.readouterr()
    return exit_code, json.loads(captured.out)


def test_parse_json_is_structured(tmp_path, capsys):
    f = write_file(tmp_path, "begin x := 10 end")
    code, data = run_cli_json(capsys, ["parse", f])

    assert code == 0
    assert data["schema_version"] == 1
    assert data["status"] == "ok"
    assert data["ast"]["type"] == "Program"
    assert data["ast"]["statement"]["var"] == "x"
    assert data["ast"]["statement"]["expression"]["value"] == 10


def test_parse_text(tmp_path, capsys):
    f = write_file(tmp_path, "begin skip end")
    assert main(["parse", f]) == 0
    captured = capsys.readouterr()
    assert "Program" in captured.out


def test_check_ok_and_syntax_error(tmp_path, capsys):
    good_f = write_file(tmp_path, "begin skip end")
    assert main(["check", good_f]) == 0
    assert "Syntax OK" in capsys.readouterr().out

    bad_f = write_file(tmp_path, "begin x := end", name="bad.sipl")

    code, data = run_cli_json(capsys, ["check", bad_f])
    assert code == 3
    assert data["status"] == "syntax_error"
    assert data["line"] == 1
    assert data["column"] is not None

    assert main(["check", bad_f]) == 3
    assert "Syntax error" in capsys.readouterr().err


def test_run_with_vars(tmp_path, capsys):
    f = write_file(tmp_path, "begin y := x + 10 end")

    code, data = run_cli_json(capsys, ["run", f, "--var", "x=5"])
    assert code == 0
    assert data["status"] == "completed"
    assert data["state"] == {"x": 5, "y": 15}

    assert main(["run", f, "--var", "x=5"]) == 0
    assert "y = 15" in capsys.readouterr().out


def test_run_runtime_error(tmp_path, capsys):
    f = write_file(tmp_path, "begin x := undef end")

    code, data = run_cli_json(capsys, ["run", f])
    assert code == 1
    assert data["status"] == "error"

    assert main(["run", f]) == 1
    assert "Error:" in capsys.readouterr().err


def test_trace_success(tmp_path, capsys):
    f = write_file(tmp_path, "begin while x > 0 do x := x - 1 end")

    code, data = run_cli_json(capsys, ["trace", f, "--var", "x=2"])
    assert code == 0
    assert data["status"] == "completed"
    event_names = [e["event"] for e in data["events"]]
    assert event_names[0] == "execution_start"
    assert event_names[-1] == "execution_end"

    assert main(["trace", f, "--var", "x=1"]) == 0
    out = capsys.readouterr().out
    assert "WhileStmt: while x > 0 do x := x - 1" in out
    assert "x: 1 -> 0" in out
    assert "while condition `x > 0` is False" in out


def test_trace_failure_keeps_trace_and_exit_code(tmp_path, capsys):
    f = write_file(tmp_path, "begin while 1 = 1 do skip end")
    code, data = run_cli_json(capsys, ["trace", f, "--max-iterations", "3"])

    assert code == 1
    assert data["status"] == "failed_iteration_limit"
    assert data["events"][-1]["event"] == "execution_end"


def test_invalid_var_and_missing_file_and_usage(tmp_path, capsys):
    f = write_file(tmp_path, "begin skip end")

    assert main(["run", f, "--var", "x"]) == 1
    assert main(["run", f, "--var", "x=abc"]) == 1

    assert main(["check", "non_existent_file.sipl"]) == 1

    capsys.readouterr()
    assert main([]) == 2
    assert main(["unknown_command"]) == 2


def test_file_with_bom(tmp_path, capsys):
    bom_file = tmp_path / "bom.sipl"
    bom_file.write_bytes(b"\xef\xbb\xbfbegin skip end")
    assert main(["check", str(bom_file)]) == 0


def test_module_entry_point(tmp_path):
    f = write_file(tmp_path, "begin y := x + 1 end")
    proc = subprocess.run(
        [sys.executable, "-m", "src.sipl", "run", f, "--var", "x=2", "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert json.loads(proc.stdout)["state"] == {"x": 2, "y": 3}

def test_text_trace_hides_structural_nodes_and_shows_error(tmp_path, capsys):
    f = write_file(tmp_path, "begin x := 1; y := 2 end")
    assert main(["trace", f]) == 0
    out = capsys.readouterr().out
    assert "SeqStmt" not in out
    assert "x: unset -> 1" in out and "y: unset -> 2" in out

    loop_file = write_file(tmp_path, "begin while 1 = 1 do skip end", name="loop.sipl")
    assert main(["trace", loop_file, "--max-iterations", "2"]) == 1
    assert "end: failed_iteration_limit" in capsys.readouterr().out

def test_snippet_limit_and_empty():
    from src.sipl.cli import snippet
    assert snippet("x := 1", None) == ""
    assert snippet("x := 1", {}) == ""
    long_code = "x := " + "1" * 100
    span = {"start_position": 0, "end_position": len(long_code)}
    res = snippet(long_code, span, limit=20)
    assert len(res) == 20
    assert res.endswith("...")