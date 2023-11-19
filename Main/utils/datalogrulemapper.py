import os
import ast
import jpype
import jpype.imports
from jpype.types import *
from loguru import logger

from pathlib import Path
from tqdm import tqdm

from utils.csvtofacts import *
from src.errors import CouldNotStartJVM
from src.config import Settings

print(Settings.java_home_path)
os.environ["JAVA_HOME"] = Settings.java_home_path


class DatalogRuleMapper:
    def start_jvm(self):
        try:
            jpype.startJVM(jpype.getDefaultJVMPath())
            jpype.addClassPath(os.path.join("../lib", "*"))

            from org.semanticweb.rulewerk.parser import RuleParser
            from org.semanticweb.rulewerk.core.model.api import Rule, Literal
            from org.semanticweb.rulewerk.core.reasoner import Reasoner

            logger.success("JVM started")
            return RuleParser, Rule, Literal

        except Exception as e:
            raise CouldNotStartJVM(e)

    def stop_jvm(self):
        # Shutdown the JVM when you're done
        jpype.shutdownJVM()
        logger.success("JVM stopped")

    def rulewerktoobject(self, rule_file_name, parser):
        # Parse the Rulewerk rule file into an object model
        with open(rule_file_name, "r") as rule_file:
            kb = parser.parse(rule_file.read())

        # Getting Datasources, Facts and Rules from the Rule File
        facts = kb.getFacts()
        rules = kb.getRules()
        data_sources = kb.getDataSourceDeclarations()

        file_name = os.path.basename(rule_file_name)
        file_name_without_extension = os.path.splitext(file_name)[0]

        return rules, facts, data_sources, file_name_without_extension

    def process_clingo_facts(self, facts):
        facts_list = []
        facts_list = [str(facts[i].toString()).replace('"', "").lower() for i in range(len(facts))]

        return facts_list

    '''def get_data_sources_and_filenames(self, data_sources_objects):
        pairs = []
        for data_source_object in data_sources_objects:
            pair = []
            source_name = str(data_source_object.getPredicate().getName())
            pair.append(source_name)
            full_path = data_source_object.getDataSource().getDeclarationFact().getArguments()[0].getName()
            csv_filename = os.path.basename(str(full_path).strip('"'))
            pair.append(csv_filename)
            pairs.append(pair)
        return pairs'''

    def processDataSources(self, rule_file_path, data_Sources):
        dataSource_dict = {}

        # Storing the DataSources in the following format
        # {Table1_Name: [Num_of_variables used in it, Path of the csv zipped file], ......}
        for datasource in data_Sources:
            predicate = datasource.getPredicate()
            data_source = Path(
                str(datasource.getDataSource().getDeclarationFact().getArguments()[0].getName()).strip('"')
            )
            cwd = str(os.getcwd())
            base_dir = Path(cwd)
            rel_path = data_source.relative_to(base_dir)
            source = Path(str(os.path.join(os.getcwd(), rule_file_path, rel_path)))

            if predicate.getName() not in dataSource_dict.keys():
                dataSource_dict[predicate.getName()] = [predicate.getArity(), str(source)]
            else:
                dataSource_dict[predicate.getName()].append(str(source))

        return dataSource_dict

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

                head_args = [
                    str(arg.toString()).replace("!", "").lower()
                    if str(arg.toString()).startswith("!")
                    else str(arg.toString()).replace("?", "").capitalize()
                    for arg in head_atom.getArguments()
                ]
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
                    else str(arg.toString()).replace('"', "").lower()
                    for arg in atom.getArguments()
                ]
                body_preds.append(pred_name + "(" + ", ".join(pred_args) + ")")
            body = ", ".join(body_preds)

            clingo_rule = head + " :- " + body + "."

            rules_list.append(str(clingo_rule))

        return rules_list, head_atom_pred

    def write_clingo_rules(self, rule_list, location_to_save):
        with open(f"{location_to_save}.lp", "w") as clingo_rule:
            clingo_rule.writelines("\n".join(rule_list))

    def write_clingo_facts(self, facts_list, location_to_save):
        unique_facts = sorted(list(set(facts_list)))

        with open(location_to_save + "-facts.lp", "w") as file:
            for fact in tqdm(unique_facts, desc="Writing Facts to file: ", colour="blue"):
                file.write(fact + "\n")

        # print(f"Facts File saved at location: {location_to_save}-facts.lp")

    def rulewerk_to_clingo(self, rule_file_dir, rules, facts, data_sources, saving_location):
        rules_list, head_predicates = self.process_clingo_rules(rules)
        facts_list = self.process_clingo_facts(facts)
        data_sources_dict = self.processDataSources(rule_file_dir, data_sources)
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

    def rulewerk_to_souffle(self, rules, facts):
        """Transform Rulewerk Rules and Facts objects into Souffle type declarations, facts and rules"""
        alphabet_letters = [chr(ord("A") + i) for i in range(26)]
        type_declarations = []
        rules_list = []
        facts_list = []
        query_list = []

        # facts and type declarations
        for i, fact in enumerate(facts):
            souffle_arguments = [f"{argument}" for argument in fact.getArguments()]
            souffle_declaration_arguments = []
            for j, argument in enumerate(fact.getArguments()):
                data_type = ": symbol"
                souffle_declaration_argument = alphabet_letters[j] + data_type
                souffle_declaration_arguments.append(souffle_declaration_argument)

            souffle_fact = str(fact.getPredicate().getName()) + "(" + ", ".join(souffle_arguments) + ")."
            souffle_declaration = (
                ".decl " + str(fact.getPredicate().getName()) + "(" + ", ".join(souffle_declaration_arguments) + ")"
            )
            facts_list.append(souffle_fact)
            type_declarations.append(souffle_declaration)

        # rules and type declarations
        for i, rule in enumerate(rules):
            body_literals = rule.getBody().getLiterals()
            souffle_rule = str(rule).replace("?", "").replace(" .", ".").replace("~", "!")
            rules_list.append(souffle_rule)

            query_list.append(".output " + str(rule.getHead().getLiterals()[0].getPredicate().getName()))

            # type declarations for head
            souffle_declaration_arguments = []
            for j, argument in enumerate(rule.getHead().getLiterals()[0].getArguments()):
                data_type = ": symbol"
                souffle_declaration_argument = alphabet_letters[j] + data_type
                souffle_declaration_arguments.append(souffle_declaration_argument)

            souffle_declaration = (
                ".decl "
                + str(rule.getHead().getLiterals()[0].getPredicate().getName())
                + "("
                + ", ".join(souffle_declaration_arguments)
                + ")"
            )
            type_declarations.append(souffle_declaration)

            # type declarations for body
            for j, body_literal in enumerate(body_literals):
                souffle_declaration_arguments = []
                for k, argument in enumerate(body_literal.getArguments()):
                    data_type = ": symbol"
                    souffle_declaration_argument = alphabet_letters[k] + data_type
                    souffle_declaration_arguments.append(souffle_declaration_argument)
                souffle_declaration = (
                    ".decl "
                    + str(body_literal.getPredicate().getName())
                    + "("
                    + ", ".join(souffle_declaration_arguments)
                    + ")"
                )
                type_declarations.append(souffle_declaration)

        type_declarations = sorted(list(set(type_declarations)))
        query_list = sorted(list(set(query_list)))
        return type_declarations, facts_list, rules_list, query_list
