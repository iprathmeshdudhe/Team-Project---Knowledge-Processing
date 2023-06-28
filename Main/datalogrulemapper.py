import os
import ast
import jpype
import jpype.imports
from jpype.types import *

# Replace with the actual path to the lib folder
rulewerk_lib_path = '/Users/v.sinichenko/PycharmProjects/TeamProject/Main/lib'

class DatalogRuleMapper:
    list_of_variable_names = ['X', 'Y', 'Z', 'K', 'L', 'M', 'N']

    def start_jvm(self):
        try:
            # Start the JVM
            jpype.startJVM(jpype.getDefaultJVMPath())
            print("JVM Started")
            print("==========================================================================================================================================================")
            print("JVM Path: ", jpype.getDefaultJVMPath())

            #Add the classPath
            jpype.addClassPath(os.path.join(rulewerk_lib_path,"*"))
            print("Added the Class Path")
    
            from org.semanticweb.rulewerk.parser import RuleParser as rp
            from org.semanticweb.rulewerk.core.model.api import Rule
            print("Libraries Imported")
            print("==========================================================================================================================================================")
        
        except Exception as e:
            print("An exception occurred: ", e)
        
        return rp, Rule


    def stop_jvm(self):
        # Shutdown the JVM when you're done
        jpype.shutdownJVM()
        print("==========================================================================================================================================================")
        print("JVM Stopped")


    def rulewerk_to_clingo(self, rule_file, parser):
        with open(rule_file, 'r') as rule_file:
            kb = parser.parse(rule_file.read())

        #Getting facts from the Rule File
        facts = kb.getFacts()
        facts_list = [str(facts[i].toString()).lower() for i in range(len(facts))]

        #Getting Rules from the Rule File
        rules = kb.getRules()
        rules_list = []

        for i in range(len(rules)):
            head = rules[i].getHead().getLiterals()[0]
            head_pred = head.getPredicate().getName()
            head_args = [str(arg.toString()).replace("?", "") for arg in head.getArguments()]
            body = rules[i].getBody()

            body_preds = []
            for atom in rules[i].getBody():
                pred_name = atom.getPredicate().getName()
                if i == len(rules) - 1:
                    pred_args = [str(arg.toString()).replace("?", "") if str(arg.toString()).startswith('?') else str(arg.toString()).lower() for arg in atom.getArguments()]
                    qpred_name = head_pred
                else:
                    pred_args = [str(arg.toString()).replace("?", "") for arg in atom.getArguments()]
                body_preds.append(str(pred_name.toString()).replace("?", "") + "(" + ", ".join(pred_args) + ")")
            body = ", ".join(body_preds)

            clingo_rule = head_pred + "(" + ", ".join(head_args) + ") :- " + body + "."

            rules_list.append(str(clingo_rule))

        return facts_list, rules_list, qpred_name

    def rulewerk_to_souffle(self, rule_file, parser):
        with open(rule_file, 'r') as rule_file:
            kb = parser.parse(rule_file.read())

        facts = kb.getFacts()
        rules = kb.getRules()

        type_declarations = []
        rules_list = []
        query = []
        facts_list = []

        # facts and type declarations
        for i, fact in enumerate(facts):
            # print(f'-----------------------fact # {i}, fact {fact}-----------------------')
            souffle_arguments = [f'"{argument}"' for argument in fact.getArguments()]
            souffle_declaration_arguments = []
            for j, argument in enumerate(fact.getArguments()):
                # type declarations
                # type = ': number' if str(argument).isdigit() else ': symbol' # it is possible also to treat numbers
                data_type = ': symbol'
                souffle_declaration_argument = self.list_of_variable_names[j] + data_type
                souffle_declaration_arguments.append(souffle_declaration_argument)

            souffle_fact = str(fact.getPredicate().getName()) + '(' + ', '.join(souffle_arguments) + ').'
            souffle_declaration = ".decl " + str(fact.getPredicate().getName()) + "(" + ", ".join(souffle_declaration_arguments) + ")"
            facts_list.append(souffle_fact)
            type_declarations.append(souffle_declaration)

        # rules and type declarations
        for i, rule in enumerate(rules):
            # print(f'-----------------------rule # {i}, rule {rule}-----------------------')
            # first, check if there is a question mark in each argument. If not, treat it as a query
            body_literals = rule.getBody().getLiterals()
            body_arguments = [str(argument) for literal in body_literals for argument in literal.getArguments()]
            is_fact = min([argument.startswith('?') for argument in body_arguments])
            if is_fact:
                # souffle facts
                souffle_rule = str(rule).replace('?', '').replace(' .', '.').replace('~', '!')
                rules_list.append(souffle_rule)

                # type declarations
                souffle_declaration_arguments = []
                for j, argument in enumerate(rule.getHead().getLiterals()[0].getArguments()):
                    data_type = ': symbol'
                    souffle_declaration_argument = self.list_of_variable_names[j] + data_type
                    souffle_declaration_arguments.append(souffle_declaration_argument)

                souffle_declaration = '.decl ' + str(rule.getHead().getLiterals()[0].getPredicate().getName()) + '(' + \
                    ', '.join(souffle_declaration_arguments) + ')'
                type_declarations.append(souffle_declaration)

            else:
                # treat this "KB fact" as a query
                # type declaration
                query_head_name = str(rule.getHead().getLiterals()[0].getPredicate().getName())
                print(f'rls query is {rule}')
                souffle_declaration_arguments = []
                for j, argument in enumerate(rule.getHead().getLiterals()[0].getArguments()):
                    data_type = ': symbol'
                    souffle_declaration_argument = self.list_of_variable_names[j] + data_type
                    souffle_declaration_arguments.append(souffle_declaration_argument)

                souffle_declaration = '.decl ' + query_head_name + '(' + \
                                      ', '.join(souffle_declaration_arguments) + ')'
                type_declarations.append(souffle_declaration)
                output_statement = '.output ' + query_head_name
                query.append(output_statement)
                query_statement = str(rule.getHead().getLiterals()[0]).replace('?', '') + ' :- '
                for k, literal in enumerate(body_literals):
                    if k > 0:
                        query_statement = query_statement + ', '

                    query_statement = query_statement + str(literal.getPredicate().getName())+'('
                    for m, argument in enumerate(literal.getArguments()):
                        if m > 0:
                            query_statement = query_statement + ', '
                        str_argument = str(argument)
                        if str_argument.startswith('?'):
                            query_statement = query_statement + str_argument.replace('?', '')
                        else:
                            query_statement = query_statement + '"' + str_argument + '"'
                    query_statement = query_statement + ')'

                    print(literal)

                query_statement = query_statement + '.'
                query.append(query_statement)

        type_declarations = list(set(type_declarations))
        return type_declarations, facts_list, rules_list, query


