import copy
from random import randrange
import sys

def count_distinct_numbers(lst):
    '''
    list of int) -> int
    Return the number of distinct numbers appeared in a list.
    >>> a = [1,1,2,3,4]
    >>> print(count_distinct_numbers(a))
    4
    '''
    count = 1
    _lst = copy.deepcopy(lst)
    for i in range(1,len(_lst)):
        if _lst[i] in _lst[:i]:
            continue
        else:
            count += 1
    return count

def write_output(output_file, output):
    for i in range(len(output)):
        output_file.write(str(output[i]) + ' ')
    output_file.write('\n')
        
class ProcessAssignment:
    def __init__(self):
	# variables involved with processes
        self.process = [] 	# list of list of int. stands for resources needed by each process
        self.pmcost = []	# list of int
        self.service = [] 	# list of int. each process's service number

        self.spread = []	

	# variables involved with machines
        self.hard_capacity = []
        self.soft_capacity = []      
        self.location = []         
        
        self.initial_assign = []
        self.best_assign = []
        self.best_assign_cost = 0
        self.assign = []
        self.cost = 0

        self.N_r = 0
        self.N_m = 0
        self.N_s = 0
        self.N_p = 0

	# variables invovled for checking condidtions and computing cost
        self.useage = []
        self.record = []
        self.service_to_location = []      

        self.tabu = []

        # output filename
        self.output_file_name = ''
    # parser for input files
    def string_to_number(self, line):
        '''
        (str) -> list of int
        Convert numbers in a string to integer numbers stored in a list.
        '''
        numbers = []
        number_by_str = ''
        for char in line:
            if char != ' ':
                number_by_str += char
            else:
                numbers.append(int(number_by_str))
                number_by_str = ''
        numbers.append(int(number_by_str))

        return numbers

    def read_machine(self,file):
        location = []
        hard_capacity = []
        soft_capacity = []
        for i in range(self.N_m):
            line = file.readline().strip()
            numbers = self.string_to_number(line)

            location.append(numbers[0])
            hard_capacity.append(numbers[1:self.N_r+1])
            soft_capacity.append(numbers[self.N_r+1:])
            
        return  location, hard_capacity, soft_capacity

    def read_process(self,file):
        process = []
        pmcost = []
        service = []
        
        for i in range(self.N_p):
            line = file.readline().strip()
            numbers = self.string_to_number(line)

            service.append(numbers[0])
            process.append(numbers[1:self.N_r+1])
            pmcost.append(numbers[-1])

        return process, pmcost, service
		
    def read_data(self, instance, assign):
        '======================read instance========================'
        file = open(instance)
        self.N_r = int(file.readline().strip())
        
        self.N_m = int(file.readline().strip())
        self.location, self.hard_capacity, self.soft_capacity = self.read_machine(file)

        self.N_s = int(file.readline().strip())
        for i in range(self.N_s):
            self.spread.append(int(file.readline().strip()))

        self.N_p = int(file.readline().strip())
        self.process, self.pmcost, self.service = self.read_process(file)
        file.close()

        '====================read initial assignment==================='
        file = open(assign)
        line = file.readline().strip()
        self.initial_assign = self.string_to_number(line)
        self.assign = copy.deepcopy(self.initial_assign)
        self.best_assign = copy.deepcopy(self.initial_assign)
        #self.tabu.append(self.best_assign)
        file.close()

    # this function builds values associated with initial assign
    def build(self):
        # compute useage
        self.useage = [[0 for i in range(self.N_r)] for j in range(self.N_m)]
        for i in range(self.N_p):
            for j in range(self.N_r):
                self.useage[self.initial_assign[i]][j] += self.process[i][j]
               
        # record the service to machine deploy of the initial assign
        for i in range(self.N_p):
            self.record.append(str(self.service[i]) + ' ' + str(self.initial_assign[i]))
            #without this ' ' it may incur error. for example, 2 + 10 == 21 + 0

        # compute service to location assign
        self.service_to_location = [[] for i in range(self.N_s)]
        for i in range(self.N_p):
            service_num = self.service[i]
            location = self.location[self.initial_assign[i]]
            self.service_to_location[service_num].append(location)

        # compute mlcost of initial assign
        for i in range(self.N_m):
            for j in range(self.N_r):
                if self.useage[i][j] > self.soft_capacity[i][j]:
                    self.cost += self.useage[i][j] - self.soft_capacity[i][j]

        self.best_assign_cost = self.cost

    # this function test whether a new assign satisfies those conditions
    def test(self, p, m):
        return self.serv_conflict_con(p, m) and self.serv_spread_con(p, m) and self.memo_cap_con(p, m)

    '''
    All constraint functions only checks whether the assign satisfies thses conditions
    but didn't modify self.useage    self.record  self.service_to_location 
    '''
    def serv_conflict_con(self, p, m):
        '''
        if process has been assigned to machine m in the new assign,
        this function returns True if no process belongs to the same
        servie number of p has been assigned to machine m
        '''
        deploy = str(self.service[p]) + ' ' + str(m)
        return not(deploy in self.record)
    
    def memo_cap_con(self, p, m):
        useage_m = copy.deepcopy(self.useage[m])
        for j in range(self.N_r):
            useage_m[j] += self.process[p][j]
            if useage_m[j] > self.hard_capacity[m][j]:
                return False
        return True

    def serv_spread_con(self, p, m):
        service_num = self.service[p]
        _s_t_l = copy.deepcopy(self.service_to_location[service_num])        
        _s_t_l.remove(self.location[self.assign[p]])
        _s_t_l.append(self.location[m])

        return count_distinct_numbers(_s_t_l) > self.spread[service_num]

    # compute cost    
    def compute_cost(self, p, m):
        return  self.MLCost(p, m) + self.PMCost(p, m)

    def PMCost(self, p, m):
        # no need to consider self.assign[p] == self.initial_assign[p] and m == self.initial_assign[p]
        # because that means self.assign[p] == m which is not a neighbour and it won't be computed
    
        if self.assign[p] != self.initial_assign[p] and m == self.initial_assign[p]:
            return -self.pmcost[p]
        if self.assign[p] == self.initial_assign[p] and m != self.initial_assign[p]:
            return self.pmcost[p]
        if self.assign[p] != self.initial_assign[p] and m != self.initial_assign[p]:
            return 0
        
    def MLCost(self, p, m):       
        cost = 0
        useage_m = copy.deepcopy(self.useage[m])
        previous_machine = self.assign[p]
        useage_previous_machine = copy.deepcopy(self.useage[previous_machine])
        
        for j in range(self.N_r):
            if useage_m[j] > self.soft_capacity[m][j]:
                cost += self.process[p][j]
            else:
                useage_m[j] = useage_m[j] + self.process[p][j]
                if useage_m[j] > self.soft_capacity[m][j]:
                    cost += (useage_m[j] - self.soft_capacity[m][j])

            if useage_previous_machine[j] < self.soft_capacity[previous_machine][j]:
                continue
            if useage_previous_machine[j] - self.process[p][j] < self.soft_capacity[previous_machine][j]:
                cost = cost - (useage_previous_machine[j] - self.soft_capacity[previous_machine][j])
            else:
                cost = cost - self.process[p][j]
        return cost

    # tabu search
    def tabu_search(self):
        i = 0
        output_file = open(self.output_file_name, 'w')
        while True:
            if i > 200:
                self.tabu.pop(0)
                
            neighbour, cost = self.generate_neighbour()
            self.change_assign(neighbour[0], neighbour[1], cost)
            if self.cost < self.best_assign_cost:
                self.best_assign = copy.deepcopy(self.assign)
                self.best_assign_cost = self.cost
                print(self.best_assign_cost)
                write_output(output_file, self.best_assign)
##                print(self.best_assign)
            self.tabu.append(neighbour)
            i += 1
        output_file.close()   

    def generate_neighbour(self):
        '''
        Return the best neighbour of current assign.
        '''
        neighbour = []
        cost = []
        for i in range(int(0.1 * self.N_p)):
            p = randrange(self.N_p)
            for m in range(self.N_m):
                if self.assign[p] == m:
                    continue
                if [p, m] in self.tabu:
                    if self.test(p, m) and ( self.cost + self.compute_cost(p, m) < self.best_assign_cost):
                        return [p, m], self.compute_cost(p, m)
                    continue
                if self.test(p, m):
                    neighbour.append([p,m])
                    cost.append(self.compute_cost(p,m))
        return neighbour[cost.index(min(cost))], min(cost)

    def change_assign(self, p, m, cost):
        '''
        five variables need to be changed:

        self.useage = []
        self.record = []
        self.service_to_location = []    
        self.cost = 0
        '''
        previous_machine = self.assign[p]
        service_number = self.service[p]
        # change self.record
        deploy = str(service_number) + ' ' + str(previous_machine)
        self.record.remove(deploy)
        deploy = str(service_number) + ' ' + str(m)
        self.record.append(deploy)

        # change self.service_to_location
        self.service_to_location[service_number].remove(self.location[previous_machine])
        self.service_to_location[service_number].append(self.location[m])

        # change self.useage
        for j in range(self.N_r):
            self.useage[previous_machine][j] -= self.process[p][j]
            self.useage[m][j] += self.process[p][j]

        # change self.cost
        self.cost += cost

        # change self.assign
        self.assign[p] = m
        
if __name__ == '__main__':
    instance_file = sys.argv[1]
    assign_file = sys.argv[2]
    
    trial = ProcessAssignment()
    trial.read_data(instance_file, assign_file)
    trial.output_file_name = sys.argv[3]
    trial.build()
    trial.tabu_search()   
    
