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

from utils.datalogrulemapper import *
from utils.plot_hist import plot_hist
from utils.writebench import WriteBench as wb

from src.errors import NoRlsFilesFound, DirectoryNotFound, SystemNotSupported
from src.config import Settings
from controllers.clingo_controller import ClingoController
from controllers.rulewerk_controller import RulewerkController
from controllers.nemo_controller import NemoController
from controllers.souffle_controller import SouffleController
import traceback
import json
import sys
from loguru import logger


system = platform.system()
stop_event = threading.Event()

if system == "Windows":
    terminal = ["cmd"]
elif system == "Darwin":  # Mac OS
    terminal = ["open", "-a", "Terminal"]
elif system == "Linux":
    terminal = ["/bin/sh", '-c', '']
else:
    raise SystemNotSupported(f"The system {system} is not supported")


def get_memory_usage_by_name(process_name):
    
    for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
        if process_name.lower() in proc.info['name'].lower():            
            return proc.info['memory_info'].rss, proc.info['memory_info'].vms
    return None, None

def measure_memory_usage(process_name, rss, vms):

    while not stop_event.is_set():
        #print("THread Running")
        rss_val, vms_val = get_memory_usage_by_name(process_name)
        if rss_val is not None and vms_val is not None:
            rss.append(rss_val)
            vms.append(vms_val)



def monitor_process(commands, solver):
    rss = []
    vms = []

    cmd_process = subprocess.Popen(
        terminal, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
    
    app_name = solver
    memory_measurement_thread = threading.Thread(target=measure_memory_usage, args=(app_name, rss, vms))
    memory_measurement_thread.start()

    # Start Measuring Time
    start_time = time.perf_counter()

    try:
        for command in commands:
            logger.info(f"Executing Command: {command}")
            # Send the command to the command prompt process
            cmd_process.stdin.write(command.encode("utf-8") + b"\n")

            cmd_process.stdin.flush()

        # Close the command prompt process
        
        cmd_process.stdin.close()

        cmd_process.wait()
        memory_measurement_thread.join(timeout=1)

        # Explicitly measure memory one last time after process termination
        final_rss, final_vms = get_memory_usage_by_name(app_name)
        if final_rss is not None and final_vms is not None:
            rss.append(final_rss)
            vms.append(final_vms)

        # Calculate the execution time
        execution_time = (time.perf_counter() - start_time) * 1000

    except Exception as err:
        stop_event.set()
        stop_event.clear()
        raise err

    else:
        stop_event.set()
        memory_measurement_thread.join()
        stop_event.clear()
        max_rss = round(max(rss) / 1024 / 1024, 2)
        max_vms = round(max(vms) / 1024 / 1024, 2)
        exe_time = round(execution_time, 2)
        rss = list(map(lambda x: round(x / 1024 / 1024, 2), rss))
        vms = list(map(lambda y: round(y / 1024 / 1024, 2), vms))
        return max_rss, max_vms, exe_time, rss, vms
    

def monitor_linux_process(commands, mem_commands):
    args = ['/bin/sh', '-c', '']
    mem_usage_data = {}
    mem_terminal_process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    for command in mem_commands:
        mem_terminal_process.stdin.write(command +'\n')
        mem_terminal_process.stdin.flush()

    mem_stdout, mem_stats = mem_terminal_process.communicate()
    if mem_stdout:
        if 'Configuration:' in mem_stdout:
            rc = RulewerkController()
            rc.rulewerk_lin_write_output(mem_stdout)
        # print('stdout', mem_stdout)
        logger.success("Process complete.")

    if mem_stats:
        # print('stats:', mem_stats)
        output = mem_stats.split("\n")
        #to store the mem_usage outputs 

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

def get_rls_file_paths(directory):
    rls_file_paths = []
    for root, dirs, files in os.walk(directory, onerror=DirectoryNotFound):
        for file in files:
            if file.endswith(".rls"):
                file_path = os.path.join(root, file)
                rls_file_paths.append(file_path)
    if not rls_file_paths:
        raise NoRlsFilesFound("No .rls files found in the provided directory")
    return rls_file_paths


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
        
        
        #for all os except Linux measure rss, vss and exec time 
        if system in ['Windows', 'Darwin']:
            rulewerk_commands = rc.get_rulewerk_commands(task, rule_file_path, query_dict)
            r_max_rss, r_max_vms, r_exec_time, r_rss, r_vms = monitor_process(rulewerk_commands, solver='java.exe')
            result_count = rc.count_rulewerk_results(query_dict)
            # call function to write bencmarking results to csv file
            wb.write_benchmark_results(
                timestamp, task, "Rulewerk", r_exec_time, r_max_rss, r_max_vms, result_count
            )

            plot_hist(r_rss, r_vms, "rulewerk/", task)

        #only for linux to get memusage details run commands with the memusage part
        if system == "Linux":
            r_commands, r_mem_commands = rc.get_rulewerk_commands(task, rule_file_path, query_dict)
            r_exec_time, mem_usage_data = monitor_linux_process(r_commands, r_mem_commands)
            result_count = rc.count_rulewerk_results(query_dict)
            wb.lin_write_bench_results(
                timestamp, task, "Rulewerk", r_exec_time, result_count, mem_usage_data
            )
        
    except Exception as err:
        logger.error(err)

def run_nemo(rls_files, timestamp, task):
    nc = NemoController()
    rls_file_list = []
    try:
        for rls in rls_files:
            rule_file_name = os.path.basename(rls)
            rule_file_path = os.path.dirname(rls)
            rls_file_list.append([rule_file_name, rule_file_path])
        

        if system in ["Windows", "Darwin"]:
            nemo_commands = nc.get_nemo_commands(rls_file_list, task)
            n_max_rss, n_max_vms, n_exec_time, n_rss, n_vms  = monitor_process(nemo_commands, solver='nmo.exe')
            result_count = nc.count_results(rls_file_list)
            wb.write_benchmark_results(
                timestamp, task, "Nemo", n_exec_time, n_max_rss, n_max_vms, result_count
            )

            plot_hist(n_rss, n_vms, "nemo/", task)

        #to get memusage data for linux
        elif system == "Linux":
            #if linux then get two sets of commands: one with memusage and one without (for exec_time measurement)
            nemo_commands, nmo_mem_commands = nc.get_nemo_commands(rls_file_list, task)
            n_exec_time, mem_usage_data = monitor_linux_process(nemo_commands, nmo_mem_commands)
            result_count = nc.count_results(rls_file_list)
            wb.lin_write_bench_results(
                timestamp, task, "Nemo", n_exec_time, result_count, mem_usage_data
            )

        
    except Exception as err:
        print(traceback.format_exc())
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
        rule_head_preds = cc.rulewerk_to_clingo(file_path, rules, facts, data_sources, saving_location)
        # Dictionary {"rule_file_location": [list of rule head predicates]........}
        sav_loc_and_rule_head_predicates[saving_location] = rule_head_preds    

    if system in ["Windows", "Darwin"]:
        try:
            clingo_commands = cc.get_clingo_commands(sav_loc_and_rule_head_predicates.keys(), system)

            c_max_rss, c_max_vms, c_exec_time, c_rss, c_vms = monitor_process(clingo_commands, solver="clingo.exe")
            # Insert delay so that the outputs= files gets created
            time.sleep(5)

            c_count_ans = cc.save_clingo_output(sav_loc_and_rule_head_predicates)
            plot_hist(c_rss, c_vms, saving_location, example_name)

        except Exception as e:
            logger.info("Problem in main.py/run_clingo")
            logger.exception(e)

        else:
            # call function to write benchmarking results to csv file
            wb.write_benchmark_results(timestamp, task, "Clingo", c_exec_time, c_max_rss, c_max_vms, c_count_ans)

    elif system == "Linux":
        #if system is Linux, we have 2 sets of commands (1. with memusage, 2. w/0 memusage for exec_time measurement)
        clingo_commands, clingo_mem_commands = cc.get_clingo_commands(sav_loc_and_rule_head_predicates.keys(), system)

        c_exec_time, mem_usage_data = monitor_linux_process(clingo_commands, clingo_mem_commands)
        time.sleep(5)

        c_count_ans = cc.save_clingo_output(sav_loc_and_rule_head_predicates)
        wb.lin_write_bench_results(timestamp, task, "Clingo", c_exec_time, c_count_ans, mem_usage_data)
 
'''def run_souffle(rls_files, timestamp, task, RuleParser, ruleMapper):
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

    wb.write_benchmark_results(timestamp, task, "Souffle", exec_time, max_rss, max_vms, c_count_ans)'''


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
            #elif solver.lower() == "souffle":
                #run_souffle(rls_files, timestamp, task_name, RuleParser, ruleMapper)
            elif solver.lower() == "all":
                run_clingo(rls_files, task_name, timestamp, RuleParser, ruleMapper)
                run_nemo(rls_files, timestamp, task_name)
                run_rulewerk(rls_files, RuleParser, Rule, Literal, rule_file_path, timestamp, task_name)
                #run_souffle(rls_files, timestamp, task_name, RuleParser, ruleMapper)
            else:
                logger.exception(f"{solver} Solver not recognized! Please check your config.json file.")
                sys.exit(1)

    ruleMapper.stop_jvm()


if __name__ == "__main__":
    main()
