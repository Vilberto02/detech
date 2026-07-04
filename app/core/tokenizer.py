"""
Tokenización léxica de código fuente multilingüe.
Usa Pygments para descomponer el código en tokens sin construir un AST formal.
"""

import re
from dataclasses import dataclass
from typing import List, Optional
from pygments.lexers import get_lexer_for_filename, guess_lexer
from pygments.util import ClassNotFound
from pygments.token import Token as PygmentsToken

@dataclass
class Token:
    """Representa un token léxico del código fuente."""
    type: str          # Categoría mapeada
    string: str        # Valor textual del token
    line: int          # Número de línea (1-indexed)
    col: int           # Columna de inicio (0-indexed)
    line_text: str     # Texto completo de la línea donde aparece el token
    pygments_type: object # Tipo de token original de Pygments

# Tipos de token unificados
NAME_TOKEN = "NAME"
COMMENT_TOKEN = "COMMENT"
STRING_TOKEN = "STRING"
OP_TOKEN = "OP"
NEWLINE_TOKEN = "NEWLINE"
KEYWORD_TOKEN = "KEYWORD"
UNKNOWN_TOKEN = "UNKNOWN"

# Maintain compatibility imports but we don't emit them anymore
INDENT_TOKEN = "INDENT"
DEDENT_TOKEN = "DEDENT"
NL_TOKEN = "NL"

CONTROL_FLOW_KEYWORDS = frozenset({
    # Python
    "if", "elif", "else", "for", "while", "try", "except", "finally", "with", "case", "match",
    # JS/TS / Java / C++ / Go / Rust
    "switch", "catch", "do", "loop", "defer", "go"
})

def map_pygments_token_to_unified(token_type) -> str:
    if token_type in PygmentsToken.Keyword:
        return KEYWORD_TOKEN
    elif token_type in PygmentsToken.Name:
        return NAME_TOKEN
    elif token_type in PygmentsToken.String:
        return STRING_TOKEN
    elif token_type in PygmentsToken.Comment:
        return COMMENT_TOKEN
    elif token_type in PygmentsToken.Operator or token_type in PygmentsToken.Punctuation:
        return OP_TOKEN
    elif token_type in PygmentsToken.Text and (token_type == PygmentsToken.Text.Whitespace or token_type == PygmentsToken.Text):
        return "WHITESPACE"
    return UNKNOWN_TOKEN

def tokenize_source(source: str, filepath: Optional[str] = None) -> List[Token]:
    """Tokeniza el código fuente usando Pygments."""
    lexer = None
    if filepath:
        try:
            lexer = get_lexer_for_filename(filepath)
        except ClassNotFound:
            pass
    
    if not lexer:
        try:
            lexer = guess_lexer(source)
        except ClassNotFound:
            from pygments.lexers.special import TextLexer
            lexer = TextLexer()
            
    tokens: List[Token] = []
    lines = source.splitlines()
    if not lines:
        return tokens
        
    current_line = 1
    current_col = 0
    
    for t_type, t_value in lexer.get_tokens(source):
        lines_in_value = t_value.split('\n')
        
        for i, val_line in enumerate(lines_in_value):
            if val_line:
                unified_type = map_pygments_token_to_unified(t_type)
                if unified_type != "WHITESPACE":
                    line_idx = current_line - 1
                    line_text = lines[line_idx] if line_idx < len(lines) else ""
                    
                    tokens.append(Token(
                        type=unified_type,
                        string=val_line,
                        line=current_line,
                        col=current_col,
                        line_text=line_text,
                        pygments_type=t_type
                    ))
                current_col += len(val_line)
            
            if i < len(lines_in_value) - 1:
                line_idx = current_line - 1
                line_text = lines[line_idx] if line_idx < len(lines) else ""
                tokens.append(Token(
                    type=NEWLINE_TOKEN,
                    string="\\n",
                    line=current_line,
                    col=current_col,
                    line_text=line_text,
                    pygments_type=PygmentsToken.Text.Whitespace
                ))
                current_line += 1
                current_col = 0
                
    return tokens


def get_lines(source: str) -> List[str]:
    return source.splitlines()


def find_function_boundaries(tokens: List[Token]) -> List[dict]:
    """Detecta funciones usando tokens genéricos de Pygments."""
    functions = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        # Búsqueda genérica de declaración de función
        if tok.pygments_type in PygmentsToken.Keyword.Declaration or (tok.type == KEYWORD_TOKEN and tok.string in ("def", "func", "function", "fn")):
            name = ""
            params_start = -1
            j = i + 1
            while j < len(tokens):
                if tokens[j].pygments_type in PygmentsToken.Name.Function or tokens[j].type == NAME_TOKEN:
                    name = tokens[j].string
                    j += 1
                    break
                if tokens[j].type not in ("WHITESPACE", NEWLINE_TOKEN):
                    break
                j += 1
                
            if name:
                while j < len(tokens) and tokens[j].string != "(":
                    if tokens[j].type not in ("WHITESPACE", NEWLINE_TOKEN):
                        break
                    j += 1
                if j < len(tokens) and tokens[j].string == "(":
                    params_start = j
                    functions.append({
                        "name": name,
                        "start_line": tok.line,
                        "params_token_idx": params_start,
                    })
        i += 1
    return functions

def count_function_params(tokens: List[Token], open_paren_idx: int) -> int:
    """Cuenta parámetros contando comas en el nivel raíz de los paréntesis."""
    depth = 0
    param_count = 0
    found_param = False
    i = open_paren_idx

    while i < len(tokens):
        tok = tokens[i]
        if tok.string == "(":
            depth += 1
        elif tok.string == ")":
            depth -= 1
            if depth == 0:
                if found_param:
                    param_count += 1
                break
        elif depth == 1 and tok.string == ",":
            param_count += 1
        elif depth == 1 and tok.type in (NAME_TOKEN, KEYWORD_TOKEN) and not found_param:
            found_param = True
        i += 1
    return param_count


_COMMENTED_CODE_PATTERN = re.compile(
    r"^\s*(#|//|/\*)\s*(def |class |import |from |if |for |while |return |func |function |fn |let |const |var )",
    re.IGNORECASE,
)

def is_commented_code_line(line: str) -> bool:
    return bool(_COMMENTED_CODE_PATTERN.match(line))
