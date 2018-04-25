"""6.009 Lab 8A: carlae Interpreter"""

import sys


class EvaluationError(Exception):
    """Exception to be raised if there is an error during evaluation."""
    pass


def tokenize(source):
    """
    Splits an input string into meaningful tokens (left parens, right parens,
    other whitespace-separated values).  Returns a list of strings.

    Arguments:
        source (str): a string containing the source code of a carlae
                      expression
    """
    tokens = []
    cont_char = ""
    
    for multiline in source.splitlines():
        char = 0
        while char < len(multiline):
            if multiline[char] == ";":
                char = len(multiline)
            elif multiline[char] == "(" or multiline[char] == ")":
                if cont_char != "":
                    tokens.append(cont_char)
                    cont_char = ""
                tokens.append(multiline[char])
            else:
                if multiline[char] != " ":
                    cont_char += multiline[char]
                elif cont_char != "" and multiline[char] == " ":
                    tokens.append(cont_char)
                    cont_char = ""
            char += 1

        if cont_char != "":
            tokens.append(cont_char)
            cont_char = ""

    return tokens
        

def parse(tokens):
    """
    Parses a list of tokens, constructing a representation where:
        * symbols are represented as Python strings
        * numbers are represented as Python ints or floats
        * S-expressions are represented as Python lists

    Arguments:
        tokens (list): a list of strings representing tokens
    """

    def is_valid():
        count = 0
        if tokens[0] != "(" and len(tokens) > 1:
            return False
        
        for char in tokens:
            if char == "(":
                count += 1
            elif char == ")":
                count -= 1
                if count < 0:
                    return False

        if count != 0:
            return False
        return True

    def parse_expression(index):
        if tokens[index] == "(":
            i = index+1
            answer = []
            while i < len(tokens):
                if tokens[i] == ")":
                    return answer, i+1
                sub_parsed, sub_index = parse_expression(i)
                answer.append(sub_parsed)
                i = sub_index
            return answer, i+1
        else:
            try:
                expression = float(tokens[index])
            except:
                expression = tokens[index]
            return expression, index+1

    if not is_valid():
        raise SyntaxError
    else:
        final_expression = parse_expression(0)[0]
        return final_expression 

def product(tree):
    prod = tree[0]
    for val in tree[1:]:
        prod *= val
    return prod

def division(tree):
    div = tree[0]
    for val in tree[1:]:
        div /= val
    return div

carlae_builtins = {
    '+': sum,
    '-': lambda args: -args[0] if len(args) == 1 else (args[0] - sum(args[1:])),
    "*": lambda args: product(args),
    "/": lambda args: division(args)
}


def evaluate(tree, environment=None):
    """
    Evaluate the given syntax tree according to the rules of the carlae
    language.

    Arguments:
        tree (type varies): a fully parsed expression, as the output from the
                            parse function
    """
    if environment == None:
        environment = Environment(carlae_environment)
    
    if isinstance(tree, list):
        if tree[0] == "define":
            if isinstance(tree[1], list):
                func_name = tree[1][0]
                args = tree[1][1:].copy()
                op = tree[2].copy()
                tree[1] = func_name
                tree[2] = ['lambda', args, op]
                
            assigned = evaluate(tree[2], environment)
            environment.assignment[tree[1]] = assigned
            return assigned
        elif tree[0] == "lambda":
            param = tree[1]
            func = tree[2]
            lisp_func = LISP_Functions(param, func, environment)
            return lisp_func
        elif isinstance(tree[0], list):
            sub_tree = tree[0]
            args = tree[1:]
            lambda_func = evaluate(sub_tree, environment)
            values = [evaluate(arg, environment) for arg in args]
            return lambda_func(values)
        
        try:
            func = environment.lookup(tree[0])
            evaled_list = []
            for elt in tree[1:]:
                evaled_list.append(evaluate(elt, environment))
            return func(evaled_list)
        except:
            raise EvaluationError
    else:
        if isinstance(tree, (int, float)):
            return tree
        return environment.lookup(tree)


class Environment(object):
    def __init__(self, parent=None):
        self.parent = parent
        self.assignment = dict()

    def lookup(self, var):
        if var in self.assignment:
            return self.assignment[var]
        elif self.parent == None:
            raise EvaluationError
        else:
            return self.parent.lookup(var)

class LISP_Functions(object):
    def __init__(self, param, func, environment):
        self.variables = param
        self.function = func
        self.env = environment

    def __call__(self, args):
        new_env = Environment(self.env)
        for v in range(len(self.variables)):
            new_env.assignment[self.variables[v]] = args[v]
        return evaluate(self.function, new_env)
        

def result_and_env(tree, environment=None):
    if environment == None:
        environment = Environment(carlae_environment)
    return evaluate(tree, environment), environment


def REPL(environment=None):
    user_input = input("in> ")
    if environment == None:
        environment = Environment(carlae_environment)
        
    while user_input != "QUIT":
        tokens = tokenize(user_input)
        parsed = parse(tokens)
        print (parsed)
        result, env = result_and_env(parsed, environment)
        print ("out> "+str(result))
        user_input = input("in> ")

carlae_environment = Environment()
carlae_environment.assignment = carlae_builtins


if __name__ == '__main__':
    # code in this block will only be executed if lab.py is the main file being
    # run (not when this module is imported)
    REPL()
    

