class SourceSpan:
    def __init__(self, start_line: int, start_column: int, end_line: int, end_column: int,
                 start_position: int = None, end_position: int = None):
        self.start_line = start_line
        self.start_column = start_column
        self.end_line = end_line
        self.end_column = end_column
        self.start_position = start_position
        self.end_position = end_position

    def __repr__(self):
        return (f"SourceSpan(line={self.start_line}:{self.start_column}.."
                f"column={self.end_line}:{self.end_column}, pos={self.start_position}..{self.end_position})")

    def __eq__(self, other):
        if not isinstance(other, SourceSpan):
            return NotImplemented
        return (self.start_line == other.start_line and
                self.start_column == other.start_column and
                self.end_line == other.end_line and
                self.end_column == other.end_column and
                self.start_position == other.start_position and
                self.end_position == other.end_position)


class Node:
    def __init__(self, span=None):
        self.span = span

    def __repr__(self):
        return f"Node(span={self.span})"


class Number(Node):
    def __init__(self, value, span=None):
        super().__init__(span)
        self.value = int(value)

    def __repr__(self):
        return f"Number(value={self.value}, span={self.span})"

    def __eq__(self, other):
        if type(other) is not type(self):
            return NotImplemented
        return self.value == other.value


class Variable(Node):
    def __init__(self, name, span=None):
        super().__init__(span)
        self.name = str(name)

    def __repr__(self):
        return f"Variable(name='{self.name}', span={self.span})"

    def __eq__(self, other):
        if type(other) is not type(self):
            return NotImplemented
        return self.name == other.name


class BinaryOperation(Node):
    def __init__(self, left, op, right, span=None):
        super().__init__(span)
        self.left = left
        self.op = str(op)
        self.right = right

    def __repr__(self):
        return f"BinaryOperation(left={self.left}, op='{self.op}', right={self.right}, span={self.span})"

    def __eq__(self, other):
        if type(other) is not type(self):
            return NotImplemented
        return (self.left == other.left and
                self.op == other.op and
                self.right == other.right)


class CompareOperation(Node):
    def __init__(self, op, left, right, span=None):
        super().__init__(span)
        self.op = str(op)
        self.left = left
        self.right = right

    def __repr__(self):
        return f"CompareOperation(left={self.left}, op='{self.op}', right={self.right}, span={self.span})"

    def __eq__(self, other):
        if type(other) is not type(self):
            return NotImplemented
        return (self.left == other.left and
                self.op == other.op and
                self.right == other.right)


class LogicalOrNode(Node):
    def __init__(self, left, right, span=None):
        super().__init__(span)
        self.left = left
        self.right = right

    def __repr__(self):
        return f"LogicalOrNode(left={self.left}, right={self.right}, span={self.span})"

    def __eq__(self, other):
        if type(other) is not type(self):
            return NotImplemented
        return (self.left == other.left and
                self.right == other.right)


class NotNode(Node):
    def __init__(self, expression, span=None):
        super().__init__(span)
        self.expression = expression

    def __repr__(self):
        return f"NotNode(expression={self.expression}, span={self.span})"

    def __eq__(self, other):
        if type(other) is not type(self):
            return NotImplemented
        return self.expression == other.expression


class AssignStmt(Node):
    def __init__(self, var, expression, span=None):
        super().__init__(span)
        self.var = str(var)
        self.expression = expression

    def __repr__(self):
        return f"AssignStmt(var='{self.var}', expr={self.expression}, span={self.span})"

    def __eq__(self, other):
        if type(other) is not type(self):
            return NotImplemented
        return (self.var == other.var and
                self.expression == other.expression)


class SeqStmt(Node):
    def __init__(self, left, right, span=None):
        super().__init__(span)
        self.left = left
        self.right = right

    def __repr__(self):
        return f"SeqStmt(left={self.left}, right={self.right}, span={self.span})"

    def __eq__(self, other):
        if type(other) is not type(self):
            return NotImplemented
        return (self.left == other.left and
                self.right == other.right)


class IfStmt(Node):
    def __init__(self, condition, then_action, else_action, span=None):
        super().__init__(span)
        self.condition = condition
        self.then_action = then_action
        self.else_action = else_action

    def __repr__(self):
        return f"IfStmt(condition={self.condition}, then_action={self.then_action}, else_action={self.else_action}, span={self.span})"

    def __eq__(self, other):
        if type(other) is not type(self):
            return NotImplemented
        return (self.condition == other.condition and
                self.then_action == other.then_action and
                self.else_action == other.else_action)


class WhileStmt(Node):
    def __init__(self, condition, do_action, span=None):
        super().__init__(span)
        self.condition = condition
        self.do_action = do_action

    def __repr__(self):
        return f"WhileStmt(condition={self.condition}, do_action={self.do_action}, span={self.span})"

    def __eq__(self, other):
        if type(other) is not type(self):
            return NotImplemented
        return (self.condition == other.condition and
                self.do_action == other.do_action)


class BlockStmt(Node):
    def __init__(self, body, span=None):
        super().__init__(span)
        self.body = body

    def __repr__(self):
        return f"BlockStmt(body={self.body}, span={self.span})"

    def __eq__(self, other):
        if type(other) is not type(self):
            return NotImplemented
        return self.body == other.body


class SkipStmt(Node):
    def __init__(self, span=None):
        super().__init__(span)

    def __repr__(self):
        return f"SkipStmt(span={self.span})"

    def __eq__(self, other):
        if type(other) is not type(self):
            return NotImplemented
        return True


class Program(Node):
    def __init__(self, statement, span=None):
        super().__init__(span)
        self.statement = statement

    def __repr__(self):
        return f"Program(statement={self.statement}, span={self.span})"

    def __eq__(self, other):
        if type(other) is not type(self):
            return NotImplemented
        return self.statement == other.statement