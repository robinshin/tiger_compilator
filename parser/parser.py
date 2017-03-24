from ast.nodes import *
from . import tokenizer
import ply.yacc as yacc

tokens = tokenizer.tokens

precedence = (
    ('nonassoc', 'ELSE'),
    ('left', 'OR'),
    ('left', 'AND'),
    ('nonassoc', 'SMALLER', 'SMALLEROREQUALS', 'BIGGER', 'BIGGEROREQUALS', 'EQUAL', 'DIFFERENT'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
    ('right', 'UMINUS')
)

def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
                  | expression MINUS expression
                  | expression AND expression
                  | expression OR expression
                  | expression SMALLER expression
                  | expression SMALLEROREQUALS expression
                  | expression BIGGER expression
                  | expression BIGGEROREQUALS expression
                  | expression EQUAL expression
                  | expression DIFFERENT expression'''
    p[0] = BinaryOperator(p[2], p[1], p[3])

def p_expression_number(p):
    'expression : NUMBER'
    p[0] = IntegerLiteral(p[1])

def p_expression_identifier(p):
    'expression : ID'
    p[0] = Identifier(p[1])

def p_expression_uminus(p):
    'expression : MINUS expression %prec UMINUS'
    p[0] = BinaryOperator(p[1], IntegerLiteral(0), p[2])

def p_expression_seq_exp(p):
    '''expression : LPAREN RPAREN
                  | LPAREN seq_expression RPAREN'''
    p[0] = SeqExp(p[2]) if len(p) == 4 else SeqExp([])

def p_seq_expression(p):
    '''seq_expression : expression
                      | seq_expression SEMICOLON expression'''
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[3]]

#### If/then/else structure
def p_expression_ifthenelse(p):
    '''expression : IF expression THEN expression ELSE expression
                  | IF expression THEN expression'''
    p[0] = IfThenElse(p[2], p[4], p[6]) if len(p) == 7 else IfThenElse(p[2], p[4], None)

#### Declarations
def p_decls(p):
    '''decls : decl
             | decls decl'''
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]

def p_decl(p):
    '''decl : var_decl
            | fun_decl'''
    p[0] = p[1]

## Variable declaration
def p_var_decl(p):
    '''var_decl : VAR ID ASSIGN expression
                | VAR ID COLON INT ASSIGN expression'''
    p[0] = VarDecl(p[2], None, p[4]) if len(p) == 5 else VarDecl(p[2], Type(p[4]), p[6])

## Function declaration
def p_fun_decl(p):
    '''fun_decl : FUNCTION ID LPAREN fun_decl_args RPAREN EQUAL expression
                | FUNCTION ID LPAREN fun_decl_args RPAREN COLON INT EQUAL expression'''
    p[0] = FunDecl(p[2], p[4], Type(p[7]), p[9]) if len(p) == 10 else FunDecl(p[2], p[4], None, p[7])

def p_fun_decl_args(p):
    '''fun_decl_args :
                     | fun_decl_argssome'''
    p[0] = p[1] if len(p) == 2 else []

def p_fun_decl_argssome(p):
    '''fun_decl_argssome : fun_decl_arg
                         | fun_decl_argssome COMMA fun_decl_arg'''
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[3]]

def p_fun_decl_arg(p):
    '''fun_decl_arg : ID COLON INT'''
    p[0] = VarDecl(p[1], Type(p[3]), None)

#### Let/in/end structure
def p_expression_let(p):
    '''expression : LET decls IN seq_expression END
                  | LET decls IN END'''
    p[0] = Let(p[2], p[4]) if len(p) == 6 else Let(p[2], [])

#### Function call
def p_fun_call(p):
    '''expression : ID LPAREN fun_call_args RPAREN'''
    p[0] = FunCall(Identifier(p[1]), p[3])

def p_fun_call_args(p):
    '''fun_call_args :
                     | fun_call_argssome'''
    p[0] = p[1] if len(p) == 2 else []

def p_fun_call_argssome(p):
    '''fun_call_argssome : expression
                         | fun_call_argssome COMMA expression'''
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[3]]

#### Assignment
def p_assignment(p):
    '''expression : ID ASSIGN expression'''
    p[0] = Assignment(Identifier(p[1]), p[3])

### While structure
def p_while(p):
    '''expression : WHILE expression DO expression'''
    p[0] = While(p[2], p[4]) 

### For structure
def p_for(p):
    '''expression : FOR ID ASSIGN expression TO expression DO expression'''
    p[0] = For(IndexDecl(p[2]), p[4], p[6], p[8])

### Break
def p_break(p):
    '''expression : BREAK'''
    p[0] = Break()


def p_error(p):
    import sys
    sys.stderr.write("no way to analyze %s\n" % p)
    sys.exit(1)

parser = yacc.yacc()

def parse(text):
    return parser.parse(text, lexer = tokenizer.lexer.clone())
