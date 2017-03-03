from tree import Tree
from functionRegister import *

import argparse
import os.path


def validate_file(file):
    return os.path.exists(file)


def print_extended_help():
    help_str = "Following parameters are configurable within solver.\nEach argument has it's own function, that might "\
               "change solver's behaviour.\nFor each configurable attribute, every possibility is explained below\n"

    help_str += "\nVariable functions (--var) is used to determine order of variables."\
                "\nPossible Functions: \n"
    tmp = '\n'.join([': '.join(par) for par in [[function[1], function[2]] for function in var_functions]])
    help_str += tmp

    help_str += "\n\nValue functions (--val) is used to determine which value to assign first."\
                "\nPossible Functions: \n"
    tmp = '\n'.join([': '.join(par) for par in [[function[1], function[2]] for function in val_functions]])
    help_str += tmp

    help_str += "\n\nBacktrack functions (--backtrack) is used to determine which algorithm for backtracking is used."\
                "\nPossible Functions: \n"
    tmp = '\n'.join([': '.join(par) for par in [[function[1], function[2]] for function in backtrack_functions]])
    help_str += tmp

    help_str += "\n\nRestart functions (--restart) is used to determine condition at which solver restarts itself."\
                "\nPossible Functions: \n"
    tmp = '\n'.join([': '.join(par) for par in [[function[1], function[2]] for function in restart_functions]])
    help_str += tmp

    print(help_str)


def parser():
    parser_inst = argparse.ArgumentParser()
    parser_inst.add_argument('file',
                             help="Name of file in DIMACS format with SAT problem")

    parser_inst.add_argument('-l', '--longHelp',
                             action='store_true',
                             help="Use this help to see detailed description of all available functions")

    parser_inst.add_argument('--solution_num',
                             required=False,
                             type=int,
                             action="store",
                             default=1,
                             help="Number of solutions that solver will try to find, type 0 for all solutions")

    parser_inst.add_argument('--val',
                             required=False,
                             choices=[values[1] for values in val_functions],
                             default=val_functions[0][1],
                             help="Function choosing value for variable in each step")

    parser_inst.add_argument('--var',
                             required=False,
                             choices=[variables[1] for variables in var_functions],
                             default=var_functions[0][1],
                             help="Function choosing variable in each step")

    parser_inst.add_argument('--backtrack',
                             required=False,
                             choices=[bt[1] for bt in backtrack_functions],
                             default=backtrack_functions[0][1],
                             help="Function backtrack technique")

    parser_inst.add_argument('--restart',
                             required=False,
                             choices=[rest[1] for rest in restart_functions],
                             default=restart_functions[0][1],
                             help="Solver restart condition")

    return parser_inst


# this is moved here only for proxy reasons - useful in tests
def run_solver(val, var, backtrack, restart, filename, solution_num):
    Tree([fun[0] for fun in val_functions if fun[1] == val][0],
         [fun[0] for fun in var_functions if fun[1] == var][0],
         [fun[0] for fun in backtrack_functions if fun[1] == backtrack][0],
         [fun[0] for fun in restart_functions if fun[1] == restart][0],
         file_name=filename,
         number_of_solutions=solution_num)

if __name__ == '__main__':

    args = parser().parse_args()
    if not validate_file(args.file):
        print("Following file does not exist or could not be open: " + args.file)
        exit(1)

    if args.longHelp:
        print_extended_help()
        exit(0)

    else:
        run_solver(args.val, args.var, args.backtrack, args.restart, args.file, args.solution_num)
