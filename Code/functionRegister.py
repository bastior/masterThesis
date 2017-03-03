from enum import Enum


class FunType(Enum):
    VALUE = 1
    VARIABLE = 2
    BACKTRACK = 3
    RESTART = 4


val_functions = []
var_functions = []
backtrack_functions = []
restart_functions = []


def register(argument, *, cli_arg, help_desc):
    def wrapper(fun):
        if argument == FunType.VALUE:
            val_functions.append((fun.__name__, cli_arg, help_desc))
        elif argument == FunType.VARIABLE:
            var_functions.append((fun.__name__, cli_arg, help_desc))
        elif argument == FunType.BACKTRACK:
            backtrack_functions.append((fun.__name__, cli_arg, help_desc))
        elif argument == FunType.RESTART:
            restart_functions.append((fun.__name__, cli_arg, help_desc))
        return fun
    return wrapper
