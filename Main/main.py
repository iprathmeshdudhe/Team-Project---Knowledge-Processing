import os
import argparse
from datalogrulemapper import *
import datetime
import sys
# from clingo_controller import ClingoController
from rulewerk_controller import RulewerkController
from nemo_controller import NemoController

def get_rls_file_paths(directory):
    rls_file_paths = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".rls"):
                file_path = os.path.join(root, file)
                rls_file_paths.append(file_path)
    return rls_file_paths



def main():
    
    #Dictionary to save locaion and rule head Predicates
    sav_loc_and_rule_head_predicates = {}

    ruleMapper = DatalogRuleMapper()
    RuleParser, Rule, Literal = ruleMapper.start_jvm()

    #Added the parser to use the code as tool
    parser = argparse.ArgumentParser()
    parser.add_argument('--solver', required=True, type=str, choices=['clingo', 'nemo', 'rulewerk', 'souffle', 'all'])
    parser.add_argument('--input_dir', type=str, required=True)
    parser.add_argument('--task_name', type=str, required=True)

    args = parser.parse_args()

    rule_file_path = args.input_dir

    try:
        rls_files = get_rls_file_paths(rule_file_path)
    except:
        print("Could not find directory!", err)
        raise
        sys.exit(1)

    timestamp = datetime.datetime.now().strftime("%d-%m-%Y @%H:%M:%S")

    task = args.task_name

    if args.solver == 'clingo':
        pass
        # run_clingo(rls_files, RuleParser)
      
    elif args.solver == 'nemo':
        run_nemo(rls_files, timestamp, task)

    elif args.solver == 'rulewerk':
        run_rulewerk(rls_files, RuleParser, Rule, Literal, rule_file_path, timestamp, task)

    elif args.solver == 'souffle':
        print("souffle")
        # run_souffle(rule_file_path, RuleParser)
        
    elif args.solver == 'all':
        print("all")
        # run_clingo(rls_files, RuleParser)
        run_nemo(rls_files, timestamp, task)
        run_rulewerk(rls_files, RuleParser, Rule, Literal, rule_file_path, timestamp, task)
        # run_souffle(rule_file_path, RuleParser)

    ruleMapper.stop_jvm()

def run_rulewerk(rls_files, RuleParser, Rule, Literal, rule_file_path, timestamp, task):
    rc = RulewerkController()
    query_dict={}
    try:
        for rls in rls_files:
            file_name = os.path.basename(rls)
            query, head_pred = rc.rulefileElements(RuleParser, Rule, Literal, rls)
            query_dict[rls]=[query, head_pred]
        execution_time, memory_info = rc.runRulewerk(rule_file_path, query_dict)
        #call function to write bencmarking results to csv file
        write_benchmark_results(timestamp, task, "Rulewerk", execution_time, memory_info, 10)
    except Exception as err:
        print("An exception occurred: ", err)

def run_clingo(rls_files, RuleParser):
    cc = ClingoController()
        
    #Converting Rulewerk Rule file into Clingo rules file
    for rls in rls_files:
        rules, facts, data_sources, example_name = ruleMapper.rulewerktoobject(rls, RuleParser)
        saving_location = cc.get_clingo_location(example_name)
        rule_head_preds = ruleMapper.rulewerk_to_clingo(rules, facts, data_sources, saving_location)

        #Dictionary {"rule_file_location": [list of rule head predicates]........}
        sav_loc_and_rule_head_predicates[saving_location] = rule_head_preds

    c_memory, c_exec_time,  c_count_ans = cc.run_clingo(sav_loc_and_rule_head_predicates)
    write_benchmark_results(timestamp, task, "Nemo", c_exec_time, c_memory, c_count_ans)

def run_nemo(rls_files, timestamp, task):
    nc = NemoController()
    rls_file_list = []
    try:
        for rls in rls_files:
            rule_file_name = os.path.basename(rls)
            rule_file_path = os.path.dirname(rls)
            rls_file_list.append([rule_file_name, rule_file_path])
        execution_time, memory_info = nc.runNemo(rls_file_list) 

        #call function to write bencmarking results to csv file
        write_benchmark_results(timestamp, task, "Nemo", execution_time, memory_info, 10)
    except Exception as err:
        print("An exception occurred: ", err)

def run_souffle(rule_file_path, RuleParser):
    type_declarations, facts_list, rules_list, query = ruleMapper.rulewerk_to_souffle(rule_file_path, RuleParser)
    with open('souffle-example.dl', 'w') as output_file:
        output_file.write('// Declarations\n')
        output_file.writelines('\n'.join(type_declarations))
        output_file.write('\n\n')
        output_file.write('// Facts\n')
        output_file.writelines('\n'.join(facts_list))
        output_file.write('\n\n')
        output_file.write('// Rules\n')
        output_file.writelines('\n'.join(rules_list))
        output_file.write('\n\n')
        output_file.write('// Query\n')
        output_file.writelines('\n'.join(query))
        output_file.write('\n\n')

def write_benchmark_results(timestamp, task, tool, execution_time, memory_info, count):
    #if not csv file exist create a new one : in which directory?
    #header: timestamp task, tool, execution_time, memory_info
    #row: parameters in order
    #close csv
    flag=os.path.exists("BenchResults.csv")
    #print(flag)
    with open("BenchResults.csv", mode='a', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        if flag:
            pass
        else:
            dw = csv.DictWriter(csv_file, delimiter=',', fieldnames=["Timestamp (YYYY-MM-DD HH:MM:SS)", "Task", "Tool", "Execution Time (ms)", "Memory Info (MB)", "Count of grounded Rule Predicates"])
            dw.writeheader()
        csv_writer.writerow([timestamp, task, tool, execution_time, memory_info, count])

if __name__ == '__main__':
    main()

