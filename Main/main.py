import argparse
import os.path
import shutil
import subprocess

from datalogrulemapper import *
import datetime
from loguru import logger
import traceback

from src.errors import NoRlsFilesFound, DirectoryNotFound
from src.config import Settings
from clingo_controller import ClingoController
from rulewerk_controller import RulewerkController
from nemo_controller import NemoController
from souffle_controller import SouffleController


def get_rls_file_paths(directory):
    rls_file_paths = []
    for root, dirs, files in os.walk(directory):
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
    # print(flag)
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


def run_rulewerk(rls_files, RuleParser, Rule, Literal, rule_file_path, timestamp, task):
    rc = RulewerkController()
    query_dict = {}
    result_count = 0
    try:
        for rls in rls_files:
            file_name = os.path.basename(rls)
            query, head_pred = rc.rulefileElements(RuleParser, Rule, Literal, rls)
            query_dict[rls] = [query, head_pred]
        execution_time, memory_info, result_count = rc.runRulewerk(rule_file_path, query_dict)
        # call function to write bencmarking results to csv file
        write_benchmark_results(
            timestamp, task, "Rulewerk", round(execution_time, 2), round(memory_info, 2), round(int(result_count), 2)
        )
    except Exception as err:
        print("An exception occurred: ", err)
        traceback.print_exc()


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

    c_memory, c_exec_time, c_count_ans = cc.run_clingo(sav_loc_and_rule_head_predicates)

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
        execution_time, memory_info, result_count = nc.runNemo(rls_file_list)

        # call function to write bencmarking results to csv file
        write_benchmark_results(
            timestamp, task, "Nemo", round(execution_time, 2), round(memory_info, 2), round(int(result_count), 2)
        )
    except Exception as err:
        print("An exception occurred: ", err)


def run_souffle(rls_files, timestamp, task, RuleParser, ruleMapper):
    sc = SouffleController()

    for rls in rls_files:
        rls_basename = os.path.basename(rls)
        dir_fullname = os.path.dirname(rls)
        dir_basename = os.path.basename(dir_fullname)
        print()
        print(f" ----------- EXAMPLE ={dir_basename} -----------")
        folder_to_create = os.path.join("souffle", dir_basename)
        os.makedirs(folder_to_create, exist_ok=True)

        rules, facts, data_sources, _ = ruleMapper.rulewerktoobject(rls, RuleParser)
        souffle_type_declarations, souffle_facts_list, souffle_rules_list = ruleMapper.rulewerk_to_souffle(rules, facts)

        saving_location = os.path.join(folder_to_create, rls_basename)
        saving_location = os.path.splitext(saving_location)[0] + ".dl"
        dl_rulefile = rls_basename.replace('.rls', '.dl')

        if data_sources:
            csv_filenames = ruleMapper.get_csv_filenames(data_sources)
            for csv_filename in csv_filenames:
                csv_fullpath = os.path.join(dir_fullname, "sources", csv_filename)
                with open(csv_fullpath, "r") as csv_file:
                    csv_reader = csv.reader(csv_file)
                    for row in csv_reader:
                        souffle_facts_list.append(row)


        sc.write_souffle_rule_file(saving_location, souffle_type_declarations, souffle_facts_list, souffle_rules_list)

        command = f"{Settings.souffle_master_path}  -D {folder_to_create} {folder_to_create}/{dl_rulefile}"
        print(f"command={command}")
        # process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)


        c_count_ans=0 # TODO count
    # write_benchmark_results(timestamp, task, "Clingo", c_exec_time, c_memory, c_count_ans)






def main():
    ruleMapper = DatalogRuleMapper()
    RuleParser, Rule, Literal = ruleMapper.start_jvm()

    # Added the parser to use the code as tool
    parser = argparse.ArgumentParser()
    parser.add_argument("--solver", required=True, type=str, choices=["clingo", "nemo", "rulewerk", "souffle", "all"])
    parser.add_argument("--input_dir", type=str, required=True)
    parser.add_argument("--task_name", type=str, required=False)

    args = parser.parse_args()

    rule_file_path = args.input_dir
    if not os.path.exists(rule_file_path):
        raise DirectoryNotFound(f"The given directory {rule_file_path} does not exist")

    rls_files = get_rls_file_paths(rule_file_path)
    if not rls_files:
        raise NoRlsFilesFound("No .rls files found in the given directory")

    if not args.task_name:
        normalized_path = os.path.normpath(rule_file_path)
        args.task_name = normalized_path.split(os.sep)[-1]

    timestamp = datetime.datetime.now().strftime("%d-%m-%Y @%H:%M:%S")

    if args.solver == "clingo":
        run_clingo(rls_files, args.task_name, timestamp, RuleParser, ruleMapper)

    elif args.solver == "nemo":
        run_nemo(rls_files, timestamp, args.task_name)

    elif args.solver == "rulewerk":
        run_rulewerk(rls_files, RuleParser, Rule, Literal, rule_file_path, timestamp, args.task_name)

    elif args.solver == "souffle":
        run_souffle(rls_files, timestamp, args.task_name, RuleParser, ruleMapper)

    elif args.solver == "all":
        print("All Solvers are selected.")
        run_clingo(rls_files, args.task_name, timestamp, RuleParser, ruleMapper)
        run_nemo(rls_files, timestamp, args.task_name)
        run_rulewerk(rls_files, RuleParser, Rule, Literal, rule_file_path, timestamp, args.task_name)
        run_souffle(rls_files, timestamp, args.task_name, RuleParser, ruleMapper)

    ruleMapper.stop_jvm()


if __name__ == "__main__":
    main()
