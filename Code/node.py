from math import copysign


def getClause(fileName):
    with open(fileName, 'r') as my_file:
        clauseList = []
        variableList = []
        clauseNumber = 1
        for line in my_file.readlines():
            if line[0] == 'p':
                varNr, clauseNr = map(int, line.strip().split(" ")[2:4])
                for i in range(varNr):
                    variableList.append([])
            elif line[0] != 'c' and line[len(line.strip()) - 1] == "0":
                clauseList.append([int(a) for a in line.strip().split(" ")][:-1])
                for i in clauseList[len(clauseList) - 1]:
                    variableList[abs(i) - 1].append(int(copysign(clauseNumber, i)))
                clauseNumber += 1
    return clauseList, variableList


class Variable:
    def __init__(self):
        self.number = -1

        self.previous_variable = None
        self.clause_that_lead_to_this_variable = None
        self.level_of_decision = -1
        self.probability = -1

    def __repr__(self):
        # just for debugging, if you want to printout variable -- it prints its number
        return "Number = " + str(self.number)


class Node:
    instances = []

    def __init__(self, var, parent=None):
        Node.instances.append(self)
        self.variable = var
        self.parent = parent

        # each list is variable.
        # each element inside list is clause
        self.variable_lookup_valid_for_node = []

        self.current_clauses = []

        # Is entire left/right "checked" - to avoid checking same leafs twice
        self.left_checked = False
        self.right_checked = False

        self.left_child = None
        self.right_child = None

        # depth of Tree
        if not parent:
            self.tree_depth = 1
        else:
            self.tree_depth = parent.tree_depth + 1
