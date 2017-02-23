#
# This file contains the AST typer of the Tiger project.
# It must not be modified.
#

import sys

from ast.nodes import *
from utils.visitor import *


class TypeException(Exception):
    pass


class Typer(Visitor):
    """Assign types to all the nodes in the AST.

    The nodes are put in cliques where all the nodes must have the same type
    (including nodes for the `int` and `void` types themselves).

    If two Type nodes are put in a clique, they must refer to the same type
    or an error will be raised: this corresponds to incorrectly typed
    expressions.

    If the `run` method of the Typer is used, additional checks are ran
    after the visitor has walked the tree:
      - If variables are of a `void` type, an error is raised.
      - If some types are undetermined, an error is raised if the result
        is assigned to a variable. Otherwise, a warning is printed if
        the `warn` parameter is set to True.

    The latter case may happen when recursive functions are used and there
    could be polymorphic over their type. For example

      let
        function f() = f()
        var a := f()
      in
        a
      end

    In this case, `f` could as well be a function returning `int` or a
    function returning `void`. In practice, this is of little importance
    as its return value cannot be used, and we might as well consider
    it void."""

    # List of type names that can be declared in Tiger code.
    declarable_types = ['int']

    def __init__(self):
        self.int_type = Type('int')
        self.void_type = Type('void')
        self.cliques = {self.int_type: [self.int_type],
                        self.void_type: [self.void_type]}

    def run(self, ast, warn):
        """Run the typer over the AST and check that no variable declaration
        resolves to void. Optionally warn about undefined types on stderr."""
        ast.accept(self)
        for n in self.cliques[self.void_type]:
            if isinstance(n, VarDecl):
                raise TypeException('var %s cannot be void' % n.name)
        for n in self.cliques:
            if n.type is None:
                n.type = self.void_type
                if isinstance(n, VarDecl):
                    raise TypeException('type of var %s cannot be determined' %
                                    n.name)
                elif warn and isinstance(n, FunDecl):
                    sys.stderr.write("Warning: could not determine type "
                                     "for %s\n" % n.name)

    def merge(self, node1, node2):
        """Merge two cliques. If it contains one type, the nodes get assigned
        the type. If it contains two types, it raises an error if they do not
        designate the same type."""
        # If one of the node is None, return
        if node1 is None or node2 is None:
            return
        # If either node is not in a clique, put it in a clique of its own to
        # avoid special casing later.
        if node1 not in self.cliques:
            self.cliques[node1] = [node1]
        if node2 not in self.cliques:
            self.cliques[node2] = [node2]
        clique1 = self.cliques[node1]
        clique2 = self.cliques[node2]
        # If both nodes are in the same clique, return
        if clique1 is clique2:
            return
        # Merge the clique of node2 into the clique of node1
        del self.cliques[node2]
        clique1.extend(clique2)
        for n in clique2:
            self.cliques[n] = clique1
        typenames = list(set([n.typename for n in clique1
                              if isinstance(n, Type)]))
        if len(typenames) == 1:
            for n in clique1:
                self.assign_type(n, typenames[0])
        elif len(typenames) > 1:
            raise TypeException('incompatible types: %s' % typenames)

    def assign_type(self, node, typename):
        """Assign a type to a node if it has none or if it is compatible."""
        if node.type is None:
            node.type = Type(typename)

    @visitor(IntegerLiteral)
    def visit(self, n):
        self.merge(n, self.int_type)

    @visitor(Identifier)
    def visit(self, i):
        assert i.decl is not None, \
          "no declaration for identifier %s" % i
        self.merge(i, i.decl)

    @visitor(Type)
    def visit(self, t):
        assert t.typename in self.declarable_types, \
            "type %s is unknown" % t.typename

    @visitor(VarDecl)
    def visit(self, decl):
        self.visit_all(decl.children)
        self.merge(decl, decl.type)
        self.merge(decl, decl.exp)
        self.merge(decl.type, decl.exp)

    @visitor(FunDecl)
    def visit(self, decl):
        self.visit_all(decl.children)
        self.merge(decl, decl.type)
        self.merge(decl, decl.exp)

    @visitor(FunCall)
    def visit(self, call):
        self.visit_all(call.children)
        decl = call.identifier.decl
        self.merge(call, decl)
        for (a, p) in zip(decl.args, call.params):
            self.merge(a, p)

    @visitor(BinaryOperator)
    def visit(self, binop):
        self.visit_all(binop.children)
        self.merge(binop, self.int_type)
        self.merge(binop.left, self.int_type)
        self.merge(binop.left, binop.right)

    @visitor(Let)
    def visit(self, let):
        self.visit_all(let.children)
        if let.exps:
            self.merge(let, let.exps[-1])
        else:
            self.merge(let, self.void_type)

    @visitor(IfThenElse)
    def visit(self, ite):
        self.visit_all(ite.children)
        self.merge(ite.condition, self.int_type)
        self.merge(ite, ite.then_part)
        self.merge(ite, ite.else_part if ite.else_part else self.void_type)

    @visitor(SeqExp)
    def visit(self, seq):
        self.visit_all(seq.children)
        self.merge(seq, seq.exps[-1] if seq.exps else self.void_type)

    @visitor(While)
    def visit(self, w):
        self.visit_all(w.children)
        self.merge(w.condition, self.int_type)
        self.merge(w.exp, self.void_type)

    @visitor(For)
    def visit(self, f):
        self.visit_all(f.children)
        self.merge(f, self.void_type)
        self.merge(f.indexdecl, self.int_type)
        self.merge(f.indexdecl, f.low_bound)
        self.merge(f.indexdecl, f.high_bound)
        self.merge(f.exp, self.void_type)

    @visitor(Break)
    def visit(self, b):
        self.merge(b, self.void_type)

    @visitor(Assignment)
    def visit(self, a):
        self.visit_all(a.children)
        self.merge(a.identifier, a.exp)
        self.merge(a, self.void_type)
