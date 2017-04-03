from ast.nodes import *
from frame.frame import *
from ir.nodes import *
from utils.visitor import *

class Shell:
    """Wrap an IR tree into a wrapper which can be unwrapped later.
    This allows deferring the translation of an expression or a
    statement to a later step."""

    def unCx(self, ifTrue, ifFalse):
        """Transform this wrapper into a conditional jump exception (or,
        in some cases where the result can be determined, into an
        inconditionnal jump). The result is a Stm."""
        raise AssertionError("unimplemented")

    def unEx(self):
        """Transform this wrapper into an expression whose value
        can then be used (a Sxp)."""
        raise AssertionError("unimplemented")

    def unNx(self):
        """Transform this wrapper into a statement whose result will not
        be used (a Stm)."""
        raise AssertionError("unimplemented")

    def is_known_const(self):
        """Return the integer value of a known CONST node or None if
        the node does not evaluate to an integer at compile time."""
        return None

    def is_known_true(self):
        """Check if the value is a compile-time True."""
        c = self.is_known_const()
        return c is not None and c

    def is_known_false(self):
        """Check if the value is a compile-time False."""
        return self.is_known_const() == 0


class Cx(Shell):
    """Wrap a comparaison operator."""

    def __init__(self, frame, op, left, right):
        assert isinstance(op, str), "op must be a string"
        assert op in logical_operators, "op must be a logical operator"
        assert isinstance(left, Shell), "left must be a Shell"
        assert isinstance(right, Shell), "right must be a Shell"
        self.frame = frame
        self.op = op
        self.left = left
        self.right = right

    def unCx(self, ifTrue, ifFalse):
        assert isinstance(ifTrue, Sxp), "ifTrue must be a Sxp"
        assert isinstance(ifFalse, Sxp), "ifFalse must be a Sxp"
        return CJUMP(self.op, self.left.unEx(), self.right.unEx(),
                     ifTrue, ifFalse)

    def unEx(self):
        return Ix(self.frame, self, Ex(CONST(1)), Ex(CONST(0))).unEx()

    def unNx(self):
        return SEQ([self.left.unNx(), self.right.unNx()])


class Ex(Shell):
    """Wrap an expression."""

    def __init__(self, sxp):
        """Wrap a `Sxp` node."""
        assert isinstance(sxp, Sxp), "sxp must be a Sxp"
        self.sxp = sxp

    def unCx(self, ifTrue, ifFalse):
        assert isinstance(ifTrue, Sxp), "ifTrue must be a Sxp"
        assert isinstance(ifFalse, Sxp), "ifFalse must be a Sxp"
        # If the expression is a known constant, directly jump to the
        # right label instead of generating a conditional jump.
        if self.is_known_true():
            return JUMP(ifTrue)
        if self.is_known_false():
            return JUMP(ifFalse)
        # Compare the result of the expression to 0.
        return CJUMP('<>', self.sxp, CONST(0), ifTrue, ifFalse)

    def unEx(self):
        return self.sxp

    def unNx(self):
        return SXP(self.sxp)

    def is_known_const(self):
        return self.sxp.value if isinstance(self.sxp, CONST) else None


class Ix(Shell):
    """Wrap a conditional jump statement in order to chain them easily."""

    def __init__(self, frame, test, thenClause, elseClause):
        """Represents if test then thenClause else elseClause
        with a possible empty elseClause."""
        assert isinstance(frame, Frame), "frame must be a Frame"
        assert isinstance(test, Shell), "test must be a Shell"
        assert isinstance(thenClause, Shell), "thenClause must be a Shell"
        assert elseClause is None or isinstance(elseClause, Shell), \
            "elseClause must be a Shell or None"
        self.frame = frame
        self.test = test
        self.thenClause = thenClause
        self.elseClause = elseClause

    def unCx(self, ifTrue, ifFalse):
        # This unCx clause means:
        #
        #   if current then jump(ifTrue) else jump(ifFalse)
        #
        # with current being the result of evaluating either thenClause or
        # elseClause depending on the test.
        #
        # We transform it into:
        #   if test
        #     then (if thenClause then jump(ifTrue) else jump(ifFalse))
        #     else (if elseClause then jump(ifTrue) else jump(ifFalse))
        #
        # This prevents evaluating thenClause or elseClause into an integer
        # which must then be compared to 0, and we can used chained conditional
        # jumps in the output.
        #
        # If we did not implement such an expansion, it would look like:
        #
        #  TEMP = if test then thenClause else elseClause
        #  if TEMP then jump(ifTrue) else jump(ifFalse)
        #
        # which requires storing the result of the test in a temporary
        # register, as an integer value, instead of using conditional jumps.
        #
        # Note that this preserves "if" short-circuit semantics: thenClause is
        # only evaluated if the test is true and elseClause is only evaluated
        # if the test is false.
        assert isinstance(ifTrue, Sxp), "ifTrue must be a Sxp"
        assert isinstance(ifFalse, Sxp), "ifFalse must be a Sxp"
        assert self.elseClause is not None, \
            "unable to take the value of a if/then/else without an else clause"
        chained = \
            Ix(self.frame, self.test,
               Nx(self.thenClause.unCx(ifTrue, ifFalse)),
               Nx(self.elseClause.unCx(ifTrue, ifFalse)))
        # Then we return the code corresponding to this chained expression.
        return chained.unNx()

    def unEx(self):
        assert self.elseClause is not None, \
            "unable to take the value of a if/then/else without an else clause"
        # We will evaluate either thenClause or elseClause and put that in a
        # new temporary and then return the value of this temporary:
        #
        # if test
        #   then TEMP = thenClause
        #   else TEMP = elseClause
        # return TEMP
        #
        # In order to do that, we will build a new Ix for the assignment
        # operation and call unNx on it.
        #
        # We first check if the condition is a known constant in
        # which case we only evaluate what is necessary.
        if self.test.is_known_true():
            return self.thenClause.unEx()
        if self.test.is_known_false():
            return self.elseClause.unEx()
        result = TEMP(Temp.create("ifresult"))
        assignment = Ix(self.frame, self.test,
                        Nx(MOVE(result, self.thenClause.unEx())),
                        Nx(MOVE(result, self.elseClause.unEx())))
        return ESEQ(assignment.unNx(), result)

    def unNx(self):
        # Transform this into
        #
        # if test then jump(TRUE) else jump(FALSE)
        # LABEL(FALSE)
        # elseClause
        # jump(JOIN)
        # LABEL(TRUE)
        # thenClause
        # LABEL(JOIN)
        #
        # where TRUE, FALSE, and JOIN are three new labels. If elseClause is
        # None, we will directly jump to JOIN.
        #
        # We first check if the condition is a known constant in
        # which case we only evaluate what is necessary.
        if self.is_known_true():
            return self.thenClause.unNx()
        if self.is_known_false():
            return self.elseClause.unNx() if self.elseClause else SEQ([])
        trueLabel = Label.create(self.frame)
        joinLabel = Label.create(self.frame)
        if self.elseClause is None:
            return SEQ([self.test.unCx(NAME(trueLabel), NAME(joinLabel)),
                        LABEL(trueLabel),
                        self.thenClause.unNx(),
                        LABEL(joinLabel)])
        falseLabel = Label.create(self.frame)
        return SEQ([self.test.unCx(NAME(trueLabel), NAME(falseLabel)),
                    LABEL(falseLabel),
                    self.elseClause.unNx(),
                    JUMP(NAME(joinLabel)),
                    LABEL(trueLabel),
                    self.thenClause.unNx(),
                    LABEL(joinLabel)])

    def is_known_const(self):
        if self.test.is_known_true():
            return self.thenClause.is_known_const()
        if self.test.is_known_false():
            return self.elseClause.is_known_const()
        return None


class Nx(Shell):
    """Wrap a statement. Note that only `unNx` is implemented in this case."""

    def __init__(self, stm):
        """Wrap a `Stm` node."""
        assert isinstance(stm, Stm), "stm must be a Stm"
        self.stm = stm

    def unCx(self, ifTrue, ifFalse):
        raise AssertionError("`unCx` makes no sense on a `Nx`")

    def unEx(self):
        raise AssertionError("`unEx` makes no sense on a `Nx`")

    def unNx(self):
        return self.stm


class Translator(Visitor):
    """Transform an AST into a Shell node."""

    def __init__(self, Frame):
        # Store Frame creator class.
        self.Frame = Frame
        # Map of currently defined functions. Keys are the function
        # expanded names (see visitor for FunDecl), values are the
        # pair (frame, Stm) associated to the function.
        self.functions = {}
        # Stack of frames of functions being analyzed.
        self.frame_stack = []
        # Mapping of all function parameters and variables to Access.
        self.frame_parameters = {}
        # Mapping from function declaration to labels.
        self.labels = {}
        # Mapping from loop nodes to loop labels, used for breaks.
        self.loops = {}

    def run(self, ast):
        """Run the visitor over the ast after wrapping it into a
        main() function declaration and return a dictionary of
        function declarations to pairs of (frame, Stm)."""
        FunDecl('main', [], ast.type, ast).accept(self)
        return self.functions

    def current_frame(self):
        return self.frame_stack[-1]

    @visitor(FunDecl)
    def visit(self, decl):
        # We have a new function declaration. We will create a new frame
        # for this function, add it to the list of function and analyze
        # its content. The name of the label for the function will be
        # computed from the name of the current frame to allow several
        # functions in different scopes to coexist.
        label = self.current_frame().label + decl.name if self.frame_stack \
                else Label(decl.name)
        self.labels[decl] = label
        frame = self.Frame(label)
        self.frame_stack.append(frame)
        # For every argument to this function, allocate an access for
        # this argument into the function frame.
        for arg in decl.args:
            self.frame_parameters[arg] = frame.alloc_parameter(arg.escapes)
        # Analyze the expression for this function and get its Shell.
        body = decl.exp.accept(self)
        # Turn the body into a statement, after putting its result into
        # a register if it returns a value.
        stm = body.unNx() \
            if decl.exp.type is None or decl.exp.type.typename == 'void' \
            else frame.wrap_result(body.unEx())
        # Register the current function into the list of functions and
        # pop the current frame from the frame stack.
        self.functions[decl] = (frame, frame.decorate(stm))
        del self.frame_stack[-1]
        # Nothing has to be built dynamically when a function declaration
        # is encountered.
        return Nx(SEQ([]))

    def decl_to_sxp(self, decl, depth_difference):
        """Return the Sxp corresponding to a given declaration and the
        depth difference."""
        assert depth_difference >= 0, "depth_difference cannot be negative"
        # To locate an identifier, we must first find the static frame
        # into which we have to find it by dereferencing the frame
        # pointer as many time as needed to compensate the depth difference.
        fp = TEMP(self.current_frame().fp)
        for i in range(depth_difference):
            fp = MEM(fp)
        # Then we must locate its position into the frame relative to
        # the static frame pointer.
        return self.frame_parameters[decl].toSxp(fp)

    @visitor(IntegerLiteral)
    def visit(self, i):
        return Ex(CONST(i.intValue))

    @visitor(BinaryOperator)
    def visit(self, binop):
        left = binop.left.accept(self)
        right = binop.right.accept(self)
        # If the result of the binary operation can be evaluated at
        # compile time, do it using the evaluator we built in earlier
        # steps.
        if isinstance(left.unEx(), CONST) and \
           isinstance(right.unEx(), CONST) and \
           (binop.op != '/' or right.unEx().value != 0):
            # Since we have an evaluator, let's use it for this job
            from ast.evaluator import Evaluator
            result = binop.accept(Evaluator())
            return Ex(CONST(result))
        # If this is an operator with shortcut evaluation, transform
        # into embedded ifs.
        if binop.op == '&':
            return Ix(self.current_frame(), left,
                      Ix(self.current_frame(), right,
                         Ex(CONST(1)), Ex(CONST(0))),
                      Ex(CONST(0)))
        if binop.op == '|':
            return Ix(self.current_frame(), left,
                      Ex(CONST(1)),
                      Ix(self.current_frame(), right,
                         Ex(CONST(1)), Ex(CONST(0))))
        # If this is a logical operator, return a Cx Shell, else return
        # an Ex one.
        if binop.op in logical_operators:
            return Cx(self.current_frame(), binop.op, left, right)
        return Ex(BINOP(binop.op, left.unEx(), right.unEx()))

    @visitor(Identifier)
    def visit(self, id):
        return Ex(self.decl_to_sxp(id.decl, id.depth - id.decl.depth))

    @visitor(VarDecl)
    def visit(self, decl):
        var = self.current_frame().alloc(decl.escapes)
        self.frame_parameters[decl] = var
        # If the declaration has an expression, assign it to the newly created
        # variable, or return a no-op (empty sequence).
        if decl.exp:
            return Nx(MOVE(var.toSxp(TEMP(self.current_frame().fp)),
                           decl.exp.accept(self).unEx()))
        return Nx(SEQ([]))

    @visitor(Let)
    def visit(self, let):
        # Collect all the variable declarations then the body expressions
        code = self.visit_all(let.decls + let.exps)
        # If the let expression does not return a value, return a SEQ
        # since no result is expected, otherwise return an ESEQ with the
        # result of its evaluation.
        if let.type == None or let.type.typename == 'void':
            return Nx(SEQ([c.unNx() for c in code]))
        else:
            return Ex(ESEQ(SEQ([c.unNx() for c in code[:-1]]),
                           code[-1].unEx()))

    @visitor(IfThenElse)
    def visit(self, ite):
        return Ix(self.current_frame(),
                  ite.condition.accept(self),
                  ite.then_part.accept(self),
                  ite.else_part.accept(self) if ite.else_part else None)

    @visitor(FunCall)
    def visit(self, funcall):
        # For a function call, we add the current frame pointer (acting as
        # a static link) adjusted for the relative depth of the called
        # function. This will be the first argument of the function. We
        # do not need to do that for an intrinsics function.
        args = [param.accept(self).unEx() for param in funcall.params]
        if isinstance(funcall.identifier.decl.exp, Intrinsics):
            call = CALL(NAME(Label(funcall.identifier.name)), args)
        else:
            name = NAME(self.labels[funcall.identifier.decl])
            # We want to give the function the static link of its enclosing
            # frame. If the call_depth is 0 (the function is immediately
            # inside the current frame), this is the current frame pointer.
            # If it is negative, we need to go up the static link chain
            # as many levels as needed.
            call_depth = \
                funcall.identifier.depth - funcall.identifier.decl.depth
            static_link = TEMP(self.current_frame().fp)
            for i in range(call_depth):
                static_link = MEM(static_link)
            call = CALL(name, [static_link] + args)
        type = funcall.identifier.decl.type
        if type is None or type.typename == 'void':
            call.return_result = False
            return Nx(SXP(call))
        return Ex(call)

    @visitor(SeqExp)
    def visit(self, seq):
        # If the SeqExp contains only one expression, use it directly.
        if len(seq.exps) == 1:
            return seq.exps[0].accept(self)
        # We have either zero or more than one expressions, we will build
        # a SEQ (if the SeqExp returns nothing) or a ESEQ (if it returns
        # something).
        exps = self.visit_all(seq.exps)
        type = seq.exps[-1].type if seq.exps else None
        if type is None or type.typename == 'void':
            return Nx(SEQ([exp.unNx() for exp in exps]))
        # Only the result from the latest expression will be used,
        # after the previous ones have been executed.
        return Ex(ESEQ(SEQ([exp.unNx() for exp in exps[:-1]]),
                       exps[-1].unEx()))

    @visitor(Assignment)
    def visit(self, assign):
        return Nx(MOVE(
            self.decl_to_sxp(assign.identifier.decl,
                             assign.identifier.depth -
                             assign.identifier.decl.depth),
            assign.exp.accept(self).unEx()))

    @visitor(Break)
    def visit(self, b):
        # Jump to the label corresponding to the right loop. This has been
        # determined in the binder.
        return Nx(JUMP(NAME(self.loops[b.loop])))

    @visitor(While)
    def visit(self, w):
        # Store the end loop label, then expand the test and the body.
        endLabel = Label.create(self.current_frame())
        self.loops[w] = endLabel
        testLabel = Label.create(self.current_frame())
        bodyLabel = Label.create(self.current_frame())
        return Nx(SEQ([LABEL(testLabel),
                       w.condition.accept(self).unCx(NAME(bodyLabel),
                                                     NAME(endLabel)),
                       LABEL(bodyLabel),
                       w.exp.accept(self).unNx(),
                       JUMP(NAME(testLabel)),
                       LABEL(endLabel)]))

    @visitor(For)
    def visit(self, f):
        # Store the end loop label, then expand the initial assignment, the
        # test and the body.
        endLabel = Label.create(self.current_frame())
        self.loops[f] = endLabel
        testLabel = Label.create(self.current_frame())
        bodyLabel = Label.create(self.current_frame())
        index = self.current_frame().alloc(f.indexdecl.escapes)
        indexSxp = index.toSxp(TEMP(self.current_frame().fp))
        self.frame_parameters[f.indexdecl] = index
        return Nx(SEQ([MOVE(indexSxp,
                            f.low_bound.accept(self).unEx()),
                       LABEL(testLabel),
                       Cx(self.current_frame(),
                          "<=",
                          Ex(indexSxp),
                          f.high_bound.accept(self)).unCx(
                             NAME(bodyLabel), NAME(endLabel)),
                       LABEL(bodyLabel),
                       f.exp.accept(self).unNx(),
                       MOVE(indexSxp,
                            BINOP("+", indexSxp, CONST(1))),
                       JUMP(NAME(testLabel)),
                       LABEL(endLabel)]))
