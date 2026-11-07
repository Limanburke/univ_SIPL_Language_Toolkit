import json

class TraceObserver:
    def on_execution_start(self, program, state):
        pass

    def on_before_stmt(self, step, stmt_type, span, state):
        pass

    def on_after_stmt(self, step, stmt_type, state):
        pass

    def on_variable_change(self, step, var_name, old_val, new_val, state):
        pass

    def on_condition_eval(self, step, context, span, result, state):
        pass

    def on_execution_end(self, step, status, state, error=None):
        pass


class ExecutionTraceObserver(TraceObserver):
    def __init__(self):
        self.events = []

    @staticmethod
    def _span(span):
        return span.to_dict() if span is not None and hasattr(span, "to_dict") else None

    def on_execution_start(self, program, state):
        self.events = []
        self.events.append({
            "event": "execution_start",
            "state": state.copy(),
        })

    def on_before_stmt(self, step, stmt_type, span, state):
        self.events.append({
            "event": "before_stmt",
            "step": step,
            "stmt": stmt_type,
            "span": self._span(span),
            "state": state.copy(),
        })

    def on_after_stmt(self, step, stmt_type, state):
        self.events.append({
            "event": "after_stmt",
            "step": step,
            "stmt": stmt_type,
            "state": state.copy(),
        })

    def on_variable_change(self, step, var_name, old_val, new_val, state):
        self.events.append({
            "event": "variable_change",
            "step": step,
            "var": var_name,
            "old_val": old_val,
            "new_val": new_val,
            "state": state.copy(),
        })

    def on_condition_eval(self, step, context, span, result, state):
        self.events.append({
            "event": "condition_eval",
            "step": step,
            "context": context,
            "span": self._span(span),
            "result": result,
            "state": state.copy(),
        })

    def on_execution_end(self, step, status, state, error=None):
        self.events.append({
            "event": "execution_end",
            "step": step,
            "status": status,
            "error": error,
            "final_state": state.copy(),
        })

    def to_list(self):
        return self.events

    def to_json(self, indent: int = 2):
        return json.dumps(self.events, indent=indent, ensure_ascii=False)