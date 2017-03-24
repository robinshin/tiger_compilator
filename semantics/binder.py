from ast.nodes import *
from utils.visitor import *


class BindException(Exception):
    """Exception encountered during the binding phase."""
    pass


class Binder(Visitor):
    """The binder takes care of linking identifier uses to its declaration. If
    will also remember the depth of every declaration and every identifier,
    and mark a declaration as escaping if it is accessed from a greater depth
    than its definition.

    A new scope is pushed every time a let, function declaration or for loop is
    encountered. It is not allowed to have the same name present several
    times in the same scope.

    The depth is increased every time a function declaration is encountered,
    and restored afterwards.

    A loop node for break is pushed every time we start a for or while loop.
    Pushing None means that we are outside of break scope, which happens in the
    declarations part of a let."""

    def __init__(self):
        """Create a new binder with an initial scope for top-level
        declarations."""
        self.depth = 0
        self.scopes = []
        self.push_new_scope()
        self.break_stack = [None]

    def push_new_scope(self):
        """Push a new scope on the scopes stack."""
        self.scopes.append({})

    def pop_scope(self):
        """Pop a scope from the scopes stack."""
        del self.scopes[-1]

    def current_scope(self):
        """Return the current scope."""
        return self.scopes[-1]

    def push_new_loop(self, loop):
        """Push a new loop node on the break stack."""
        self.break_stack.append(loop)

    def pop_loop(self):
        """Pop a loop node from the break stack."""
        del self.break_stack[-1]

    def current_loop(self):
        loop = self.break_stack[-1]
        if loop is None:
            raise BindException("break called outside of loop")
        return loop

    def add_binding(self, decl):
        """Add a binding to the current scope and set the depth for
        this declaration. If the name already exists, an exception
        will be raised."""
        if decl.name in self.current_scope():
            raise BindException("name already defined in scope: %s" %
                                decl.name)
        self.current_scope()[decl.name] = decl
        decl.depth = self.depth

    def lookup(self, identifier):
        """Return the declaration associated with a identifier, looking
        into the closest scope first. If no declaration is found,
        raise an exception. If it is found, the decl and depth field
        for this identifier are set, and the escapes field of the
        declaration is updated if needed."""
        name = identifier.name
        for scope in reversed(self.scopes):
            if name in scope:
                decl = scope[name]
                identifier.decl = decl
                identifier.depth = self.depth
                decl.escapes |= self.depth > decl.depth
                return decl
        else:
            raise BindException("name not found: %s" % name)

    @visitor(None)
    def visit(self, node):
        raise BindException("unable to bind %s" % node)

    @visitor(IntegerLiteral)
    def visit(self, i):
        pass

    @visitor(BinaryOperator)
    def visit(self, binop):
        binop.left.accept(self)
        binop.right.accept(self)

    @visitor(Let)
    def visit(self, let):
        self.push_new_scope()
        for decl in let.decls:
            decl.accept(self)
        for expr in let.exps:
            expr.accept(self)
        self.pop_scope()
   
    @visitor(Identifier)
    def visit(self, id):
        decl = self.lookup(id)
        if isinstance(decl, FunDecl):
            raise BindException("Function name cannot be used as a variable name")

    @visitor(IfThenElse)
    def visit(self, ifthenelse):
        ifthenelse.condition.accept(self)
        ifthenelse.then_part.accept(self)
        if ifthenelse.else_part is not None:
            ifthenelse.else_part.accept(self)

    @visitor(VarDecl)
    def visit(self, vardecl):
        if vardecl.exp != None:
            vardecl.exp.accept(self)
        self.add_binding(vardecl)

    @visitor(FunDecl)
    def visit(self, func):
        self.add_binding(func)
        self.push_new_scope()
        self.depth += 1
        for arg in func.args:
            self.add_binding(arg)
        func.exp.accept(self)
        self.depth -= 1
        self.pop_scope()

    @visitor(FunCall)
    def visit(self, func):
        fundecl = self.lookup(func.identifier)
        if isinstance(fundecl, FunDecl):
            if len(fundecl.args) != len(func.params):
                raise BindException("Wrong number of parameters")
            for param in func.params:
                param.accept(self)
        else:
            raise BindException("Function identifier unknown")

    @visitor(SeqExp)
    def visit(self, exprs):
        for exp in exprs.exps:
            exp.accept(self)

    @visitor(Assignment)
    def visit(self, ass):
        decl = self.lookup(ass.identifier)
        if not isinstance(decl, VarDecl):
            raise BindException("Affected variable must be a VarDecl type")
        ass.exp.accept(self)
