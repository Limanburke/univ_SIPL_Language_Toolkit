class Term:
    def __init__(self, rule=None, span=None):
        self.rule = rule
        self.span = span

    def children(self):
        return ()

    def __str__(self):
        raise NotImplementedError

    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        result = {"type": type(self).__name__, "rule": self.rule}
        for key, value in vars(self).items():
            if key not in ("rule", "span"):
                if isinstance(value, Term):
                    result[key] = value.to_dict()
                elif isinstance(value, (list, tuple)):
                    result[key] = [v.to_dict() if isinstance(v, Term) else v for v in value]
                else:
                    result[key] = value
        result["span"] = self.span.to_dict() if self.span else None
        return result


class Id(Term):
    def __init__(self, span=None):
        super().__init__(rule="NS_Stm_skip", span=span)

    def __str__(self):
        return "id"

    def __eq__(self, other):
        if type(other) is not type(self):
            return NotImplemented
        return True


class Const(Term):
    def __init__(self, value, span=None):
        super().__init__(rule="NS_A_Num", span=span)
        self.value = int(value)

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        if type(other) is not type(self):
            return NotImplemented
        return self.value == other.value


class Name(Term):
    def __init__(self, name, span=None):
        super().__init__(rule="NS_A_Var", span=span)
        self.name = str(name)

    def __str__(self):
        return f"{self.name}=>"

    def __eq__(self, other):
        if type(other) is not type(self):
            return NotImplemented
        return self.name == other.name


class Apply(Term):
    def __init__(self, func, args, rule=None, span=None):
        super().__init__(rule=rule, span=span)
        self.func = str(func)
        self.args = tuple(args)

    def children(self):
        return self.args

    def __str__(self):
        inner = ", ".join([self.func] + [str(arg) for arg in self.args])
        return f"S^{len(self.args)}({inner})"

    def __eq__(self, other):
        if type(other) is not type(self):
            return NotImplemented
        return self.func == other.func and self.args == other.args


class Assign(Term):
    def __init__(self, var, arg, span=None):
        super().__init__(rule="NS_Stm_As", span=span)
        self.var = str(var)
        self.arg = arg

    def children(self):
        return self.arg,

    def __str__(self):
        return f"AS^{self.var}({self.arg})"

    def __eq__(self, other):
        if type(other) is not type(self):
            return NotImplemented
        return self.var == other.var and self.arg == other.arg


class Comp(Term):
    def __init__(self, left, right, span=None):
        super().__init__(rule="NS_Stm_Seq", span=span)
        self.left = left
        self.right = right

    def children(self):
        return self.left, self.right

    def __str__(self):
        return f"{self.left} . {self.right}"

    def __eq__(self, other):
        if type(other) is not type(self):
            return NotImplemented
        return self.left == other.left and self.right == other.right


class If(Term):
    def __init__(self, cond, then_action, else_action, span=None):
        super().__init__(rule="NS_Stm_If", span=span)
        self.cond = cond
        self.then_action = then_action
        self.else_action = else_action

    def children(self):
        return self.cond, self.then_action, self.else_action

    def __str__(self):
        return f"IF({self.cond}, {self.then_action}, {self.else_action})"

    def __eq__(self, other):
        if type(other) is not type(self):
            return NotImplemented
        return (
            self.cond == other.cond
            and self.then_action == other.then_action
            and self.else_action == other.else_action
        )


class While(Term):
    def __init__(self, condition, do_action, span=None):
        super().__init__(rule="NS_Stm_Wh", span=span)
        self.condition = condition
        self.do_action = do_action

    def children(self):
        return self.condition, self.do_action

    def __str__(self):
        return f"WH({self.condition}, {self.do_action})"

    def __eq__(self, other):
        if type(other) is not type(self):
            return NotImplemented
        return self.condition == other.condition and self.do_action == other.do_action


class Paren(Term):
    def __init__(self, body, span=None):
        super().__init__(rule="NS_Stm_BE", span=span)
        self.body = body

    def children(self):
        return self.body,

    def __str__(self):
        return f"({self.body})"

    def __eq__(self, other):
        if type(other) is not type(self):
            return NotImplemented
        return self.body == other.body