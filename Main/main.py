import os
import argparse
from datalogrulemapper import *
from rulewerk_controller import *
from clingo_controller import ClingoController

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
        for rls in rls_files:
            runNemo(rls)

    elif args.solver == 'rulewerk':
        query_dict={}
        for rls in rls_files:
            file_name = os.path.basename(rls)
            query, head_pred = rulefileElements(RuleParser, Rule, Literal, rls)
            query_dict[rls]=[query, head_pred]
        runRulewerk(rule_file_path, query_dict)

    elif args.solver == 'souflle':
        print("souflle")
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



    ruleMapper.stop_jvm()

if __name__ == '__main__':
    main()

