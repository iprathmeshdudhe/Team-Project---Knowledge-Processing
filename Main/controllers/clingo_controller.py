import os
import clingo
import pandas as pd
from tqdm import tqdm
from utils.csvtofacts import *
from utils.datalogrulemapper import DatalogRuleMapper 
from loguru import logger
from urllib.parse import unquote
import warnings

warnings.filterwarnings("ignore")


class ClingoController:
    # Passing a dictionary as parameter whose keys contains the File Location and the value contains rule_head_predicates
    def get_clingo_commands(self, file_locations, system):
        commands = []

        if system in ["Windows", "Darwin"]:
            for file in file_locations:
                commands.append(f"clingo {file}-facts.lp {file}.lp > {file}-output.txt")
            return commands
                
        elif system == "Linux":
            mem_commands = []
            for file in file_locations:
                commands.append(f"clingo {file}-facts.lp {file}.lp > {file}-output.txt")
                mem_commands.append(f"memusage --data={file}.dat --png={file}.png clingo {file}-facts.lp {file}.lp > {file}-output.txt")
            return commands, mem_commands

        

    def save_clingo_output(self, loc_rule_head_predicate):
        try:
            count_ans = 0
            for output_file, rule_head_preds in loc_rule_head_predicate.items():
                models = []

                with open(f"{output_file}-output.txt", "r", encoding='utf-8', errors='ignore') as file:
                    output_list = file.readlines()
                    symbols = output_list[4].strip().split()

                for symbol in symbols:
                    model = clingo.parse_term(unquote(symbol))
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
                    output_list = []

                    for model in models:
                        if pred == model.name:
                            output_list.append([const for const in model.arguments])
                            count_ans += 1

                    output_df = pd.DataFrame(output_list)
                    output_df.to_csv(f"{output_sav_loc}/{pred}.csv", index=False, header=False)

        except Exception as ex:
            logger.info("Problem While saving clingo output.")
            logger.exception("ERROR ", ex)
            logger.info("Possible Solution: Check whether clingo is installed in the system properly.")

        else:
            return count_ans
        
    def process_clingo_facts(self, facts):
        facts_list = []
        facts_list = [str(facts[i].toString()).replace('"', "").lower() for i in range(len(facts))]

        return facts_list
    
    def process_clingo_rules(self, rules):
        rules_list = []
        head_atom_pred = []

        for i in range(len(rules)):
            head_preds = []
            for head_atom in rules[i].getHead():
                head_pred = head_atom.getPredicate().getName()

                if all(char.isupper() for char in str(head_pred.toString())):
                    head_pred = str(head_pred.toString()).lower()
                else:
                    head_pred = str(head_pred.toString())[:1].lower() + str(head_pred.toString())[1:]

                head_args = []

                for arg in head_atom.getArguments():
                    if str(arg.toString()).startswith("!"):
                        head_args.append(str(arg.toString()).replace("!", "").lower())
                    elif str(arg.toString()).startswith("?"):
                        head_args.append(str(arg.toString()).replace("?", "").capitalize())
                    else:
                        head_args.append('"'+str(arg.toString()).replace('"', "").lower()+'"')

                head_preds.append(head_pred + "(" + ", ".join(head_args) + ")")

                # It will get used while saving the output in CSV
                head_atom_pred.append(head_pred)

            head = ", ".join(head_preds)

            body_preds = []
            for atom in rules[i].getBody():
                pred_name = atom.getPredicate().getName()

                if all(char.isupper() for char in str(pred_name.toString())):
                    pred_name = str(pred_name.toString()).lower()
                else:
                    pred_name = str(pred_name.toString())[:1].lower() + str(pred_name.toString())[1:]

                pred_args = [
                    str(arg.toString()).replace("?", "").capitalize()
                    if str(arg.toString()).startswith("?")
                    else '"'+str(arg.toString()).replace('"', "").lower()+'"'
                    for arg in atom.getArguments()
                ]
                body_preds.append(pred_name + "(" + ", ".join(pred_args) + ")")
            body = ", ".join(body_preds)

            clingo_rule = head + " :- " + body + "."

            rules_list.append(str(clingo_rule))

        return rules_list, head_atom_pred

    def write_clingo_rules(self, rule_list, location_to_save):
        with open(f"{location_to_save}.lp", "w", encoding='utf-8', errors='ignore') as clingo_rule:
            clingo_rule.writelines("\n".join(rule_list))

    def write_clingo_facts(self, facts_list, location_to_save):
        unique_facts = sorted(list(set(facts_list)))

        with open(location_to_save + "-facts.lp", "w", encoding='utf-8', errors='ignore') as file:
            for fact in tqdm(unique_facts, desc="Writing Facts to file: ", colour="blue"):
                file.write(fact + "\n")

        # print(f"Facts File saved at location: {location_to_save}-facts.lp")

    def rulewerk_to_clingo(self, rule_file_dir, rules, facts, data_sources, saving_location):
        rulemapper = DatalogRuleMapper()
        rules_list, head_predicates = self.process_clingo_rules(rules)
        facts_list = self.process_clingo_facts(facts)
        data_sources_dict = rulemapper.processDataSources(rule_file_dir, data_sources)
        # print("Data Sources Dict:--", data_sources_dict)

        if len(facts_list) == 0 and len(rules_list) == 0 and len(data_sources_dict) == 0:
            print("The Rulewerk .rls provided file is Empty !!")

        elif len(facts_list) == 0 and len(rules_list) > 0 and len(data_sources_dict) > 0:
            # print("Rules and DataSources")
            csvtofacts = CSVtoFacts()
            datasources_facts = csvtofacts.toFactsfile(data_sources_dict)

            self.write_clingo_rules(rules_list, saving_location)
            self.write_clingo_facts(datasources_facts, saving_location)

        elif len(facts_list) > 0 and len(rules_list) > 0 and len(data_sources_dict) == 0:
            # print("Rules and Facts")

            self.write_clingo_rules(rules_list, saving_location)
            self.write_clingo_facts(facts_list, saving_location)

        elif len(facts_list) > 0 and len(rules_list) > 0 and len(data_sources_dict) > 0:
            # print("Rules and Facts and Datasources")

            csvtofacts = CSVtoFacts()
            datasource_facts = csvtofacts.toFactsfile(data_sources_dict)

            final_facts = facts_list + datasource_facts

            self.write_clingo_rules(rules_list, saving_location)
            self.write_clingo_facts(final_facts, saving_location)

        else:
            print("The Rulewerk .rls file contains only Rules")
            self.write_clingo_rules(rules_list)

        return head_predicates

    def get_clingo_location(self, ex_name):
        directory_path = os.path.join("clingo/", ex_name)
        os.makedirs(directory_path, exist_ok=True)

        clingo_location = f"{directory_path}/{ex_name}"

        return clingo_location
