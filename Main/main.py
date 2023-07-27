import os
import psutil
import time
import subprocess
from datalogrulemapper import *


def measure_usage(processid):

    # Get the CPU and memory usage of the command prompt process
    cpu_usage = psutil.Process(processid).cpu_percent()
    memory_usage = psutil.Process(processid).memory_info().rss /1024/1024
    
    # Get the CPU frequency of the system
    cpu_frequency = psutil.cpu_freq().current

    print(f"CPU Usage: {cpu_usage}%")
    print(f"Memory Usage: {memory_usage} MB")
    print(f"CPU Frequency: {cpu_frequency} MHz")
    

def get_rls_file_paths(directory):
    rls_file_paths = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".rls"):
                file_path = os.path.join(root, file)
                rls_file_paths.append(file_path)
    return rls_file_paths

def get_clingo_location(ex_name):

    directory_path = os.path.join("clingo/", ex_name)
    os.makedirs(directory_path, exist_ok=True)

    clingo_location = f"{directory_path}/{ex_name}"

    return clingo_location

def save_clingo_output(loc_rule_head_predicate):

    for output_file, rule_head_preds in loc_rule_head_predicate.items():
        models = []

        with open(f"{output_file}-output.txt", 'r') as file:
            output_list = file.readlines()
            symbols=output_list[4].strip().split()

        for symbol in symbols:
            model = clingo.parse_term(symbol)
            models.append(model)
        
        # Find the last occurrence of "/"
        index = output_file.rfind("/")
        new_path = output_file[:index+1]
        #print(new_path)

        directory_path = os.path.join(new_path, "Output")
        os.makedirs(directory_path, exist_ok=True)

        output_sav_loc = directory_path

        #print(list(set(rule_head_preds)))
        for pred in list(set(rule_head_preds)):
            output_list = [[const.name for const in model.arguments] for model in models if pred == model.name]
            output_df = pd.DataFrame(output_list)
            output_df.to_csv(f"{output_sav_loc}/{pred}.csv",  index=False, header=False)

def run_clingo(files_location):
    
    commands = []

    for file in files_location:
        commands.append(f"clingo {file}-facts.lp {file}.lp > {file}-output.txt")

    # Start measuring
    start_time = time.time()
    cmd_process = subprocess.Popen(['cmd'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)

    # Execute each command in the command prompt
    for command in commands:
        print("Executing Command: ", command)
        # Send the command to the command prompt process
        cmd_process.stdin.write(command.encode('utf-8') + b'\n')
        cmd_process.stdin.flush()
    
    #print(cmd_process.pid)

    measure_usage(cmd_process.pid)

    # Close the command prompt process
    cmd_process.stdin.close()

    # Calculate the execution time
    execution_time = (time.time() - start_time)*1000
    print(f"Execution Time: {execution_time} ms")


    cmd_process.stdout.read()
    cmd_process.stdout.close()

    save_clingo_output(loc_and_rule_head_predicates)


def main():

    #Dictionary to save locaion and rule head Predicates
    sav_loc_and_rule_head_predicates = {}

    ruleMapper = DatalogRuleMapper()
    RuleParser, Rule = ruleMapper.start_jvm()

    #Added the parser to use the code as tool
    parser = argparse.ArgumentParser()
    parser.add_argument('--solver', required=True, type=str, choices=['clingo', 'nemo', 'rulewerk', 'souflle'])
    parser.add_argument('--input_dir', type=str, required=True)

    args = parser.parse_args()

    rule_file_path = args.input_dir
    rls_files = get_rls_file_paths(rule_file_path)

    if args.solver == 'clingo':
        
        #Converting Rulewerk Rule file into Clingo rules file
        for rls in rls_files:
            rules, facts, data_sources, example_name = ruleMapper.rulewerktoobject(rls, RuleParser)
            saving_location = get_clingo_location(example_name)
            rule_head_preds = ruleMapper.rulewerk_to_clingo(rules, facts, data_sources, saving_location)

            #Dictionary {"rule_file_location": [list of rule head predicates]........}
            sav_loc_and_rule_head_predicates[saving_location] = rule_head_preds

        run_clingo(sav_loc_and_rule_head_predicates)

    elif args.solver == 'nemo':
        print("nemo")
    elif args.solver == 'rulewerk':
        print("rulewerk")
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

