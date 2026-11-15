def with_location(message, span):
    if span is None or getattr(span, "start_line", None) is None:
        return message
    return f"{message} at line {span.start_line}, column {span.start_column}"


class SIPLRuntimeError(RuntimeError):
    def __init__(self, message, span=None):
        super().__init__(with_location(message, span))
        self.span = span
        self.line = span.start_line if span is not None else None
        self.column = span.start_column if span is not None else None