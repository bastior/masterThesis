from node import *
from functionRegister import *

from math import copysign, inf
from copy import deepcopy
import heapq

class Tree:

    def __init__(self,
                 val_func,
                 var_func,
                 backtrack_func,
                 restart_func,
                 file_name,
                 number_of_solutions):

        # functions assignments
        self.choose_val = getattr(self, val_func)
        self.choose_var = getattr(self, var_func)
        self.fall_back = getattr(self, backtrack_func)
        self.restart_condition = getattr(self, restart_func)

        # Number given by user how many solutions should solver look for (0 for all until UNSAT)
        self.number_of_solutions_to_find = (inf if not number_of_solutions else number_of_solutions)

        # main list of all clauses and variables
        self.clauses = []
        self.variables = []
        self.variable_lookup = []

        # read file
        self.read_cnf(file_name)

        # create current solution vector
        self.current_solutions = len(self.variables) * [None]

        # variable vectors
        self.used_variables = []
        self.variables_to_use = self.variables[:]

        # Tree pivots
        self.main_node = None
        self.current_node = None

        # Flag to stop searching - found SAT or UNSAT
        self.done_searching = False

        # Variables used for next iteration processing
        self.next_iteration_lookup = deepcopy(self.variable_lookup)
        self.next_iteration_clauses = deepcopy(self.clauses[:])

        # stacks of decisions - could be opt-out later on
        self.stack_of_guessed_decisions = []
        self.stack_of_forced_decisions = []

        # Level of decision
        self.current_level_of_decision = 0

        # latest clause that was learnt
        self.learnt_clause = []
        # latest variable chosen
        self.latest_var = None

        # Set to true to invoke restart on next loop
        self.restart_triggered = False

        # This variable does not get zeroed with restart of solver
        self.number_of_learnt_clauses = 0

        # main loop
        self.main()

    def main(self):
        """
        Main loop of a program. Will loop until solution is found or exit if UNSAT found
        :return: No Return
        """
        # main searching loop
        while not self.done_searching:
            # check if are on leaf's level. If yes - find if sat or fall back
            if self.variables_to_use:
                # start = time.time()
                # Choose variable and value for next loop
                chosen_var, value_to_be_assigned = self.return_variable_and_value()
                node = Node(chosen_var, self.current_node)
                if node.parent:
                    if self.current_solutions[node.parent.variable.number - 1]:
                        node.parent.left_child = node
                    else:
                        node.parent.right_child = node

                self.current_node = node
                self.current_node.variable_lookup_valid_for_node = self.next_iteration_lookup
                self.current_node.current_clauses = self.next_iteration_clauses

                # we are on the top of the tree
                if not self.main_node:
                    self.main_node = node

                # we already have most top node of the tree
                new_lookup, new_clauses = self.update_lookup_and_clauses(self.current_node.variable_lookup_valid_for_node,
                                                                         self.current_node.current_clauses,
                                                                         chosen_var.number,
                                                                         value_to_be_assigned)
                if new_lookup and new_clauses:
                    self.next_iteration_lookup = new_lookup
                    self.next_iteration_clauses = new_clauses
            else:
                if self.check_solution():
                    # print solution and check if we need to search for another
                    for i, solution in enumerate(self.current_solutions, 1):
                        print(i, end=" ") if solution else print(-i, end=" ")
                    print()
                    self.number_of_solutions_to_find -= 1
                    if self.number_of_solutions_to_find == 0:
                        self.done_searching = True
                    else:
                        # add new clause that is negation of found solution
                        new_clause = [-i if solution else i for i, solution in enumerate(self.current_solutions, 1)]
                        self.clauses.append(new_clause)
                        for value in new_clause:
                            self.variable_lookup[abs(value) - 1].append(int(copysign(len(self.clauses), value)))
                        self.restart()

                else:
                    self.fall_back()
            if not self.done_searching and self.restart_triggered:
                self.restart()

    def update_lookup_and_clauses(self, lookup, clauses, variable_number, value):
        """
        :param lookup: lookup list to be updated by new variable assigned
        :param clauses: clauses list to be updated by new variable assigned
        :param variable_number: Variable number that was assigned
        :param value: Value which was assigned to variable param {True/False}
        :return: 2-element Tuple containing (updated lookup list, updated clause list)
        """
        self.current_solutions[variable_number - 1] = value
        # lookup for next iteration
        new_lookup = deepcopy(lookup)
        # clauses for next iteration
        new_clauses = deepcopy(clauses)
        # clauses we need to update
        clauses_to_be_updated = new_lookup[variable_number - 1][:]

        for i in clauses_to_be_updated:
            # variable sign in clause matches. Whole clause is true - it can be removed
            if (i > 0) == value:
                # get the clause to be removed
                to_be_removed = new_clauses[abs(i) - 1]
                # iterate thru removed clause to update all variables in it
                for j in to_be_removed:
                    # we do not have to update variable we choose
                    if j != variable_number:
                        new_lookup[abs(j) - 1].remove(copysign(i, j))
                    # remove clause
                    new_clauses[abs(i) - 1] = []
            # chosen value does not match in given clause - only chosen variable is to be removed from it
            else:
                '''
                example:
                chosen variable: 1 chosen value: True
                given clause
                -1 2 3
                we end up with clause
                2 3
                '''
                if len(new_clauses[abs(i) - 1]) == 1:
                    '''
                    We are trying to assign value to variable which has to be different value
                    '''
                    self.conflict_detected(abs(i) - 1)
                    return None, None
                else:
                    new_clauses[abs(i) - 1].remove(copysign(variable_number, i))

        new_lookup[variable_number - 1] = []
        return new_lookup, new_clauses

    def read_cnf(self, file_name):
        """
        Update Tree class with variables clauses and variable lookup lists
        :param file_name: path to file with cnf formula
        :return: No return
        """
        self.clauses, variables = getClause(file_name)
        var_number = 0
        for var in variables:
            v = Variable()
            v.clauses = var
            v.number = var_number + 1
            self.variables.append(v)
            self.variable_lookup.append(var)
            var_number += 1
            # number of positive appearances
            positive = sum(1 for x in var if x > 0)
            # scale probability from <0,1> to <-1,1>
            try:
                v.probability = ((positive/len(var))*2) - 1
            # if it happens that variable does not occur anywhere in formula
            except ZeroDivisionError:
                v.probability = 1
            # now probability is -1 if only negatives, 0 if same amount of positives and negatives etc.

    def conflict_detected(self, clause_index):
        self.learnt_clause = self.learn_clause(clause_index)
        self.update_tree_with_new_clause(self.learnt_clause)
        self.fall_back()
        self.restart_algorithm()

    def restart_algorithm(self):
        if self.restart_condition():
            self.restart_triggered = True

    def restart(self):
        """
        Restarts whole tree - leaving only learnt clauses. All nodes are deleted after that operation and Tree is empty
        :return: No return
        """
        for node in Node.instances:
            del node
        # just repeat most operations from __init__ to clean up Tree state
        self.used_variables = []
        self.variables_to_use = self.variables[:]
        self.main_node = None
        self.current_node = None
        self.next_iteration_lookup = deepcopy(self.variable_lookup)
        self.next_iteration_clauses = deepcopy(self.clauses[:])
        self.stack_of_guessed_decisions = []
        self.stack_of_forced_decisions = []
        self.current_level_of_decision = 0
        self.learnt_clause = []
        self.latest_var = None
        self.restart_triggered = False

    def learn_clause(self, clause_index):
        clause_to_learn = deepcopy(self.clauses[clause_index])
        clause_to_learn = Tree.merge_clauses(clause_to_learn,
                                             deepcopy(self.clauses[self.current_node.variable.clause_that_lead_to_this_variable]))
        counter = 0
        while True:
            prev_clause = clause_to_learn
            list_of_variables = [self.variables[abs(i) - 1] for i in clause_to_learn]
            # check if we can stop searching
            current_decision_level = self.current_node.variable.level_of_decision
            other_decision_levels = [var.level_of_decision for var in list_of_variables]
            if other_decision_levels.count(current_decision_level) == 1:
                break
            elif other_decision_levels.count(current_decision_level) == 0:
                # TODO find out if this could really happen or something is wrong
                break
                # assert False  # Something is wrong with algorithm as this should never happen
            same_level_variables = [v for v in list_of_variables if v.level_of_decision == current_decision_level]
            var_to_merge = next(v for v in same_level_variables if v.clause_that_lead_to_this_variable is not None)
            next_clause_for_merge = var_to_merge.clause_that_lead_to_this_variable
            clause_to_learn = Tree.merge_clauses(clause_to_learn,
                                                 deepcopy(self.clauses[next_clause_for_merge]))
            if prev_clause == clause_to_learn:
                break  # we learn nothing new, and we start looping around
            counter += 1
            if counter > len(self.variables) > 10:
                # TODO this is due to some bug that clauses are looped and solver can not find new clause.To investigate
                break
        if not clause_to_learn:
            self.print_unsatisfability()
        self.number_of_learnt_clauses += 1
        return clause_to_learn

    def update_tree_with_new_clause(self, clause):
        self.clauses.append(clause)
        for i in clause:
            self.variable_lookup[abs(i)-1].append(int(copysign(len(self.clauses), i)))
        # update main node if exists
        if self.main_node:
            self.main_node.current_clauses.append(clause)
            for i in clause:
                self.main_node.variable_lookup_valid_for_node[abs(i) - 1].append(int(copysign(len(self.clauses), i)))
        nodes_to_update = []

        if self.main_node.left_child:
            nodes_to_update.append(self.main_node.left_child)
        if self.main_node.right_child:
            nodes_to_update.append(self.main_node.right_child)

        while len(nodes_to_update) > 0:
            node = nodes_to_update[0]
            nr = node.parent.variable.number
            var = (node is node.parent.left_child)
            new_clause = deepcopy(node.parent.current_clauses[-1])
            if nr in new_clause:
                if var:
                    new_clause = []
                else:
                    new_clause.remove(nr)
            elif -nr in new_clause:
                if not var:
                    new_clause = []
                else:
                    new_clause.remove(-nr)
            node.current_clauses.append(new_clause)
            for i in node.current_clauses[-1]:
                node.variable_lookup_valid_for_node[abs(i) - 1].append(int(copysign(len(self.clauses), i)))
            if node.left_child:
                nodes_to_update.append(node.left_child)
            if node.right_child:
                nodes_to_update.append(node.right_child)
            nodes_to_update.pop(0)

    def return_variable_and_value(self):
        chosen_var, chosen_val = None, None
        # find if we have any clause with len 1
        for nr, clause in enumerate(self.next_iteration_clauses):
            if len(clause) == 1:
                chosen_var = self.variables[abs(clause[0]) - 1]
                chosen_val = clause[0] > 0
                chosen_var.clause_that_lead_to_this_variable = nr
                break
        if not chosen_var:
            # find if we have any variable with only 1 sign
            for nr, lu in enumerate(self.next_iteration_lookup):
                if lu and (not min(lu) < 0 < max(lu)):
                    # TODO For now lets assume we guessed this variable. To much effort to follow which clause caused it
                    chosen_var = self.variables[nr]
                    chosen_val = lu[0] > 0
                    self.current_level_of_decision += 1
                    break
        if not chosen_var:
            chosen_var = self.choose_var()
            # TODO: This self value could be used as chosen_val. For now it is only helper variable for value funtion
            self.latest_var = chosen_var
            chosen_val = self.choose_val()
            self.current_level_of_decision += 1
            # TODO: Optimise out those stacks. Remove them as it is unnecessary memory usage.
            self.stack_of_guessed_decisions.append(chosen_var)
        else:
            self.stack_of_forced_decisions.append(chosen_var)
            if self.main_node is not None:
                chosen_var.previous_variable = self.current_node.variable
        chosen_var.level_of_decision = self.current_level_of_decision
        self.variables_to_use.remove(chosen_var)
        self.used_variables.append(chosen_var)
        return chosen_var, chosen_val

    @staticmethod
    def print_unsatisfability():
        print("UNSATISFIABLE")
        exit(0)

    @staticmethod
    # TODO this function has big potential for optimisation. Right now it is just a brute-force merging
    def merge_clauses(first, second):
        merged_clause = []
        for i in first:
            if -1 * i in second:
                pass
            else:
                merged_clause.append(i)
        for i in second:
            if -1 * i in first:
                pass
            elif i in merged_clause:
                pass
            else:
                merged_clause.append(i)
        return merged_clause

    def check_solution(self):
        sat = True
        for clause in self.clauses:
            sat_clause = False
            for i in clause:
                if i > 0 and self.current_solutions[i - 1]:
                    sat_clause = True
                if i < 0 and not self.current_solutions[abs(i) - 1]:
                    sat_clause = True
            if not sat_clause:
                sat = False
                break
        return sat

    """
    REGISTER FUNCTIONS STARING HERE - FUNCTIONS THAT CAN BE REPLACE MAIN TREE FUNCTIONS
    """

    @register(FunType.RESTART, cli_arg='F', help_desc="Restart each 50 clauses learned")
    def restart_each_fifty(self):
        if self.number_of_learnt_clauses % 50 == 0 and self.number_of_learnt_clauses > 0:
            return True
        else:
            return False

    @register(FunType.RESTART, cli_arg='S', help_desc="Restart condition increased by 20 learnt clause each restart"
                                                      " starting from 30 (30-50-70-90-etc..)")
    def restart_sum(self):
        if self.number_of_learnt_clauses == self.sum_counter and self.number_of_learnt_clauses > 0:
            self.sum_counter += 20
            return True
        else:
            return False
    # init static counter for fun above
    sum_counter = 30

    @register(FunType.RESTART, cli_arg='M', help_desc="Restart condition multiplied by 2 learnt clause each restart"
                                                      " starting from 10 (10-20-40-80-etc..)")
    def restart_mul(self):
        if self.number_of_learnt_clauses == self.mul_counter and self.number_of_learnt_clauses > 0:
            self.mul_counter *= 2
            return True
        else:
            return False
    # init static counter for fun above
    mul_counter = 10

    @register(FunType.VARIABLE, cli_arg='A', help_desc="Choose variable that reduces most clauses")
    def choose_with_most_reduction(self):
        if self.variables_to_use:
            maximum = 0
            var_to_return = None
            for var in self.variables_to_use:
                num = var.number
                lookup = self.next_iteration_lookup[num - 1]
                positives = sum(1 for x in lookup if x > 0)
                negatives = len(lookup) - positives
                if positives > maximum:
                    maximum = positives
                    var_to_return = var
                if negatives > maximum:
                    maximum = negatives
                    var_to_return = var
            # TODO: This should be handled different way. Since no more clauses take any effect on formula, meaning all clauses are empty
            # IF formula is satisfied by this substitution or not.
            if var_to_return is None:
                var_to_return = self.variables_to_use[-1] # in case all variables are empty
            return var_to_return
        else:
            return None

    @register(FunType.VARIABLE, cli_arg='H', help_desc="Choose var with most positive literals")
    def choose_var_based_on_number_of_pos(self):
        if self.variables_to_use:
            # return variable with maximum number of positive literals
            return max(self.variables_to_use, key=lambda x: sum(i>0 for i in self.next_iteration_lookup[x.number - 1]))
        else:
            return None

    @register(FunType.VARIABLE, cli_arg='B', help_desc="Choose based on basic probability - does not update each node")
    def choose_var_based_on_prob(self):
        if self.variables_to_use:
            var = max(self.variables_to_use, key=lambda x: abs(x.probability))
            return var
        else:
            return None

    @register(FunType.VARIABLE, cli_arg='N', help_desc="Choose next available variable")
    def choose_next_available_var(self):
        if self.variables_to_use:
            return self.variables_to_use[0]
        else:
            return None

    @register(FunType.VALUE, cli_arg='A',
              help_desc="Choose value based on current's node probability")
    def return_based_on_prob_rev(self):
        var = self.latest_var.number
        lookup = self.next_iteration_lookup[var-1]
        positives = sum(1 for x in lookup if x > 0)
        negatives = len(lookup) - positives
        return positives > negatives

    @register(FunType.VALUE, cli_arg='T', help_desc="Returns TRUE value if its possible")
    def return_true(self):
        return True

    @register(FunType.VALUE, cli_arg='F', help_desc="Returns FALSE value if its possible")
    def return_false(self):
        return False

    @register(FunType.VALUE, cli_arg='P',
              help_desc="Choose based on basic probability - does not update each node, true value prefered")
    def return_based_on_initial_prob_true(self):
        return self.latest_var.probability >= 0

    @register(FunType.VALUE, cli_arg='R',
              help_desc="Choose based on basic probability - does not update each node, false value prefered")
    def return_based_on_initial_prob_false(self):
        return self.latest_var.probability > 0

    @register(FunType.VALUE, cli_arg='N',
              help_desc="Choose value in oposition to initial probability")
    def return_based_on_initial_prob_rev(self):
        # Important note: need to make sure that no pure literal is here. It does not make sense then
        return not self.return_based_on_initial_prob_true

    @register(FunType.BACKTRACK, cli_arg='C', help_desc="Non-chronological backtracking based on learnt clause")
    def fall_back_to_learned_clause(self):
        learnt_clause = self.learnt_clause
        variables = [self.variables[abs(x)-1] for x in learnt_clause]
        level_of_variables = [x.level_of_decision for x in variables]
        set_of_levels = set(level_of_variables)
        l = heapq.nlargest(2, set_of_levels)
        level = l[1] if len(l) > 1 else l[0]
        search = True
        tn = self.current_node

        while search:
            if tn.variable.level_of_decision < level:
                if tn.left_child:
                    tn.left_checked = True
                else:
                    tn.right_checked = True
                search = False
            else:
                if not tn.parent:
                    if tn.left_checked and tn.right_checked:
                        # we reached top of the tree. Nothing more to search. UNSAT.
                        self.print_unsatisfability()
                    else:
                        search = False
                        self.main_node = None
                # unwind stack now
                if self.stack_of_forced_decisions and self.stack_of_forced_decisions[-1] == tn.variable:
                    # variable was forced to be picked
                    self.stack_of_forced_decisions.pop()
                else:
                    self.stack_of_guessed_decisions.pop()
                variable = tn.variable
                self.used_variables.remove(variable)
                self.variables_to_use.append(variable)
                temp_node = tn.parent
                self.current_node = temp_node
                tn.variable.previous_variable = None
                tn.variable.clause_that_lead_to_this_variable = None
                tn.variable.level_of_decision = -1
                del tn
                tn = temp_node
                if tn:
                    self.current_level_of_decision = tn.variable.level_of_decision
                else:
                    self.current_level_of_decision = 0
        if tn:
            lookup, clauses = self.update_lookup_and_clauses(tn.variable_lookup_valid_for_node,
                                                             tn.current_clauses,
                                                             tn.variable.number,
                                                             tn.left_child is not None and (tn.left_child.parent is tn))
        else:
            lookup, clauses = deepcopy(self.variable_lookup), deepcopy(self.clauses)
        self.next_iteration_clauses = clauses
        self.next_iteration_lookup = lookup

    @register(FunType.BACKTRACK, cli_arg='P', help_desc="Chronological backtracking")
    def fall_back_to_previous_node(self):
        search = True
        tn = self.current_node
        while search:
            if tn.variable in self.stack_of_guessed_decisions and (not tn.left_checked and not tn.right_checked):
                if tn.left_child:
                    tn.left_checked = True
                else:
                    tn.right_checked = True
                search = False
            else:
                # we reached top of the tree. Nothing more to search. UNSAT.
                if not tn.parent:
                    self.print_unsatisfability()
                # unwind stack now
                if self.stack_of_forced_decisions and self.stack_of_forced_decisions[-1] == tn.variable:
                    # variable was forced to be picked
                    self.stack_of_forced_decisions.pop()
                else:
                    self.stack_of_guessed_decisions.pop()
                variable = tn.variable
                self.used_variables.remove(variable)
                self.variables_to_use.append(variable)
                temp_node = tn.parent
                self.current_node = temp_node
                tn.variable.previous_variable = None
                tn.variable.clause_that_lead_to_this_variable = None
                tn.variable.level_of_decision = -1
                del tn
                tn = temp_node
                self.current_level_of_decision = tn.variable.level_of_decision
        lookup, clauses = self.update_lookup_and_clauses(tn.variable_lookup_valid_for_node,
                                                         tn.current_clauses,
                                                         tn.variable.number,
                                                         not tn.left_checked)

        self.next_iteration_clauses = clauses
        self.next_iteration_lookup = lookup

