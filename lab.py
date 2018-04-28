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

    # split source into lines
    for multiline in source.splitlines():
        char = 0
        while char < len(multiline):

            # move to end of the comment 
            if multiline[char] == ";":
                char = len(multiline)

            # if there's multi-character from before, add them
            elif multiline[char] == "(" or multiline[char] == ")":
                if cont_char != "":
                    tokens.append(cont_char)
                    cont_char = ""
                tokens.append(multiline[char])
            else:

                # continue adding character when it's not space
                if multiline[char] != " ":
                    cont_char += multiline[char]
                elif cont_char != "" and multiline[char] == " ":
                    tokens.append(cont_char)
                    cont_char = ""
            char += 1

        # hanging characters
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
        """
        Tests if the input is valid with correct number of parenthesis
        Cannot have mis-matching parenthesis or ) ( 
        """
        count = 0
        if tokens[0] != "(" and len(tokens) > 1:
            return False
        
        for char in range(len(tokens)):
            if tokens[char] == "(":
                count += 1
            elif tokens[char] == ")":
                count -= 1
                if count < 0:
                    return False
                if count == 0 and char != len(tokens)-1:
                    return False

        if count != 0:
            return False
        return True

    def parse_expression(index):
        """
        Parse valid expressions into list
        """
        if tokens[index] == "(":
            i = index+1
            answer = []
            while i < len(tokens):

                # base case
                if tokens[i] == ")":
                    return answer, i+1

                # parse all information to the right of the index
                sub_parsed, sub_index = parse_expression(i)

                # append answer to the list
                answer.append(sub_parsed)
                i = sub_index
            return answer, i+1
        else:

            # see if token should be float or string
            try:
                expression = float(tokens[index])
                int_float = True
            except:
                expression = tokens[index]
                int_float = False

            # float vs int 
            if int_float:
                if int(float(tokens[index])) == float(tokens[index]):
                    expression = int(tokens[index])
                
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

def boolean_statement(tree, op):
    if len(tree) == 1:
        return True

    for val in range(len(tree)-1):
        if op == "=?":
            if tree[val] != tree[val+1]:
                return False
        elif op == ">":
            if tree[val] <= tree[val+1]:
                return False
        elif op == ">=":
            if tree[val] < tree[val+1]:
                return False
        elif op == "<":
            if tree[val] >= tree[val+1]:
                return False
        elif op == "<=":
            if tree[val] > tree[val+1]:
                return False
            
    return True
        

carlae_builtins = {
    '+': sum,
    '-': lambda args: -args[0] if len(args) == 1 else (args[0] - sum(args[1:])),
    "*": lambda args: product(args),
    "/": lambda args: division(args),
    "#f": False,
    "#t": True, 
    "=?": lambda args: boolean_statement(args, "=?"),
    ">": lambda args: boolean_statement(args, ">"),
    ">=": lambda args: boolean_statement(args, ">="),
    "<": lambda args: boolean_statement(args, "<"),
    "<=": lambda args: boolean_statement(args, "<=")
}


def evaluate(tree, environment=None):
    """
    Evaluate the given syntax tree according to the rules of the carlae
    language.

    Arguments:
        tree (type varies): a fully parsed expression, as the output from the
                            parse function
    """

    # take care of missing environment
    if environment == None:
        environment = Environment(carlae_environment)

    # if input is a list 
    if isinstance(tree, list):

        # take care of empty list 
        if len(tree) == 0:
            raise EvaluationError

        if tree[0] == "define":

            # easier function format: convert to original format
            if isinstance(tree[1], list):
                func_name = tree[1][0]
                args = tree[1][1:].copy()
                op = tree[2].copy()
                tree[1] = func_name
                tree[2] = ['lambda', args, op]

            # regular define function
            assigned = evaluate(tree[2], environment)
            environment.assignment[tree[1]] = assigned
            return assigned
        
        elif tree[0] == "lambda":
            param = tree[1]
            func = tree[2]

            # create LISP function with corresponding parameters
            lisp_func = LISP_Functions(param, func, environment)
            return lisp_func

        elif tree[0] == "cons":
            pass

        elif tree[0] == "if":
            if evaluate(tree[1], environment):
                return evaluate(tree[2], environment)
            return evaluate(tree[3], environment)

        elif tree[0] == "and":
            for val in tree[1:]:
                if not evaluate(val, environment):
                    return False
            return True
            
        elif tree[0] == "or":
            for val in tree[1:]:
                if evaluate(val, environment):
                    return True
            return False

        elif tree[0] == "not":
            if not evaluate(tree[1], environment):
                return True
            return False
            

        # inline lambda 
        elif isinstance(tree[0], list):
            sub_tree = tree[0]
            args = tree[1:]
            lambda_func = evaluate(sub_tree, environment)
            values = [evaluate(arg, environment) for arg in args]
            return lambda_func(values)

        # try adding to the list for operation
        try:
            func = environment.lookup(tree[0])
            evaled_list = []
            for elt in tree[1:]:
                evaled_list.append(evaluate(elt, environment))

            # operate with all variables
            return func(evaled_list)
        except:
            raise EvaluationError

    # evaluate individual character
    else:
        if isinstance(tree, (int, float)):
            return tree
        return environment.lookup(tree)


class Environment(object):
    def __init__(self, parent=None):
        self.parent = parent
        self.assignment = dict()

    def lookup(self, var):
        # recursive look up for parent assignment
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
        # create new environment upon call
        new_env = Environment(self.env)
        if len(self.variables) != len(args):
            raise EvaluationError

        # assign all variables to corresponding input arguments
        for v in range(len(self.variables)):
            new_env.assignment[self.variables[v]] = args[v]
        return evaluate(self.function, new_env)

class Pair(object):
    def __init__(self, car, cdr):
        self.car = car
        self.cdr = cdr
        

def result_and_env(tree, environment=None):
    # create environment if none 
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

        # raise error and continue
        try:
            result, env = result_and_env(parsed, environment)
            print ("out> "+str(result))
        except:
            print ("EvaluationError")
        user_input = input("in> ")

carlae_environment = Environment()
carlae_environment.assignment = carlae_builtins


if __name__ == '__main__':
    # code in this block will only be executed if lab.py is the main file being
    # run (not when this module is imported)
    REPL()

