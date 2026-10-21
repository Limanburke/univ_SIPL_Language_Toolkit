from src.sipl.ast import Program

class Visitor:
    def visit(self, node):
        method_name = f"visit_{node.__class__.__name__.lower()}"
        visitor_method = getattr(self, method_name, self.generic_visit)
        return visitor_method(node)

    def generic_visit(self, node):
        raise RuntimeError(f"No visit_{node.__class__.__name__.lower()} method defined for AST node")


class Interpreter(Visitor):
    def __init__(self, max_steps=1_000_000, max_iterations=100_000):
        if max_steps is not None and (type(max_steps) is not int or max_steps <= 0):
            raise RuntimeError(f"Invalid max_steps: expected a positive integer or None, got {max_steps}")
        if max_iterations is not None and (type(max_iterations) is not int or max_iterations <= 0):
            raise RuntimeError(f"Invalid max_iterations: expected a positive integer or None, got {max_iterations}")

        self.max_steps = max_steps
        self.max_iterations = max_iterations
        self.steps = 0
        self.state = {}

    def visit(self, node):
        if node.__class__.__name__.endswith("Stmt"):
            self.steps += 1
            if self.max_steps is not None and self.steps > self.max_steps:
                raise RuntimeError(f"Execution exceeded maximum step limit ({self.max_steps})")
        return super().visit(node)

    @staticmethod
    def _validate_initial_state(initial_state):
        if initial_state is None:
            return {}

        if not isinstance(initial_state, dict):
            raise RuntimeError(f"Initial state must be a dictionary, got {type(initial_state).__name__}")

        validated_state = {}
        for var_name, value in initial_state.items():
            if not isinstance(var_name, str) or not var_name.strip():
                raise RuntimeError(f"Variable name in state must be a non-empty string, got {var_name}")

            if type(value) is not int:
                raise RuntimeError(f"Variable '{var_name}' must have an integer value, got {value} of type {type(value).__name__}")
            validated_state[var_name] = value
        return validated_state

    @staticmethod
    def visit_number(node):
        return node.value

    def visit_variable(self, node):
        if node.name not in self.state:
            raise RuntimeError(f"Variable '{node.name}' is referenced before assignment")
        return self.state[node.name]

    def visit_binaryoperation(self, node):
        left_val = self.visit(node.left)
        right_val = self.visit(node.right)

        if type(left_val) is not int or type(right_val) is not int:
            raise RuntimeError("Arithmetic operations are only defined for integer values")

        if node.op == "+":
            return left_val + right_val
        elif node.op == "-":
            return left_val - right_val
        elif node.op == "*":
            return left_val * right_val
        else:
            raise RuntimeError(f"Unsupported binary operator: '{node.op}'")

    def visit_compareoperation(self, node):
        left_val = self.visit(node.left)
        right_val = self.visit(node.right)

        if node.op == "=":
            return left_val == right_val
        elif node.op == ">":
            return left_val > right_val
        else:
            raise RuntimeError(f"Unsupported comparison operator: '{node.op}'")

    def visit_logicalornode(self, node):
        return self.visit(node.left) or self.visit(node.right)

    def visit_notnode(self, node):
        target = getattr(node, "expression", None)
        return not self.visit(target)

    def visit_assignstmt(self, node):
        val = self.visit(node.expression)
        if type(val) is not int:
            raise RuntimeError(f"Cannot assign non-integer value to variable '{node.var}'")
        self.state[node.var] = val

    def visit_seqstmt(self, node):
        self.visit(node.left)
        self.visit(node.right)

    def visit_ifstmt(self, node):
        cond = self.visit(node.condition)
        if type(cond) is not bool:
            raise RuntimeError("The condition of an if-statement must evaluate to a boolean")

        if cond:
            self.visit(node.then_action)
        else:
            self.visit(node.else_action)

    def visit_whilestmt(self, node):
        iteration = 0
        while True:
            cond = self.visit(node.condition)
            if type(cond) is not bool:
                raise RuntimeError("The condition of a while-statement must evaluate to a boolean")
            if not cond:
                break

            iteration += 1
            if self.max_iterations is not None and iteration > self.max_iterations:
                raise RuntimeError(f"Execution exceeded loop iteration limit ({self.max_iterations})")

            self.visit(node.do_action)

    def visit_blockstmt(self, node):
        self.visit(node.body)

    def visit_skipstmt(self, _node):
        pass

    def visit_program(self, node):
        self.visit(node.statement)

    def execute(self, program, initial_state=None):
        if not isinstance(program, Program):
            raise RuntimeError(f"Expected a Program AST node, got {type(program).__name__}")

        self.state = self._validate_initial_state(initial_state)
        self.steps = 0
        self.visit(program)
        return self.state