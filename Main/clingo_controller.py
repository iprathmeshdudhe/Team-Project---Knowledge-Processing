import os
import time
import psutil
import subprocess
import clingo
import pandas as pd


class ClingoController:
    # Passing a dictionary as parameter whose keys contains the File Location and the value contains rule_head_predicates
    def get_clingo_commands(self, loc_and_rule_head_predicates):
        commands = []

        for file in loc_and_rule_head_predicates.keys():
            commands.append(f"clingo {file}-facts.lp {file}.lp > {file}-output.txt")

        return commands
        
    def save_clingo_output(self, loc_rule_head_predicate):
        try:
            count_ans = 0
            for output_file, rule_head_preds in loc_rule_head_predicate.items():
                models = []

                with open(f"{output_file}-output.txt", "r") as file:
                    output_list = file.readlines()
                    symbols = output_list[4].strip().split()

                for symbol in symbols:
                    model = clingo.parse_term(symbol)
                    models.append(model)

                # Find the last occurrence of "/"
                index = output_file.rfind("/")
                new_path = output_file[: index + 1]
                # print(new_path)

                directory_path = os.path.join(new_path, "Output")
                os.makedirs(directory_path, exist_ok=True)

                output_sav_loc = directory_path

                # print(list(set(rule_head_preds)))
                for pred in list(set(rule_head_preds)):
                    # output_list = [[const.name for const in model.arguments] for model in models if pred == model.name]   #old Implementation
                    output_list = []

                    for model in models:
                        if pred == model.name:
                            output_list.append([const.name for const in model.arguments])
                            count_ans += 1

                    output_df = pd.DataFrame(output_list)
                    output_df.to_csv(f"{output_sav_loc}/{pred}.csv", index=False, header=False)

        except Exception as ex:
            print("Problem While saving clingo output.")
            print("ERROR ", ex)
            print("Possible Solution: Check whether clingo is installed in the system properly.")

        else:
            return count_ans

    def get_clingo_location(self, ex_name):
        directory_path = os.path.join("clingo/", ex_name)
        os.makedirs(directory_path, exist_ok=True)

        clingo_location = f"{directory_path}/{ex_name}"

        return clingo_location
