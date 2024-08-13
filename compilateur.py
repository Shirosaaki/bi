#!/usr/bin/env python3
import os
import sys
import re

TRANSFORM = {
    '000': 'int',
    '001': 'char',
    '100': 'char*',
    '101': 'void',
    '0000': 'if(',
    '0001': 'else',
    '0010': 'for (int',
    '0011': 'while (',
    '0100': 'printf (',
    '0101': 'getline (',
    '0110': 'return',
    '0111': 'rand',
    '1000': 'malloc (',
    '00000': '+',
    '00001': '-',
    '00010': '*',
    '00011': '/',
    '00100': '%',
    '00101': '=',
    '00110': '==',
    '00111': '!=',
    '01000': '>',
    '01001': '<',
    '01010': '>=',
    '01011': '<=',
    '01100': '&&',
    '01101': '||',
    '01110': '+=',
    '01111': '-=',
    '10000': '*=',
    '10001': '/=',
    '10010': '%=',
    '10011': '++',
    '10100': '--',
}

TYPE_TO_POURCENTAGE = {
    'int': '%d',
    'char': '%c',
    'char*': '%s',
}

DIC_VAR1 = {}
DIC_VAR2 = {}
DIC_FUNC = {}
FUNC = []

def convert_binary_to_decimal(binary):
    decimal = 0
    for digit in binary:
        decimal = decimal*2 + int(digit)
    return decimal

def is_function_start(line):
    return re.match(r'^[0-1*]{3} \*?[*0-1]{7} .*\{$', line.strip())

def is_function(line):
    pattern = r'^(int|char\*+|void) \*?(func[01]{7}|main)( .*)?\{$'
    return re.match(pattern, line.strip()) is not None

def get_max_index(var):
    max_key = None
    for key, value in DIC_VAR1.items():
        if value == var:
            if max_key is None or key > max_key:
                print(key)
                max_key = key
    return max_key

def mod_func(line):
    n_line = ""
    i = 0
    while i < len(line):
        if line[i] in '01':
            k = i
            while i < len(line) and line[i] in '01':
                i += 1
            seq_length = i - k
            if seq_length == 7:
                n_line += line[k:i]
                n_line += ' ('
                try:
                    DIC_FUNC[line[k-4:i]] = TYPE_TO_POURCENTAGE[line[:3]]
                except:
                    DIC_FUNC[line[k-4:i]] = TYPE_TO_POURCENTAGE[line[:4]]
            elif seq_length == 6:
                n_line += line[k:i]
                if line[i] != '{' and n_line[-1] != '(' and line[i+1] != '{':
                    n_line += ', '
            else:
                n_line += ' ' if n_line and n_line[-1] not in ' (' else ''
                n_line += line[k:i]
        elif line[i] == '{':
            n_line += ') {'
            break
        else:
            n_line += line[i]
        i += 1
    return n_line.strip()

def main_use(line):
    n_line = ""
    i = line.find('(') + 1
    n_line += line[:i]
    while line[i] != '{':
        if line[i] in '01':
            k = i
            while line[i] in '01':
                i += 1
            seq_length = i - k
            if seq_length == 6:
                n_line += line[k:i]
                if line[i + 1] != '{':
                    n_line += ', '
            else:
                n_line += n_line[k:i]
        else:
            n_line += line[i]
        i += 1
    n_line += ') {'
    return n_line

def accolades(code):
    in_function = False
    open_braces = 0

    for line in code.split('\n'):
        if not in_function:
            if is_function_start(line):
                in_function = True
                open_braces = 1
            elif line.strip() and not line.isspace() and not line.startswith('//') and not line.startswith('/*') and not line.endswith('*/') and not line.startswith('**'):
                return False
        else:
            open_braces += line.count('{') - line.count('}')
            if open_braces == 0:
                in_function = False
    return True

def var_t(c, v):
    t = c.index('var')
    if c[t-4:t-1] in TYPE_TO_POURCENTAGE:
        DIC_VAR1[v] = c[t:t+9]
        DIC_VAR2[v] = TYPE_TO_POURCENTAGE[c[t-4:t-1]]
        v += 1
    elif c[t-6:t-1] in TYPE_TO_POURCENTAGE:
        DIC_VAR1[v] = c[t:t+9]
        DIC_VAR2[v] = TYPE_TO_POURCENTAGE[c[t-6:t-1]]
        v += 1
    elif c[t-7:t-2] in TYPE_TO_POURCENTAGE:
        DIC_VAR1[v] = c[t:t+9]
        DIC_VAR2[v] = TYPE_TO_POURCENTAGE[c[t-7:t-2]]
        v += 1
    if 'var' in c[t+10:]:
        v = var_t(c[t+10:], v)
    return v

def printf(c):
    t = c.index('printf')
    t += 9
    nn = c[:t] + '"'
    q = 0
    l = []
    for t in range(t, len(c)):
        if c[t] == "\"":
            q += 1
            if q == 2:
                q = 0
        if q == 1 and c[t] != '\"':
            nn += c[t]
        elif c[t] != "\"" and c[t] != ' ':
            if c[t:t+3] == 'var' and c[t-1] != '[':
                nn += DIC_VAR2[get_max_index(c[t:t+9])]
                m = t
                while c[m] != ' ' and c[m] != '\n':
                    m += 1
                l.append(c[t:m])
            elif c[t:t+4] == 'func' and c[t-1] == '[':
                nn += DIC_FUNC[c[t:t+11]]
                l.append(c[t:t+11])
    nn += '"'
    for i in l:
        nn += ', ' + i
    nn += ')'
    c = nn
    return c

def main():
    i = 0
    j = 0
    v = 0
    f = open("output.c", "w")
    f.write("#include \"my.h\"\n")

    if len(sys.argv) < 2:
        print("Usage: python3 compilateur.py <file(s)>")
        sys.exit(1)
    
    for filename in sys.argv[1:]:
        if not os.path.isfile(filename):
            print(f"Error: {filename} is not a file")
            return

        with open(filename, 'r') as file:
            code = file.read()
            if not accolades(code):
                print("Error: code is outside of any function or accolate is not closed")
                return
            new_code = ""
            k = 0
            while k < len(code):
                if code[k] in '01':
                    i = k
                    while k < len(code) and code[k] in '01':
                        k += 1
                    j = k
                    if j-i == 7:
                        instruction = "func"
                        instruction += code[i:j]
                        if instruction == 'func0000000':
                            new_code += 'main('
                        else:
                            new_code += instruction
                    elif j-i == 6:
                        instruction = "var"
                        instruction += code[i:j]
                        new_code += instruction
                    elif 3 <= j-i <= 5:
                        instruction = code[i:j]
                        if instruction in TRANSFORM:
                            new_code += TRANSFORM[instruction]
                        else:
                            print(f"Instruction non reconnue: {instruction}")
                            new_code += code[i:j]
                    else:
                        new_code += code[i:j]
                        k = j
                elif code[k] == 'n' and code[k+1] in '01':
                    k += 1
                    i = k
                    while code[k] in '01':
                        k += 1
                    j = k
                    instruction = code[i:j]
                    new_code += f'{convert_binary_to_decimal(instruction)}'
                else:
                    new_code += code[k]
                    k += 1
            m = new_code.split("\n")
            new_code = ""
            for c in m:
                if "var" in c:
                    v = var_t(c, v)
                if is_function(c):
                    c = mod_func(c)
                    FUNC.append(c)
                elif c.startswith('int main('):
                    c = main_use(c)
                    DIC_FUNC['main'] = TYPE_TO_POURCENTAGE['int']
                elif "for" in c or "while" in c:
                    c = c.replace('{', ') {')
                elif "func" in c:
                    t = c.index('func')
                    t += 11
                    nn = c[:t] + '('
                    for t in range(t, len(c)):
                        if c[t] == ' ' and nn[t] != '(':
                            nn += ', '
                        else:
                            nn += c[t]
                        t += 1
                    nn += ')'
                    c = nn
                if "printf" in c:
                    c = printf(c)
                if "if" in c:
                    c = c.replace('{', ') {')
                new_code += c + '\n'
            dd = ""
            for p in range(len(new_code)):
                if new_code[p] == '\n' and new_code[p-1] != '{' and new_code[p-1] != '}' and p < len(new_code) - 1 and new_code[p-1] != '/':
                    dd += ';\n'
                else:
                    dd += new_code[p]
            f.write(dd)
    f.close()
    for i in FUNC:
        j = i.replace('{', ';')
        FUNC[FUNC.index(i)] = j
    f = open("my.h", "w")
    f.write("#ifndef MY_H_\n")
    f.write("\t#define MY_H_\n")
    f.write("\t#include <stdio.h>\n")
    f.write("\t#include <stdlib.h>\n")
    f.write("\t#include <time.h>\n")
    f.write("\t#include <string.h>\n")
    f.write("\t#include <unistd.h>\n")
    for i in FUNC:
        f.write(i + '\n')
    f.write("#endif /* !MY_H_ */")
    f.close()
    os.system("gcc output.c")
    #os.system("rm output output.c my.h")
main()