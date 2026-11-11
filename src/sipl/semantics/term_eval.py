from src.sipl.semantics.builder import build_term
from src.sipl.semantics.terms import Term, Id, Assign, Comp, If, While, Paren
from src.sipl.visitor import Visitor


class SIPLSemanticError(Exception):
    def __init__(self, reason, message):
        super().__init__(message)
        self.reason = reason
        self.message = message


class EvaluationResult:
    DEFINED = "defined"
    UNDEFINED = "undefined"

    def __init__(self, status, state=None, reason=None, message=None, steps=0):
        self.status = status
        self.state = state
        self.reason = reason
        self.message = message
        self.steps = steps
        self.defined = (status == self.DEFINED)

    def to_dict(self):
        return {
            "status": self.status,
            "state": self.state,
            "reason": self.reason,
            "message": self.message,
            "steps": self.steps
        }

    def __repr__(self):
        if self.defined:
            return f"EvaluationResult(defined, state={self.state}, steps={self.steps})"
        return f"EvaluationResult(undefined, reason={self.reason}, steps={self.steps})"


class TermEvaluator(Visitor):
    def __init__(self, observer=None, max_steps=1000000, max_iterations=100000):
        if max_steps is not None and (type(max_steps) is not int or max_steps <= 0):
            raise RuntimeError(f"Invalid max_steps: expected a positive integer or None, got {max_steps}")
        if max_iterations is not None and (type(max_iterations) is not int or max_iterations <= 0):
            raise RuntimeError(f"Invalid max_iterations: expected a positive integer or None, got {max_iterations}")

        self.max_steps = max_steps
        self.max_iterations = max_iterations
        self.steps = 0
        self.state = {}
        self._depth = 0
        self._observers = []
        if observer is not None:
            self.attach_observer(observer)

    def attach_observer(self, observer):
        self._observers.append(observer)

    def detach_observer(self, observer):
        if observer in self._observers:
            self._observers.remove(observer)

    def _notify(self, method, *args, **kwargs):
        for observer in self._observers:
            func = getattr(observer, method, None)
            if func is not None:
                func(*args, **kwargs)

    @staticmethod
    def _kind(term):
        if isinstance(term, (Id, Assign, Comp, If, While, Paren)):
            return "stmt"
        func = getattr(term, "func", None)
        if func in ("eq", "gr", "or", "neg"):
            return "bexp"
        return "aexp"

    @staticmethod
    def _rule_of(term):
        if term.rule:
            return term.rule

        func = getattr(term, "func", None)
        if func == "add":
            return "NS_A_Add"
        elif func == "sub":
            return "NS_A_Sub"
        elif func == "mult":
            return "NS_A_Mult"
        elif func == "eq":
            return "NS_B_eq"
        elif func == "gr":
            return "NS_B_gr"
        elif func == "or":
            return "NS_B_or"
        elif func == "neg":
            return "NS_B_neg"
        return None

    def visit(self, term):
        depth = self._depth
        state_before = self.state.copy()
        self._depth += 1
        try:
            value = super().visit(term)
        finally:
            self._depth -= 1

        if self.max_steps is not None and self.steps >= self.max_steps:
            raise SIPLSemanticError("step_limit", f"Evaluation exceeded maximum step limit ({self.max_steps})")
        self.steps += 1

        self._notify(
            "on_rule_applied",
            self.steps,
            depth,
            self._rule_of(term),
            self._kind(term),
            term,
            state_before,
            self.state,
            value
        )
        return value

    @staticmethod
    def _validate_initial_state(initial_state):
        if initial_state is None:
            return {}
        if not isinstance(initial_state, dict):
            raise RuntimeError(f"Initial state must be a dictionary, got {type(initial_state).__name__}")

        validated = {}
        for name, value in initial_state.items():
            if not isinstance(name, str) or not name.strip():
                raise RuntimeError(f"Variable name in state must be a non-empty string, got {name}")
            if type(value) is not int:
                raise RuntimeError(
                    f"Variable '{name}' must have an integer value, got {value} of type {type(value).__name__}"
                )
            validated[name] = value
        return validated

    @staticmethod
    def visit_const(term):
        return term.value

    def visit_name(self, term):
        if term.name not in self.state:
            raise SIPLSemanticError("unassigned_variable", f"Variable '{term.name}' is not assigned in the state")
        return self.state[term.name]

    def visit_apply(self, term):
        args = [self.visit(arg) for arg in term.args]
        func = term.func

        if func in ("add", "sub", "mult", "eq", "gr"):
            if len(args) != 2 or type(args[0]) is not int or type(args[1]) is not int:
                raise RuntimeError(f"Function '{func}' is only defined for two integer values")
            if func == "add":
                return args[0] + args[1]
            elif func == "sub":
                return args[0] - args[1]
            elif func == "mult":
                return args[0] * args[1]
            elif func == "eq":
                return args[0] == args[1]
            else:
                return args[0] > args[1]

        elif func == "or":
            if len(args) != 2 or type(args[0]) is not bool or type(args[1]) is not bool:
                raise RuntimeError("Function 'or' is only defined for two boolean values")
            return args[0] or args[1]

        elif func == "neg":
            if len(args) != 1 or type(args[0]) is not bool:
                raise RuntimeError("Function 'neg' is only defined for one boolean value")
            return not args[0]

        else:
            raise RuntimeError(f"Unsupported function: '{func}'")

    def visit_id(self, _term):
        pass

    def visit_assign(self, term):
        value = self.visit(term.arg)
        if type(value) is not int:
            raise RuntimeError(f"Cannot assign non-integer value to variable '{term.var}'")
        self.state = self.state.copy()
        self.state[term.var] = value

    def visit_comp(self, term):
        self.visit(term.left)
        self.visit(term.right)

    def visit_if(self, term):
        cond = self.visit(term.cond)
        if type(cond) is not bool:
            raise RuntimeError("The condition of an IF term must evaluate to a boolean")
        if cond:
            self.visit(term.then_action)
        else:
            self.visit(term.else_action)

    def visit_while(self, term):
        iteration = 0
        while True:
            cond = self.visit(term.condition)
            if type(cond) is not bool:
                raise RuntimeError("The condition of a WH term must evaluate to a boolean")
            self._notify("on_loop_iteration", self._depth, term, iteration, cond, self.state)
            if not cond:
                break

            iteration += 1
            if self.max_iterations is not None and iteration > self.max_iterations:
                raise SIPLSemanticError(
                    "iteration_limit",
                    f"Loop did not terminate within {self.max_iterations} iterations"
                )
            self.visit(term.do_action)

    def visit_paren(self, term):
        self.visit(term.body)

    def evaluate(self, term, initial_state=None):
        if not isinstance(term, Term):
            term = build_term(term)

        self.state = self._validate_initial_state(initial_state)
        self.steps = 0
        self._depth = 0
        self._notify("on_eval_start", term, self.state)

        status = "error"
        reason = None
        message = None
        try:
            self.visit(term)
            result = EvaluationResult(EvaluationResult.DEFINED, self.state.copy(), steps=self.steps)
            status = result.status
        except SIPLSemanticError as undefined:
            result = EvaluationResult(
                EvaluationResult.UNDEFINED,
                None,
                undefined.reason,
                undefined.message,
                self.steps
            )
            status = result.status
            reason = result.reason
            message = result.message
        except RuntimeError as exc:
            reason = "error"
            message = str(exc)
            raise
        finally:
            final_st = self.state if status == "defined" else None
            self._notify("on_eval_end", status, self.steps, final_st, reason, message)

        return result


def evaluate(term, initial_state=None, observer=None, max_steps=1000000, max_iterations=100000):
    return TermEvaluator(observer, max_steps, max_iterations).evaluate(term, initial_state)