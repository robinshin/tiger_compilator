import ply.lex as lex

# List of keywords. Each keyword will be return as a token of a specific
# type, which makes it easier to match it in grammatical rules.
keywords = {'array': 'ARRAY',
            'break': 'BREAK',
            'do': 'DO',
            'else': 'ELSE',
            'end': 'END',
            'for': 'FOR',
            'function': 'FUNCTION',
            'if': 'IF',
            'in': 'IN',
            'let': 'LET',
            'nil': 'NIL',
            'of': 'OF',
            'then': 'THEN',
            'to': 'TO',
            'type': 'TYPE',
            'var': 'VAR',
            'while': 'WHILE',
            'int': 'INT'}


# List of tokens that can be recognized and are handled by the current
# grammar rules.
tokens = ('END', 'IN', 'LET', 'VAR',
          'PLUS', 'TIMES', 'MINUS', 'DIVIDE', 'AND', 'OR',
          'SMALLER', 'SMALLEROREQUALS', 'BIGGER', 'BIGGEROREQUALS', 'EQUAL', 'DIFFERENT',
          'COMMA', 'SEMICOLON',
          'LPAREN', 'RPAREN',
          'NUMBER', 'ID',
          'COLON', 'ASSIGN',
          'IF', 'THEN', 'ELSE',
          'FUNCTION', 'INT',
          'WHILE', 'DO',
          'FOR', 'TO',
          'BREAK')

t_PLUS = r'\+'
t_TIMES = r'\*'
t_MINUS = r'-'
t_DIVIDE = r'/'
t_AND = r'\&'
t_OR = r'\|'
t_SMALLER = r'<'
t_SMALLEROREQUALS = r'<='
t_BIGGER = r'>'
t_BIGGEROREQUALS = r'>='
t_EQUAL = r'='
t_DIFFERENT = r'<>'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_COLON = r':'
t_ASSIGN = r':='
t_COMMA = r','
t_SEMICOLON = r';'

t_ignore = ' \t'

# Count lines when newlines are encountered
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Distinguish between identifier and keyword. If the keyword is not also
# in the tokens list, this is a syntax error pure and simple since we do
# not know what to do about it.
def t_ID(t):
    r'[A-Za-z][A-Za-z\d_]*'
    if t.value in keywords:
        t.type = keywords.get(t.value)
        if t.type not in tokens:
            raise lex.LexError("unhandled keyword %s" % t.value, t.type)
    return t

# Recognize number - no leading 0 are allowed
def t_NUMBER(t):
    r'[1-9]\d*|0'
    t.value = int(t.value)
    return t

## Comments
# Declare the state
states = (
    ('ccomment','exclusive'),
)

# Match the first /*. Enter ccoment state.
def t_begin_ccomment(t):
    r'\/\*'
    t.lexer.code_start = t.lexer.lexpos        # Record the starting position
    t.lexer.level = 1                          # Initial brace level
    t.lexer.push_state('ccomment')                     # Enter 'ccoment' state

# Rules for the ccoment state
def t_ccomment_lcomment(t):     
    r'\/\*'
    t.lexer.level +=1                
    t.lexer.push_state('ccomment')

def t_ccomment_rcomment(t):
    r'\*\/'
    t.lexer.level -=1
    t.lexer.pop_state()
    if t.lexer.level == 0:
        t.lexer.begin('INITIAL')

def t_comment(t):
    r'\/\/.*'
    pass

# Ignored characters (whitespace)
t_ccomment_ignore = " \t\n"

# For bad characters, we just skip over it
def t_ccomment_error(t):
    t.lexer.skip(1)

def t_error(t):
    raise lex.LexError("unknown token %s" % t.value, t.value)

def t_ANY_eof(t):
    try:
        if t.lexer.level != 0:
            print("Make sure that comments /* */ are correct")
            import sys
            sys.exit(1)
    except AttributeError:
        pass

lexer = lex.lex()
