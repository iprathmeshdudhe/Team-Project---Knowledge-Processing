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
import re

from datalogrulemapper import *

from src.errors import NoRlsFilesFound, DirectoryNotFound, SystemNotSupported
from src.config import Settings
from clingo_controller import ClingoController
from rulewerk_controller import RulewerkController
from nemo_controller import NemoController
from souffle_controller import SouffleController
import traceback
import json
import sys
from loguru import logger


# sys.tracebacklimit = 0

system = platform.system()

if system == "Windows":
    terminal = ["cmd"]
elif system == "Darwin":  # Mac OS
    terminal = ["open", "-a", "Terminal"]
elif system == "Linux":
    terminal = ["/bin/sh", '-c', '']
else:
    raise SystemNotSupported(f"The system {system} is not supported")


def measure_memory(pid, rss, vms):
    process = psutil.Process(pid)

    try:
        while process.is_running():
            mem_info = process.memory_info()
            rss.append(mem_info.rss / 1024 / 1024)
            vms.append(mem_info.vms / 1024 / 1024)
            time.sleep(Settings.memory_measurement_interval)

    except psutil.NoSuchProcess:
        logger.info("No Such Process Exist. Or Process finished executing.")
        pass


def monitor_process(commands):
    rss = []
    vms = []

    cmd_process = subprocess.Popen(
        terminal, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, text=True
    )
    # Creating a thread to measure memory in backend
    thread = threading.Thread(target=measure_memory, args=(cmd_process.pid, rss, vms))
    thread.start()

    # Start Measuring Time
    start_time = time.perf_counter()

    try:
        for command in commands:
            logger.info(f"Executing Command: {command} + b'\n")
            # Send the command to the command prompt process
            cmd_process.stdin.write(command +'\n')
            cmd_process.stdin.flush()
        
        # Close the command prompt process
        stdout, stderr = cmd_process.communicate()
        if stdout:
            print(stdout)
        if stderr:
            print(stderr)        

        # Calculate the execution time
        execution_time = (time.perf_counter() - start_time) * 1000

    except Exception as err:
        raise err

    else:
        max_rss = round(max(rss), 2)
        max_vms = round(max(vms), 2)
        return max_rss, max_vms, round(execution_time, 2)
    

def monitor_linux_process(commands, mem_commands, task, result_directory):
    args = ['/bin/sh', '-c', '']
    terminal_process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    for command in mem_commands:
        logger.info(f"Executing Command: {command} \n")
        #Send the command to the command prompt process
        terminal_process.stdin.write(command +'\n')
        terminal_process.stdin.flush()
        # time.sleep(5)

    stdout, stderr = terminal_process.communicate()
    if stdout:
        logger.success("Process complete.")

    if stderr:
        output = stderr.split("\n")
        mem_usage_data = {} #to store the mem_usage outputs 

        # output_file_path = f"{result_directory}/{task}.txt"
        # with open(output_file_path, 'w') as f:

            for line in output:
                formatted_line = re.sub(r'\x1b\[[0-9;]*m', '', line)
                if "Memory usage summary" in line:
                    pattern = re.compile(r"heap total: (\d+), heap peak: (\d+), stack peak: (\d+)")
                    matches = pattern.search(line)

                # Check if there are matches
                    if matches:
                        heap_total = int(matches.group(1))
                        heap_peak = int(matches.group(2))
                        stack_peak = int(matches.group(3))
                        if 'heap_total' not in mem_usage_data.keys():
                            mem_usage_data['heap_total'] = [heap_total]
                            mem_usage_data['heap_peak'] = [heap_peak]
                            mem_usage_data['stack_peak'] = [stack_peak]
                        else:
                            mem_usage_data['heap_total'].append(heap_total)
                            mem_usage_data['heap_peak'].append(heap_peak)
                            mem_usage_data['stack_peak'].append(stack_peak)
                        # f.write(f'heap_total: {heap_total}\nheap_peak: {heap_peak}\nstack_peak: {stack_peak}\n')


                if "malloc" in formatted_line.split("|")[0] or "calloc" in formatted_line.split("|")[0]:
                    measure_name = formatted_line.split("|")[0].replace(" ", "")
                    pattern = re.compile(r'\b\d+\b')
                    # Find all matches in the input string
                    measures = [int(match.group()) for match in pattern.finditer(formatted_line)]
                    total_calls, total_memory, failed_calls = measures[0], measures[1], measures[2]
                    if f"{measure_name}_total_calls" not in mem_usage_data.keys():
                        mem_usage_data[f"{measure_name}_total_calls"] = [total_calls]
                        mem_usage_data[f"{measure_name}_total_memory"] = [total_memory]
                        mem_usage_data[f"{measure_name}_failed_calls"] = [failed_calls]
                    else:
                        mem_usage_data[f"{measure_name}_total_calls"].append(total_calls)
                        mem_usage_data[f"{measure_name}_total_memory"].append(total_memory)
                        mem_usage_data[f"{measure_name}_failed_calls"].append(failed_calls)
                    # f.write(f"{measure_name}: {total_calls}, {total_memory}, {failed_calls}\n")

                if "realloc" in formatted_line.split("|")[0]:
                    measure_name = formatted_line.split("|")[0].replace(" ", "")
                    pattern = re.compile(r'\b\d+\b')
                    # Find all matches in the input string
                    measures = [int(match.group()) for match in pattern.finditer(formatted_line)]
                    total_calls, total_memory, failed_calls, nomove, dec, free = measures[0], measures[1], measures[2], measures[3], measures[4], measures[5] 
                    if f"{measure_name}_total_calls" not in mem_usage_data.keys():
                        mem_usage_data[f"{measure_name}_total_calls"] = [total_calls]
                        mem_usage_data[f"{measure_name}_total_memory"] = [total_memory]
                        mem_usage_data[f"{measure_name}_failed_calls"] = [failed_calls]
                        mem_usage_data[f"{measure_name}_nomove"] = [nomove]
                        mem_usage_data[f"{measure_name}_dec"] = [dec]
                        mem_usage_data[f"{measure_name}_free"] = [free]
                    else:
                        mem_usage_data[f"{measure_name}_total_calls"].append(total_calls)
                        mem_usage_data[f"{measure_name}_total_memory"].append(total_memory)
                        mem_usage_data[f"{measure_name}_failed_calls"].append(failed_calls)
                        mem_usage_data[f"{measure_name}_nomove"].append(nomove)
                        mem_usage_data[f"{measure_name}_dec"].append(dec)
                        mem_usage_data[f"{measure_name}_free"].append(free)
                    # f.write(f"{measure_name}: {total_calls}, {total_memory}, {failed_calls}, {nomove}, {dec}, {free}\n")

                if "free" in formatted_line.split("|")[0]:
                    measure_name = formatted_line.split("|")[0].replace(" ", "")
                    pattern = re.compile(r'\b\d+\b')
                    # Find all matches in the input string
                    measures = [int(match.group()) for match in pattern.finditer(formatted_line)]
                    total_calls, total_memory = measures[0], measures[1]
                    if f"{measure_name}_total_calls" not in mem_usage_data.keys():
                        mem_usage_data[f"{measure_name}_total_calls"] = [total_calls]
                        mem_usage_data[f"{measure_name}_total_memory"] = [total_memory]
                    else:
                        mem_usage_data[f"{measure_name}_total_calls"].append(total_calls)
                        mem_usage_data[f"{measure_name}_total_memory"].append(total_memory)
                    # f.write(f"{measure_name}: {total_calls}, {total_memory}\n")

    #measure execution time (for commands without memusage)
    terminal_process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    start_time = time.perf_counter()
    for command in commands:
        logger.info(f"Executing Command: {command} \n")
        #Send the command to the command prompt process
        terminal_process.stdin.write(command +'\n')
        terminal_process.stdin.flush()

    stdout, stderr = terminal_process.communicate()
    exec_time = (time.perf_counter() - start_time) *1000
    if stderr:
        logger.error(stderr)
    return round(exec_time, 2), mem_usage_data

    #if tool is rulewerk then use java -jar rulewerk.jar instead of /bin/sh (pending)

def lin_write_bench_results(timestamp, task, tool, exec_time, result_count, mem_usage_data):
    flag = os.path.exists("MemUsageResults.csv")
    logger.info("writing memusage results to csv file")
    mem_usage_sum = []
    for key, value in mem_usage_data.items(): #using the sum of measurement values of rls files in a task to represent the task's bench measurements in the csv file
        val_sum = sum(mem_usage_data[key])  
        print(val_sum)
        mem_usage_sum.append(val_sum)
    print(mem_usage_sum)
    with open("MemUsageResults.csv", mode="a", newline="") as csv_file:
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
                    "Execution Time",
                    "Result Count",
                    "Heap Total",
                    "Heap Peak",
                    "Stack Peak",
                    "Malloc Total Calls",
                    "Malloc Total Memory",
                    "Malloc Failed Calls",
                    "Calloc Total Calls",
                    "Calloc Total Memory",
                    "Calloc Failed Calls",
                    "Realloc Total Calls",
                    "Realloc Total Memory",
                    "Realloc Failed Calls",
                    "Realloc Nomove",
                    "Realloc Dec",
                    "Realloc Free",
                    "Free Total Calls",
                    "Free Total Memory"
                ],
            )
            dw.writeheader()
        csv_writer.writerow([timestamp, task, tool, exec_time, result_count]+mem_usage_sum)
     #take the list of rls files in a task and from the memusage txt file of these rls files extract the info and do avg or max 
     #returns set of max or avg mem info 


def get_rls_file_paths(directory):
    rls_file_paths = []
    for root, dirs, files in os.walk(directory, onerror=DirectoryNotFound):
        for file in files:
            print (file)
            if file.endswith(".rls"):
                file_path = os.path.join(root, file)
                rls_file_paths.append(file_path)
    if not rls_file_paths:
        raise NoRlsFilesFound("No .rls files found in the provided directory")
    return rls_file_paths


def write_benchmark_results(timestamp, task, tool, execution_time, max_rss, max_vms, count):
    # if not csv file exist create a new one : in which directory?
    # header: timestamp task, tool, execution_time, memory_info
    # row: parameters in order
    # close csv
    flag = os.path.exists("BenchResults.csv")
    logger.info("writing benchmark results to csv file")
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
                    "Max. Resident Set Size (MB)",
                    "Max. Virtual Memory Size (MB)",
                    "Count of grounded Rule Predicates",
                ],
            )
            dw.writeheader()
        csv_writer.writerow([timestamp, task, tool, execution_time, max_rss, max_vms, count])


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
    try:
        for rls in rls_files:
            file_name = os.path.basename(rls)
            query, head_pred = rc.get_rule_file_elements(RuleParser, Rule, Literal, rls)
            query_dict[rls] = [query, head_pred]
        rulewerk_commands = rc.get_rulewerk_commands(task, rule_file_path, query_dict)
        
        #for all os except Linux measure rss, vss and exec time 
        if system in ['Windows', 'Darwin']:
            r_max_rss, r_max_vms, r_exec_time = monitor_process(rulewerk_commands)
            result_count = rc.count_rulewerk_results(query_dict)
            # call function to write bencmarking results to csv file
            write_benchmark_results(
                timestamp, task, "Rulewerk", r_exec_time, r_max_rss, r_max_vms, result_count
            )

        #only for linux to get memusage details run commands with the memusage part
        if system == "Linux":
            pass 
            # monitor_linux_process(rulewerk_commands, task, result_directory)

        
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
        result_directory = os.path.join("clingo/", example_name) #to store memusage txt file in this direcotry
        saving_location = cc.get_clingo_location(example_name) 
        rule_head_preds = ruleMapper.rulewerk_to_clingo(file_path, rules, facts, data_sources, saving_location)
        # Dictionary {"rule_file_location": [list of rule head predicates]........}
        sav_loc_and_rule_head_predicates[saving_location] = rule_head_preds    

    if system in ["Windows", "Darwin"]:
        clingo_commands = cc.get_clingo_commands(sav_loc_and_rule_head_predicates.keys(), system)

        c_max_rss, c_max_vms, c_exec_time = monitor_process(clingo_commands)
        # Insert delay so that the outputs= files gets created
        time.sleep(5)

        c_count_ans = cc.save_clingo_output(sav_loc_and_rule_head_predicates)

        # call function to write benchmarking results to csv file
        write_benchmark_results(timestamp, task, "Clingo", c_exec_time, c_max_rss, c_max_vms, c_count_ans)

    elif system == "Linux":
        #if system is Linux, we have 2 sets of commands (1. with memusage, 2. w/0 memusage for exec_time measurement)
        clingo_commands, clingo_mem_commands = cc.get_clingo_commands(sav_loc_and_rule_head_predicates.keys(), system)

        c_exec_time, mem_usage_data = monitor_linux_process(clingo_commands, clingo_mem_commands, task, result_directory)
        time.sleep(5)

        c_count_ans = cc.save_clingo_output(sav_loc_and_rule_head_predicates)
        lin_write_bench_results(timestamp, task, "Clingo", c_exec_time, c_count_ans, mem_usage_data)

    


def run_nemo(rls_files, timestamp, task):
    nc = NemoController()
    rls_file_list = []
    try:
        for rls in rls_files:
            rule_file_name = os.path.basename(rls)
            rule_file_path = os.path.dirname(rls)
            rls_file_list.append([rule_file_name, rule_file_path])
        

        if system in ["Windows", "Darwin"]:
            nemo_commands, result_directory = nc.get_nemo_commands(rls_file_list, task)
            n_max_rss, n_max_vms, n_exec_time = monitor_process(nemo_commands)
            result_count = nc.count_results(rls_file_list)
            write_benchmark_results(
                timestamp, task, "Nemo", n_exec_time, n_max_rss, n_max_vms, result_count
            )

        #to get memusage data for linux
        elif system == "Linux":
            print(rls_file_list)
            #if linux then get two sets of commands: one with memusage and one without (for exec_time measurement)
            nemo_commands, nmo_mem_commands, result_directory = nc.get_nemo_commands(rls_file_list, task)
            n_exec_time, mem_usage_data = monitor_linux_process(nemo_commands, nmo_mem_commands, task, result_directory)
            result_count = nc.count_results(rls_file_list)
            lin_write_bench_results(
                timestamp, task, "Nemo", n_exec_time, result_count, mem_usage_data
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

    max_rss, max_vms, exec_time = monitor_process(commands)

    for folder_to_create in folders_to_create:
        c_count_ans += sc.count_answers(folder_to_create)

    write_benchmark_results(timestamp, task, "Souffle", exec_time, max_rss, max_vms, c_count_ans)


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
            logger.error(exc)
            sys.exit(1)

        timestamp = datetime.datetime.now().strftime("%d-%m-%Y @%H:%M:%S")

        for solver in solvers:
            if solver.lower() == "clingo":
                run_clingo(rls_files, task_name, timestamp, RuleParser, ruleMapper)
            elif solver.lower() == "nemo":
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
