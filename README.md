Course Project for the Academic Discipline "Theory of Programming"

Selected modules

| ID          | Module                                                                        | Points   | Status   |
|:------------|:------------------------------------------------------------------------------|:--------:|:--------:|
| **CORE-01** | Formal SIPL grammar specification & positive/negative test suites             |   0.5    |   Done   |
| **CORE-02** | Parser and typed AST with source positions                                    |   1.5    |   Done   |
| **CORE-03** | Deterministic interpreter with loop iteration and step limits                 |   2.0    |   Done   |
| **CORE-04** | Event-driven execution trace observer & state snapshots                       |   1.0    |   Done   |
| **CORE-05** | Unified CLI (`check`, `parse`, `run`, `trace`, `term`, `eval`) with JSON mode |   1.0    |   Done   |
| **SEM-01**  | Automated AST-to-term conversion in ASCII form of the course notation         |   2.0    |   Done   |
| **SEM-02**  | Term evaluation on memory state, $NS_*$ rule transitions & diagnostics        |   2.0    |   Done   |

Total points: 10/10

---

## Language

- **Keywords**: `begin`, `end`, `if`, `then`, `else`, `while`, `do`, `skip`, `or`, `not`.
- **Identifiers**: an ASCII letter (`A-Z`, `a-z`) or `_` followed by ASCII letters, digits, or `_` (keywords excluded).
- **Integers**: optional `-` followed by digits.
- **Operators & Punctuation**: `:=`, `;`, `+`, `-`, `*`, `=`, `>`, and parentheses `(...)`.
- **Formal Grammar**: `grammar/grammar.lark`.

---

## Installation & Testing
Requirements (Tested on Python 3.14):

```bash
# Create and activate a virtual environment (recommended)
python -m venv venv
# Windows (PowerShell):
venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate
```

```bash
# Clone the repository and install dependencies
pip install -r requirements.txt

# Run the test suite with coverage report
pytest -v --cov=src/sipl --cov-report=term-missing
```
---
## CLI
Run via Python module entry point:
```bash
python -m src.sipl <command> <file.sipl> [options]
```

### Commands

| Command   | Description                                        | Example                                                     |
|-----------|----------------------------------------------------|-------------------------------------------------------------|
| `check`   | Validate source code syntax                        | `python -m src.sipl check examples/01_power.sipl`           |
| `parse`   | Output parsed typed AST representation             | `python -m src.sipl parse examples/01_power.sipl`           |
| `run`     | Execute program via AST interpreter                | `python -m src.sipl run examples/01_power.sipl --var X=1`   |
| `trace`   | Execute program and print statement/state trace    | `python -m src.sipl trace examples/01_power.sipl --var X=1` |
| `term`    | Build the semantic term (ASCII course notation)    | `python -m src.sipl term examples/01_power.sipl`            |
| `eval`    | Evaluate semantic term step-by-step ($NS_*$ rules) | `python -m src.sipl eval examples/01_power.sipl --var X=1`  |

### Flags

* `--var NAME=INT`: Initialize variable state (can be specified multiple times; for `run`, `trace`, `eval`).
* `--max-steps N`: Global evaluation/execution step limit (default: 1000000; for `run`, `trace`, `eval`).
* `--max-iterations N`: Loop iteration limit (default: 100000; for `run`, `trace`, `eval`).
* `--no-trace`: Suppress rule trace, printing only the final result (for `eval`).
* `--json`: Emit structured JSON output (schema_version: 1; available for all commands).

### Exit Codes

| Code   | Name                 | Description                                                          |
|--------|----------------------|----------------------------------------------------------------------|
| **0**  | `EXIT_SUCCESS`       | Success / evaluation defined                                         |
| **1**  | `EXIT_RUNTIME_ERROR` | Runtime error / invalid types / OS failure                           |
| **2**  | `EXIT_USAGE_ERROR`   | Invalid command line (unknown command, missing or invalid arguments) |
| **3**  | `EXIT_SYNTAX_ERROR`  | Parsing syntax error with source coordinates                         |
| **4**  | `EXIT_UNDEFINED`     | Semantic term is undefined on the given state                        |

### JSON Output

Every JSON object contains schema_version (1) and status.

| Command   | `status` values                                                     | Other fields                                                                                                     |
|-----------|---------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------|
| `parse`   | `ok`                                                                | `ast`                                                                                                            |
| `check`   | `ok`                                                                |                                                                                                                  |
| `run`     | `completed`                                                         | `state`                                                                                                          |
| `trace`   | `completed`, `failed_step_limit`, `failed_iteration_limit`, `error` | `events`                                                                                                         |
| `term`    | `ok`                                                                | `notation`, `term`                                                                                               |
| `eval`    | `defined`, `undefined`                                              | `term`, `state`, `reason`, `message`, `steps`, `span` (`null` when defined), `events` (absent with `--no-trace`) |
| errors    | `syntax_error`, `error`                                             | `error`; `line`, `column` (for `syntax_error` and runtime errors with a known position)                          |

Trace events: `execution_start`, `before_stmt`, `after_stmt`, `variable_change`, `condition_eval`, `execution_end` (`trace`); `eval_start`, `rule_applied`, `loop_check`, `eval_end` (`eval`).

---

## Semantic Rules

| Substitution Rule                                                                                           | Rule ID       | Code Representation    |
|-------------------------------------------------------------------------------------------------------------|---------------|------------------------|
| $sem\_S(x := a) = AS^x(sem\_A(a))$                                                                          | `NS_Stm_As`   | `AS^x(...)`            |
| $sem\_S(S_1; S_2) = sem\_S(S_1) \cdot sem\_S(S_2)$                                                          | `NS_Stm_Seq`  | `t1 . t2`              |
| $sem\_S(\text{if } b \text{ then } S_1 \text{ else } S_2) = \text{IF}(sem\_B(b), sem\_S(S_1), sem\_S(S_2))$ | `NS_Stm_If`   | `IF(cond, then, else)` |
| $sem\_S(\text{while } b \text{ do } S) = \text{WH}(sem\_B(b), sem\_S(S))$                                   | `NS_Stm_Wh`   | `WH(cond, do)`         |
| $sem\_S(\text{begin } S \text{ end}) = (sem\_S(S))$                                                         | `NS_Stm_BE`   | `(...)`                |
| $sem\_S(\text{skip}) = \text{id}$                                                                           | `NS_Stm_skip` | `id`                   |
| $sem\_A(n) = \overline{n}$                                                                                  | `NS_A_Num`    | `n`                    |
| $sem\_A(x) = x\Rightarrow$                                                                                  | `NS_A_Var`    | `x=>`                  |
| $sem\_A(a_1 + a_2) = S^2(\text{add}, sem\_A(a_1), sem\_A(a_2))$                                             | `NS_A_Add`    | `S^2(add, ...)`        |
| $sem\_A(a_1 - a_2) = S^2(\text{sub}, sem\_A(a_1), sem\_A(a_2))$                                             | `NS_A_Sub`    | `S^2(sub, ...)`        |
| $sem\_A(a_1 * a_2) = S^2(\text{mult}, sem\_A(a_1), sem\_A(a_2))$                                            | `NS_A_Mult`   | `S^2(mult, ...)`       |
| $sem\_B(a_1 = a_2) = S^2(\text{eq}, sem\_A(a_1), sem\_A(a_2))$                                              | `NS_B_eq`     | `S^2(eq, ...)`         |
| $sem\_B(a_1 > a_2) = S^2(\text{gr}, sem\_A(a_1), sem\_A(a_2))$                                              | `NS_B_gr`     | `S^2(gr, ...)`         |
| $sem\_B(b_1 \lor b_2) = S^2(\text{or}, sem\_B(b_1), sem\_B(b_2))$                                           | `NS_B_or`     | `S^2(or, ...)`         |
| $sem\_B(\neg b) = S^1(\text{neg}, sem\_B(b))$                                                               | `NS_B_neg`    | `S^1(neg, ...)`        |

### Undefinedness

When a semantic term cannot be evaluated to a state, `eval` exits with code 4 and prints the reason:

* `unassigned_variable`: Accessing a variable not present in state.
* `iteration_limit`: Loop iteration count exceeded `--max-iterations`.
* `step_limit`: Global rule derivation count exceeded `--max-steps`.

---

## Included Examples

* **`01_power.sipl`**: Computes $5^X$ for $X \ge 1$ via iterative multiplication.
* **`02_gcd.sipl`**: Euclidean subtraction algorithm computing $\gcd(M, N)$.
* **`03_fibo.sipl`**: Computes the $N$-th Fibonacci number with sequential assignments.

---

## Notes

- The AST interpreter uses short-circuit evaluation for `or`.
- The semantic evaluator follows strict superposition semantics: both operands of $S^2(or, b_1, b_2)$ must be defined. Unlike the AST interpreter, it does not skip the second operand when the first evaluates to `true`. If an operand is undefined, the entire condition is undefined.
- `--max-steps` counts visited statement AST nodes (including sequence and block nodes) for `run`/`trace`, and individual semantic term evaluations (including subexpressions) for `eval`. Therefore, the limits are not directly interchangeable.
- Parentheses in arithmetic expressions and conditions do not produce separate AST or semantic term nodes. The parser preserves their source span on the inner node, while the semantic term builder treats them as identity wrappers.
- Reaching `iteration_limit` or `step_limit` only means the evaluation did not finish within the given bounds. It does not prove that the program diverges (halting problem).