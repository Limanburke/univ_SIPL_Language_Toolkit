from src.sipl.visitor import Visitor
from src.sipl.semantics.terms import (Id, Const, Name, Apply, Assign, Comp, If, While, Paren)

class SemanticTermBuilder(Visitor):
    def generic_visit(self, node):
        raise RuntimeError(f"No semantic rule defined for AST node {node.__class__.__name__}")

    def visit_program(self, node):
        return self.visit(node.statement)

    def visit_assignstmt(self, node):
        return Assign(node.var, self.visit(node.expression), span=node.span)

    def visit_seqstmt(self, node):
        return Comp(self.visit(node.left), self.visit(node.right), span=node.span)

    def visit_ifstmt(self, node):
        return If(
            self.visit(node.condition),
            self.visit(node.then_action),
            self.visit(node.else_action),
            span=node.span,
        )

    def visit_whilestmt(self, node):
        return While(self.visit(node.condition), self.visit(node.do_action), span=node.span)

    def visit_blockstmt(self, node):
        return Paren(self.visit(node.body), span=node.span)

    @staticmethod
    def visit_skipstmt(node):
        return Id(span=node.span)

    @staticmethod
    def visit_number(node):
        return Const(node.value, span=node.span)

    @staticmethod
    def visit_variable(node):
        return Name(node.name, span=node.span)

    def visit_binaryoperation(self, node):
        left_term = self.visit(node.left)
        right_term = self.visit(node.right)

        if node.op == "+":
            return Apply("add", (left_term, right_term), rule="NS_A_Add", span=node.span)
        elif node.op == "-":
            return Apply("sub", (left_term, right_term), rule="NS_A_Sub", span=node.span)
        elif node.op == "*":
            return Apply("mult", (left_term, right_term), rule="NS_A_Mult", span=node.span)
        else:
            raise RuntimeError(f"Unsupported binary operator: '{node.op}'")

    def visit_compareoperation(self, node):
        left_term = self.visit(node.left)
        right_term = self.visit(node.right)

        if node.op == "=":
            return Apply("eq", (left_term, right_term), rule="NS_B_eq", span=node.span)
        elif node.op == ">":
            return Apply("gr", (left_term, right_term), rule="NS_B_gr", span=node.span)
        else:
            raise RuntimeError(f"Unsupported comparison operator: '{node.op}'")

    def visit_logicalornode(self, node):
        return Apply(
            "or",
            (self.visit(node.left), self.visit(node.right)),
            rule="NS_B_or",
            span=node.span,
        )

    def visit_notnode(self, node):
        target = getattr(node, "expression", None)
        return Apply(
            "neg",
            (self.visit(target),),
            rule="NS_B_neg",
            span=node.span,
        )

def build_term(node):
    return SemanticTermBuilder().visit(node)