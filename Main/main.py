import os
import argparse
from datalogrulemapper import *
import datetime
import sys
from clingo_controller import ClingoController
from rulewerk_controller import RulewerkController
from nemo_controller import NemoController
import traceback
import json

def input_path_error(exc):
    #if given rls file path does not exist then raise error
    raise exc

def get_rls_file_paths(directory):
    rls_file_paths = []
    for root, dirs, files in os.walk(directory, onerror= input_path_error):
        for file in files:
            if file.endswith(".rls"):
                file_path = os.path.join(root, file)
                rls_file_paths.append(file_path)
    return rls_file_paths\

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

def get_config(config_file_path):
    try:
        config_file = open(config_file_path)
    except Exception as exc:
        sys.exit(exc)
        
    configs = json.load(config_file)
    tasks = configs['tasks']
    solvers = configs['solvers']
    return solvers, tasks

def main():
    
    #Dictionary to save locaion and rule head Predicates
    sav_loc_and_rule_head_predicates = {}

    ruleMapper = DatalogRuleMapper()
    RuleParser, Rule, Literal = ruleMapper.start_jvm()

    #Added the parser to use the code as tool
    parser = argparse.ArgumentParser()

    parser.add_argument('--config_file', type=str, required=True)
    # parser.add_argument('--solver', required=True, type=str, choices=['clingo', 'nemo', 'rulewerk', 'souffle', 'all'])
    # parser.add_argument('--input_dir', type=str, required=True)
    # parser.add_argument('--task_name', type=str, required=True)

    args = parser.parse_args()
    print(args.config_file)

    solvers, tasks = get_config(args.config_file)

    for task in tasks:
        rule_file_path = task['path']
        task_name = task['name']

        try:
            rls_files = get_rls_file_paths(rule_file_path)
        except Exception as exc:
            sys.exit(exc)

        timestamp = datetime.datetime.now().strftime("%d-%m-%Y @%H:%M:%S")

        for solver in solvers:
            if solver.lower() == 'clingo':
                run_clingo(rls_files, task_name, timestamp, RuleParser)
            elif solver.lower() == 'nemo':
                run_nemo(rls_files, timestamp, task_name)
            elif solver.lower() == 'rulewerk':
                run_rulewerk(rls_files, RuleParser, Rule, Literal, rule_file_path, timestamp, task_name)
            elif solver.lower() == 'souffle':
                print("souffle")
                # run_souffle(rule_file_path, RuleParser)
            elif solver.lower() == 'all':
                run_clingo(rls_files, task_name, timestamp, RuleParser)
                run_nemo(rls_files, timestamp, task_name)
                run_rulewerk(rls_files, RuleParser, Rule, Literal, rule_file_path, timestamp, task_name)
                # run_souffle(rule_file_path, RuleParser)  
            else:
                sys.exit(Exception(f'"{solver}"-Solver not recognized! Please check your config file.'))
            
    ruleMapper.stop_jvm()

def run_rulewerk(rls_files, RuleParser, Rule, Literal, rule_file_path, timestamp, task):
    rc = RulewerkController()
    query_dict={}
    result_count = 0
    try:
        for rls in rls_files:
            file_name = os.path.basename(rls)
            query, head_pred = rc.rulefileElements(RuleParser, Rule, Literal, rls)
            query_dict[rls]=[query, head_pred]
        execution_time, memory_info, result_count = rc.runRulewerk(rule_file_path, query_dict)
        #call function to write bencmarking results to csv file
        write_benchmark_results(timestamp, task, "Rulewerk", round(execution_time, 2), round(memory_info, 2), round(int(result_count), 2))
    except Exception as err:
        print("An exception occurred: ", err)

def run_clingo(rls_files, task, timestamp, RuleParser):
    print(rls_files)
    cc = ClingoController()
    ruleMapper = DatalogRuleMapper()
    sav_loc_and_rule_head_predicates = {}
    #Converting Rulewerk Rule file into Clingo rules file
    for rls_file in rls_files:        
        file_name = os.path.basename(rls_file)
        file_path = os.path.dirname(rls_file)
        rules, facts, data_sources, example_name = ruleMapper.rulewerktoobject(rls_file, RuleParser)
  
        
        saving_location = cc.get_clingo_location(example_name)
        rule_head_preds = ruleMapper.rulewerk_to_clingo(file_path, rules, facts, data_sources, saving_location)

        #Dictionary {"rule_file_location": [list of rule head predicates]........}
        sav_loc_and_rule_head_predicates[saving_location] = rule_head_preds

    c_memory, c_exec_time,  c_count_ans = cc.run_clingo(sav_loc_and_rule_head_predicates)
    write_benchmark_results(timestamp, task, "Clingo", c_exec_time, c_memory, c_count_ans)

def run_nemo(rls_files, timestamp, task):
    nc = NemoController()
    rls_file_list = []
    try:
        for rls in rls_files:
            rule_file_name = os.path.basename(rls)
            rule_file_path = os.path.dirname(rls)
            rls_file_list.append([rule_file_name, rule_file_path])
        execution_time, memory_info, result_count = nc.runNemo(rls_file_list) 

        #call function to write bencmarking results to csv file
        write_benchmark_results(timestamp, task, "Nemo", round(execution_time, 2), round(memory_info, 2), round(int(result_count), 2))
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


if __name__ == '__main__':
    main()

