import argparse
import sys
import os.path
import psutil
import subprocess
import time
import platform
import datetime
import json
import threading

from datalogrulemapper import *

from src.errors import NoRlsFilesFound, DirectoryNotFound, SystemNotSupported, input_path_error
from src.config import Settings
from clingo_controller import ClingoController
from rulewerk_controller import RulewerkController
from nemo_controller import NemoController
import traceback
import json
import sys
from loguru import logger

# sys.tracebacklimit = 0

def input_path_error(exc):
    #if given rls file path does not exist then raise error
    raise exc
from souffle_controller import SouffleController

def measure_memory(pid, mu):

    process = psutil.Process(pid)
    
    try:

        while process.is_running():
            mu.append((process.memory_info().rss) / (1024 * 1024))
    
    except psutil.NoSuchProcess:
        print("No Such Process Exist. Or Process finished executing.")
        pass
        
def monitor_process(commands):

    memory_usage = []
    
    system = platform.system()
    if system == "Windows":
        args = ["cmd"]
    elif system == "Darwin":  # Mac OS
        args = ["ls", "-l"]
    else:
        raise SystemNotSupported(f"The system {system} is not supported")

    cmd_process = subprocess.Popen(
        args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False
    )

    #Creating a thread to measure memory in backend
    thread = threading.Thread(target=measure_memory, args=(cmd_process.pid, memory_usage))
    thread.start()

    #Start Measuring Time 
    start_time = time.perf_counter()
    
    try:
        for command in commands:
            print("\nExecuting Command: ", command)
            # Send the command to the command prompt process
            cmd_process.stdin.write(command.encode("utf-8") + b"\n")
            cmd_process.stdin.flush()
            
        
        # Close the command prompt process
        # stdout, stderr = cmd_process.communicate()
        # print(stdout.decode())
        # print(stderr.decode())

        cmd_process.stdin.close()

        while cmd_process.poll() is None:                     
            pass

        # Calculate the execution time            
        execution_time = (time.perf_counter() - start_time) * 1000
        

    except Exception as err:
        raise err
    
    else:
        memory_usage = max(memory_usage)
        return round(memory_usage, 2), round(execution_time, 2)
    


def get_rls_file_paths(directory):
    rls_file_paths = []
    for root, dirs, files in os.walk(directory, onerror=input_path_error):
        for file in files:
            if file.endswith(".rls"):
                file_path = os.path.join(root, file)
                rls_file_paths.append(file_path)
    return rls_file_paths


def write_benchmark_results(timestamp, task, tool, execution_time, memory_info, count):
    # if not csv file exist create a new one : in which directory?
    # header: timestamp task, tool, execution_time, memory_info
    # row: parameters in order
    # close csv
    flag = os.path.exists("BenchResults.csv")
    with open("BenchResults.csv", mode="a", newline="") as csv_file:
        csv_writer = csv.writer(csv_file)
        if flag:
            pass
        else:
            dw = csv.DictWriter(
                csv_file,
                delimiter=",",
                fieldnames=[
                    "Timestamp (YYYY-MM-DD HH:MM:SS)",
                    "Task",
                    "Tool",
                    "Execution Time (ms)",
                    "Memory Info (MB)",
                    "Count of grounded Rule Predicates",
                ],
            )
            dw.writeheader()
        csv_writer.writerow([timestamp, task, tool, execution_time, memory_info, count])


def get_config(config_file_path):
    try:
        config_file = open(config_file_path)
    except Exception as exc:
        logger.exception(exc)
        sys.exit(1)

    configs = json.load(config_file)
    tasks = configs["tasks"]
    solvers = configs["solvers"]
    return solvers, tasks


def run_rulewerk(rls_files, RuleParser, Rule, Literal, rule_file_path, timestamp, task):
    rc = RulewerkController()
    query_dict = {}
    result_count = 0
    try:
        for rls in rls_files:
            file_name = os.path.basename(rls)
            query, head_pred = rc.get_rule_file_elements(RuleParser, Rule, Literal, rls)
            query_dict[rls] = [query, head_pred]
        rulewerk_commands = rc.get_rulewerk_commands(rule_file_path, query_dict)
        r_memory, r_exec_time = monitor_process(rulewerk_commands)

        result_count = rc.count_rulewerk_results(query_dict)
        # call function to write bencmarking results to csv file
        write_benchmark_results(
            timestamp, task, "Rulewerk", r_exec_time, r_memory, result_count
        )
    except Exception as err:
        logger.error(err)


def run_clingo(rls_files, task, timestamp, RuleParser, ruleMapper):
    # Dictionary to save locaion and rule head Predicates
    sav_loc_and_rule_head_predicates = {}

    cc = ClingoController()

    # Converting Rulewerk Rule file into Clingo rules file
    for rls in rls_files:
        # file_name = os.path.basename(rls)
        file_path = os.path.dirname(rls)

        rules, facts, data_sources, example_name = ruleMapper.rulewerktoobject(rls, RuleParser)
        saving_location = cc.get_clingo_location(example_name)
        rule_head_preds = ruleMapper.rulewerk_to_clingo(file_path, rules, facts, data_sources, saving_location)
        # Dictionary {"rule_file_location": [list of rule head predicates]........}
        sav_loc_and_rule_head_predicates[saving_location] = rule_head_preds

    clingo_commands = cc.get_clingo_commands(sav_loc_and_rule_head_predicates)
    c_memory, c_exec_time = monitor_process(clingo_commands)

    #Insert delay so that the outputs= files gets created
    time.sleep(5)
    
    c_count_ans = cc.save_clingo_output(sav_loc_and_rule_head_predicates)

    # call function to write benchmarking results to csv file
    write_benchmark_results(
        timestamp, task, "Clingo", c_exec_time, c_memory, c_count_ans
    )  # add count of grounded atoms


def run_nemo(rls_files, timestamp, task):
    nc = NemoController()
    rls_file_list = []
    try:
        for rls in rls_files:
            rule_file_name = os.path.basename(rls)
            rule_file_path = os.path.dirname(rls)
            rls_file_list.append([rule_file_name, rule_file_path])
        nemo_commands = nc.get_nemo_commands(rls_file_list)
        n_memory, n_exec_time = monitor_process(nemo_commands)
        result_count = nc.count_results(rls_file_list)
        # execution_time, memory_info, result_count = nc.runNemo(rls_file_list)

        # # call function to write bencmarking results to csv file
        write_benchmark_results(
            timestamp, task, "Nemo", n_exec_time, n_memory, result_count
        )
    except Exception as err:
        print(traceback.format_exc())
        logger.error(err)


def run_souffle(rls_files, timestamp, task, RuleParser, ruleMapper):
    sc = SouffleController()
    commands = []
    c_count_ans = 0
    folders_to_create = []

    for rls in rls_files:
        rls_basename = os.path.basename(rls)
        dir_fullname = os.path.dirname(rls)
        dir_basename = os.path.basename(dir_fullname)
        folder_to_create = os.path.join("souffle", dir_basename)
        folders_to_create.append(folder_to_create)
        os.makedirs(folder_to_create, exist_ok=True)

        rules, facts, data_sources, _ = ruleMapper.rulewerktoobject(rls, RuleParser)
        souffle_type_declarations, souffle_facts_list, souffle_rules_list, query_list = ruleMapper.rulewerk_to_souffle(
            rules, facts
        )

        saving_location = os.path.join(folder_to_create, rls_basename)
        saving_location = os.path.splitext(saving_location)[0] + ".dl"
        dl_rulefile = rls_basename.replace(".rls", ".dl")

        if data_sources:
            data_sources_and_filenames = ruleMapper.get_data_sources_and_filenames(data_sources)
            for pair in data_sources_and_filenames:
                source_name = pair[0]
                csv_fullpath = os.path.join(dir_fullname, "sources", pair[1])
                with open(csv_fullpath, "r") as csv_file:
                    csv_reader = csv.reader(csv_file)
                    for row in csv_reader:
                        args_with_quotes = [f'"{arg}"' for arg in row]  # Wrap each argument with double quotes
                        fact = source_name + "(" + ", ".join(args_with_quotes) + ")."
                        souffle_facts_list.append(fact)

        sc.write_souffle_rule_file(
            saving_location, souffle_type_declarations, souffle_facts_list, souffle_rules_list, query_list
        )

        command = f"{Settings.souffle_master_path} -D {folder_to_create} {folder_to_create}/{dl_rulefile}"
        commands.append(command)
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)

    c_memory, c_exec_time = monitor_process(commands)
    time.sleep(1)
    for folder_to_create in folders_to_create:
        c_count_ans += sc.count_answers(folder_to_create)

    write_benchmark_results(timestamp, task, "Souffle", c_exec_time, c_memory, c_count_ans)


def main():
    ruleMapper = DatalogRuleMapper()
    RuleParser, Rule, Literal = ruleMapper.start_jvm()

    parser = argparse.ArgumentParser()

    parser.add_argument("--config_file", type=str, required=True)
    args = parser.parse_args()
    solvers, tasks = get_config(args.config_file)

    for task in tasks:
        rule_file_path = task["path"]
        task_name = task["name"]

        try:
            rls_files = get_rls_file_paths(rule_file_path)
        except Exception as exc:
            logger.exception(exc)
            sys.exit(1)

        timestamp = datetime.datetime.now().strftime("%d-%m-%Y @%H:%M:%S")

        for solver in solvers:
            if solver.lower() == 'clingo':
                run_clingo(rls_files, task_name, timestamp, RuleParser, ruleMapper)
            elif solver.lower() == 'nemo':
                run_nemo(rls_files, timestamp, task_name)
            elif solver.lower() == "rulewerk":
                run_rulewerk(rls_files, RuleParser, Rule, Literal, rule_file_path, timestamp, task_name)
            elif solver.lower() == "souffle":
                run_souffle(rls_files, timestamp, task_name, RuleParser, ruleMapper)
            elif solver.lower() == "all":
                run_clingo(rls_files, task_name, timestamp, RuleParser, ruleMapper)
                run_nemo(rls_files, timestamp, task_name)
                run_rulewerk(rls_files, RuleParser, Rule, Literal, rule_file_path, timestamp, task_name)
                run_souffle(rls_files, timestamp, task_name, RuleParser, ruleMapper)
            else:
                logger.exception(f"{solver} Solver not recognized! Please check your config.json file.")
                sys.exit(1)

    ruleMapper.stop_jvm()


if __name__ == "__main__":
    main()
