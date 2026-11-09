class Visitor:
    def visit(self, node):
        method_name = f"visit_{node.__class__.__name__.lower()}"
        visitor_method = getattr(self, method_name, self.generic_visit)
        return visitor_method(node)

    def generic_visit(self, node):
        raise RuntimeError(f"No visit_{node.__class__.__name__.lower()} method defined for AST node")