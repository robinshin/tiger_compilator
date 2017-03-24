#! /usr/bin/env python
#
# Do not modify

from optparse import OptionParser
from parser.parser import parse
import sys

parser = OptionParser()
parser.add_option("-b", "--bind",
                  help="invoke the binder",
                  action="store_true", default=False,
                  dest="bind")
parser.add_option("-c", "--canon",
                  help="canonicalize the IR tree",
                  action="store_true", default=False,
                  dest="canon")
parser.add_option("-d", "--dump",
                  help="dump input file to output",
                  action="store_true", default=False,
                  dest="dump")
parser.add_option("-E", "--expression",
                  help="use expression instead of file",
                  action="store", default=None,
                  dest="expression")
parser.add_option("-e", "--eval",
                  help="evaluate input file to output",
                  action="store_true", default=False,
                  dest="eval")
parser.add_option("-i", "--ir",
                  help="invoke IR translator",
                  action="store_true", default=False,
                  dest="ir")
parser.add_option("-I", "--irvm",
                  help="use IRVM target (default: ARM)",
                  action="store_true", default=False,
                  dest="irvm")
parser.add_option("-t", "--type",
                  help="invoke the typer",
                  action="store_true", default=False,
                  dest="type")
parser.usage = """%prog [options] [file]"""
parser.description = "Compile a Tiger program (or standard input)"

(options, args) = parser.parse_args()
options.ir |= options.canon
options.type |= options.ir

if len(args) > 1 or (options.expression and len(args) > 0):
    parser.print_help(file=sys.stderr)
    sys.exit(1)

if options.expression:
    content = options.expression
else:
    fd = open(args[0]) if args else sys.stdin
    content = fd.read()
    fd.close()

tree = parse(content)

if options.bind or options.type:
    from semantics.binder import Binder
    tree.accept(Binder())
    if options.type:
        from typer.typer import Typer
        Typer().run(tree, True)

if options.ir:
    if options.irvm:
        from irvm.frame import IrvmFrame as Frame
    else:
        from arm.frame import ArmFrame as Frame
    from ir.translate import Translator
    funcs = Translator(Frame).run(tree)
    if options.canon:
        from ir.canonical import canon
        from ir.hoist import HoistCalls
        H = HoistCalls()
        for (f, (frame, stm)) in funcs.items():
            funcs[f] = (frame, canon(stm.accept(H)))
    if options.dump:
        from ir.dumper import Dumper
        for (frame, stm) in funcs.values():
            print(stm.accept(Dumper()))
elif options.dump:
    from parser.dumper import Dumper
    print(tree.accept(Dumper(options.bind)))

if options.eval:
    from ast.evaluator import Evaluator
    print("Evaluating: %s" % tree.accept(Evaluator()))
