import json

class SemanticObserver:
    def on_eval_start(self, term, state):
        pass

    def on_rule_applied(self, step, depth, rule, kind, term, state_before, state_after, value):
        pass

    def on_loop_iteration(self, depth, term, iteration, condition, state):
        pass

    def on_eval_end(self, status, steps, state, reason=None, message=None):
        pass


class SemanticTraceObserver(SemanticObserver):
    def __init__(self):
        self.events = []

    @staticmethod
    def _span(term):
        span = getattr(term, "span", None)
        return span.to_dict() if span is not None and hasattr(span, "to_dict") else None

    def on_eval_start(self, term, state):
        self.events = []
        self.events.append({
            "event": "eval_start",
            "term": str(term),
            "state": state.copy()
        })

    def on_rule_applied(self, step, depth, rule, kind, term, state_before, state_after, value):
        event = {
            "event": "rule_applied",
            "step": step,
            "depth": depth,
            "rule": rule,
            "kind": kind,
            "term": str(term),
            "span": self._span(term),
            "state_before": state_before.copy()
        }
        if kind == "stmt":
            event["state_after"] = state_after.copy()
        else:
            event["value"] = value
        self.events.append(event)

    def on_loop_iteration(self, depth, term, iteration, condition, state):
        self.events.append({
            "event": "loop_check",
            "depth": depth,
            "rule": term.rule,
            "iteration": iteration,
            "condition": condition,
            "state": state.copy()
        })

    def on_eval_end(self, status, steps, state, reason=None, message=None):
        self.events.append({
            "event": "eval_end",
            "status": status,
            "steps": steps,
            "reason": reason,
            "message": message,
            "state": None if state is None else state.copy()
        })

    def to_list(self):
        return self.events

    def to_json(self, indent: int = 2):
        return json.dumps(self.events, indent=indent, ensure_ascii=False)