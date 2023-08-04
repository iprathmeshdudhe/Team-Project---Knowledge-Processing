import os
import argparse
from datalogrulemapper import *
from rulewerk_controller import *
import datetime
from clingo_controller import ClingoController

#--keep this in main.py (here)
def get_rls_file_paths(directory):
    rls_file_paths = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".rls"):
                file_path = os.path.join(root, file)
                rls_file_paths.append(file_path)
    return rls_file_paths

def main():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    #Dictionary to save locaion and rule head Predicates
    sav_loc_and_rule_head_predicates = {}

    ruleMapper = DatalogRuleMapper()
    RuleParser, Rule, Literal = ruleMapper.start_jvm()

    #Added the parser to use the code as tool
    parser = argparse.ArgumentParser()
    parser.add_argument('--solver', required=True, type=str, choices=['clingo', 'nemo', 'rulewerk', 'souflle'])
    parser.add_argument('--input_dir', type=str, required=True)

    args = parser.parse_args()

    rule_file_path = args.input_dir
    rls_files = get_rls_file_paths(rule_file_path)

    if args.solver == 'clingo':

        cc = ClingoController()
        
        #Converting Rulewerk Rule file into Clingo rules file
        for rls in rls_files:
            rules, facts, data_sources, example_name = ruleMapper.rulewerktoobject(rls, RuleParser)
            saving_location = cc.get_clingo_location(example_name)
            rule_head_preds = ruleMapper.rulewerk_to_clingo(rules, facts, data_sources, saving_location)

            #Dictionary {"rule_file_location": [list of rule head predicates]........}
            sav_loc_and_rule_head_predicates[saving_location] = rule_head_preds

        c_memory, c_exec_time = cc.run_clingo(sav_loc_and_rule_head_predicates)

    elif args.solver == 'nemo':
        rls_file_list = []
        for rls in rls_files:
            rule_file_name = os.path.basename(rls)
            rule_file_path = os.path.dirname(rls)
            rls_file_list.append([rule_file_name, rule_file_path])
        execution_time, memory_info = runNemo(rls_file_list)

        #call function to write bencmarking results to csv file
        write_benchmark_results(timestamp, "random_taskname_for_now", "Nemo", execution_time, memory_info)  # TODO add count of grounded atoms

    elif args.solver == 'rulewerk':
        query_dict={}
        for rls in rls_files:
            file_name = os.path.basename(rls)
            query, head_pred = rulefileElements(RuleParser, Rule, Literal, rls)
            query_dict[rls]=[query, head_pred]
        execution_time, memory_info = runRulewerk(rule_file_path, query_dict)
        #call function to write bencmarking results to csv file
        write_benchmark_results(timestamp, "random_taskname_for_now", "Rulewerk", execution_time, memory_info) # TODO add count of grounded atoms

    elif args.solver == 'souflle':
        print("souflle")
        type_declarations, facts_list, rules_list, query = ruleMapper.rulewerk_to_souffle(rule_file_path, RuleParser)
        # TODO add handling of data sources
        # TODO do
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



    ruleMapper.stop_jvm()


def write_benchmark_results(timestamp, task, tool, execution_time, memory_info):
    #if not csv file exist create a new one : in which directory?
    #header: timestamp task, tool, execution_time, memory_info
    #row: parameters in order
    #close csv
    flag=os.path.exists("BenchResults.csv")
    print(flag)
    with open("BenchResults.csv", mode='a', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        if flag:
            # TODO add new ruled to the existing file if it exists
            pass
        else:
            dw = csv.DictWriter(csv_file, delimiter=',', fieldnames=["Timestamp", "Task", "Tool", "Execution Time (ms)", "Memory Info (MB)", "Count of grounded atoms"])
            dw.writeheader()
        csv_writer.writerow([timestamp, task, tool, execution_time, memory_info]) # TODO add count of grounded atoms

if __name__ == '__main__':
    main()

