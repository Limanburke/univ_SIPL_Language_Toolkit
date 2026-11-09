import argparse
import json
import sys
from pathlib import Path
from src.sipl.interpreter.interpreter import Interpreter
from src.sipl.observer import ExecutionTraceObserver
from src.sipl.parser import SIPLSyntaxError, parse
from src.sipl.semantics.builder import build_term

HIDDEN_STMTS = {"SeqStmt", "BlockStmt"}

SCHEMA_VERSION = 1

EXIT_SUCCESS = 0
EXIT_RUNTIME_ERROR = 1
EXIT_USAGE_ERROR = 2
EXIT_SYNTAX_ERROR = 3

def read_source(filepath):
    path = Path(filepath)
    return path.read_text(encoding="utf-8-sig")

def snippet(source, span, limit = 60):
    if not span or span.get("start_position") is None:
        return ""
    text = " ".join(source[span["start_position"]:span["end_position"]].split())
    return text if len(text) <= limit else text[:limit - 3] + "..."

def parse_initial_state(var_assignments):
    if not var_assignments:
        return None

    state = {}
    for item in var_assignments:
        name, separator, value_str = item.partition("=")
        var_name = name.strip()
        if not separator or not var_name:
            raise ValueError(f"Invalid variable assignment '{item}', expected NAME=INTEGER")
        try:
            state[var_name] = int(value_str)
        except ValueError:
            raise ValueError(f"Variable '{var_name}' value must be an integer, got '{value_str}'")

    return state


def format_trace(events: list, source: str) -> str:
    lines = []
    depth = 0
    hidden_steps = set()

    for e in events:
        kind = e["event"]
        pad = "  " * depth

        if kind == "execution_start":
            lines.append(f"start  state={e['state']}")

        elif kind == "before_stmt":
            if e["stmt"] in HIDDEN_STMTS:
                hidden_steps.add(e["step"])
                continue
            span = e.get("span")
            where = f"  (line {span['start_line']})" if span else ""
            snip = snippet(source, span)
            lines.append(f"{pad}#{e['step']} {e['stmt']}: {snip}{where}")
            depth += 1

        elif kind == "after_stmt":
            if e["step"] not in hidden_steps:
                depth = max(depth - 1, 0)

        elif kind == "variable_change":
            old = "unset" if e["old_val"] is None else e["old_val"]
            lines.append(f"{pad}{e['var']}: {old} -> {e['new_val']}")

        elif kind == "condition_eval":
            cond = snippet(source, e.get("span"))
            lines.append(f"{pad}{e['context']} condition `{cond}` is {e['result']}")

        elif kind == "execution_end":
            tail = f" - {e['error']}" if e.get("error") else ""
            lines.append(f"end: {e['status']}{tail}  state={e['final_state']}")

    return "\n".join(lines)


def handle_trace(args):
    code = read_source(args.file)
    prog = parse(code)
    initial_vars = parse_initial_state(args.var)

    observer = ExecutionTraceObserver()
    interp = Interpreter(
        observer=observer,
        max_steps=args.max_steps,
        max_iterations=args.max_iterations,
    )

    exit_code = EXIT_SUCCESS
    try:
        interp.execute(prog, initial_state=initial_vars)
    except RuntimeError:
        exit_code = EXIT_RUNTIME_ERROR

    events = observer.to_list()
    last_status = events[-1]["status"] if events else "unknown"
    payload = {"status": last_status, "events": events}

    text_view = format_trace(events, code)

    return payload, text_view, exit_code


def output_result(args, payload, plain_text, is_error = False):
    if args.json:
        data = {"schema_version": SCHEMA_VERSION}
        data.update(payload)
        print(json.dumps(data, ensure_ascii=False))
    else:
        stream = sys.stderr if is_error else sys.stdout
        print(plain_text, file=stream)


def handle_parse(args):
    code = read_source(args.file)
    prog = parse(code)
    return {"status": "ok", "ast": prog.to_dict()}, repr(prog), EXIT_SUCCESS


def handle_check(args):
    code = read_source(args.file)
    parse(code)
    return {"status": "ok"}, "Syntax OK", EXIT_SUCCESS


def handle_run(args):
    code = read_source(args.file)
    prog = parse(code)
    initial_vars = parse_initial_state(args.var)

    interp = Interpreter(max_steps=args.max_steps, max_iterations=args.max_iterations)
    final_state = interp.execute(prog, initial_state=initial_vars)

    lines = [f"{var} = {val}" for var, val in sorted(final_state.items())]
    return {"status": "completed", "state": final_state}, "\n".join(lines), EXIT_SUCCESS


def handle_term(args):
    code = read_source(args.file)
    prog = parse(code)
    term = build_term(prog)
    text_view = str(term)
    payload = {
        "status": "ok",
        "notation": text_view,
        "term": term.to_dict(),
    }
    return payload, text_view, EXIT_SUCCESS


def create_cli_parser():
    parser = argparse.ArgumentParser(
        prog="sipl",
        description="Command line interface",
    )

    base_args = argparse.ArgumentParser(add_help=False)
    base_args.add_argument("file", help="Path to .sipl script")
    base_args.add_argument("--json", action="store_true", help="Output result as JSON")

    runtime_args = argparse.ArgumentParser(add_help=False)
    runtime_args.add_argument("--var", action="append", metavar="NAME=INT", help="Initial variable value")
    runtime_args.add_argument("--max-steps", type=int, default=1_000_000, help="Global step execution limit")
    runtime_args.add_argument("--max-iterations", type=int, default=100_000, help="Loop iteration limit")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("parse", parents=[base_args], help="Parse and show AST").set_defaults(handler=handle_parse)
    subparsers.add_parser("check", parents=[base_args], help="Validate syntax").set_defaults(handler=handle_check)
    subparsers.add_parser("run", parents=[base_args, runtime_args], help="Execute program").set_defaults(handler=handle_run)
    subparsers.add_parser("trace", parents=[base_args, runtime_args], help="Execute and show trace").set_defaults(handler=handle_trace)
    subparsers.add_parser("term", parents=[base_args], help="Build and show semantic term").set_defaults(handler=handle_term)

    return parser


def main(argv=None):
    parser = create_cli_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code

    try:
        payload, text_view, exit_code = args.handler(args)
    except SIPLSyntaxError as err:
        error_payload = {
            "status": "syntax_error",
            "error": err.message,
            "line": err.line,
            "column": err.column,
        }
        output_result(args, error_payload, err.message, is_error=True)
        return EXIT_SYNTAX_ERROR
    except (RuntimeError, OSError, ValueError) as err:
        output_result(args,{
                          "status": "error",
                          "error": str(err)
                      },f"Error: {err}", is_error=True)
        return EXIT_RUNTIME_ERROR

    output_result(args, payload, text_view)
    return exit_code