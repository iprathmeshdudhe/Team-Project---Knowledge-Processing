import os
import ast
import jpype
import jpype.imports
from jpype.types import *
from csvtofacts import *

#JAVA_HOME setup not detected without explicitly mentioning in the code itself
os.environ["JAVA_HOME"] = "C:\Program Files\Java\jdk-20"
# Replace with the actual path to the lib folder
rulewerk_lib_path = "C:/Users/kansa/Desktop/Team Project TUD SoSe23/Team-Project---Knowledge-Processing/Main/lib"

class DatalogRuleMapper:

    def start_jvm(self):
        try:
            # Start the JVM
            jpype.startJVM(jpype.getDefaultJVMPath())
            print("JVM Started")
            print("==========================================================================================================================================================")
            print("JVM Path: ", jpype.getDefaultJVMPath())

            #Add the classPath
            jpype.addClassPath(os.path.join(rulewerk_lib_path,"*"))
            print(rulewerk_lib_path)
            print("Added the Class Path")

            from org.semanticweb.rulewerk.parser import RuleParser as rp
            from org.semanticweb.rulewerk.core.model.api import Rule, Literal
            from org.semanticweb.rulewerk.core.reasoner import Reasoner
            print("Libraries imported")
            print("==========================================================================================================================================================")
        
        except Exception as e:
            print("An exception occurred: ", e)
        
        return rp, Rule, Literal


    def stop_jvm(self):
        # Shutdown the JVM when you're done
        jpype.shutdownJVM()
        print("==========================================================================================================================================================")
        print("JVM Stopped")


    def rulewerktoobject(self, rule_file, parser):

        # Parse the Rulewerk rule file into an object model
        with open(rule_file, 'r') as rule_file:
            kb = parser.parse(rule_file.read())

        #Getting Datasources, Facts and Rules from the Rule File
        facts = kb.getFacts()
        rules = kb.getRules()
        data_sources = kb.getDataSourceDeclarations()


        file_path = str(rule_file)
        file_name = os.path.basename(file_path)
        file_name_without_extension = os.path.splitext(file_name)[0]
              
        return rules, facts, data_sources, file_name_without_extension
    
    def process_clingo_facts(self, facts):
        facts_list = []
        facts_list = [str(facts[i].toString()).replace("\"", "").lower() for i in range(len(facts))]

        return facts_list
    
    def processDataSources(self, data_Sources):

        dataSource_dict = {}
        
        #Storing the DataSources in the following format
        #{Table1_Name: [Num_of_variables used in it, Path of the csv zipped file], ......}
        for datasource in data_Sources:
            predicate = datasource.getPredicate()
            source = datasource.getDataSource().getDeclarationFact().getArguments()[0].getName()

            if predicate.getName() not in dataSource_dict.keys():
                dataSource_dict[predicate.getName()] = [predicate.getArity(), str(source.toString())]
            else:
                dataSource_dict[predicate.getName()].append(str(source.toString()))   

        return dataSource_dict

    def process_clingo_rules(self, rules):
        rules_list = []

        for i in range(len(rules)):

            head_preds = []
            for head_atom in rules[i].getHead():
                head_pred = head_atom.getPredicate().getName()
                head_args = [str(arg.toString()).replace("!", "").lower() if str(arg.toString()).startswith('!') else str(arg.toString()).replace("?", "").capitalize() for arg in head_atom.getArguments()]
                head_preds.append(str(head_pred.toString())+ "(" + ", ".join(head_args) + ")")

                #It will get used while saving the output in CSV
                head_atom_pred.append(str(head_pred.toString()))
                
            head = ", ".join(head_preds)

            body_preds = []
            for atom in rules[i].getBody():
                pred_name = atom.getPredicate().getName()
                pred_args = [str(arg.toString()).replace("?", "").capitalize() if str(arg.toString()).startswith('?') else str(arg.toString()).replace("\"", "").lower() for arg in atom.getArguments()]
                body_preds.append(str(pred_name.toString()).replace("?", "") + "(" + ", ".join(pred_args) + ")")
            body = ", ".join(body_preds)

            clingo_rule = head + " :- " + body + "."

            rules_list.append(str(clingo_rule))

        return rules_list, head_atom_pred

    def write_clingo_rules(self, rule_list, location_to_save):

        with open(f"{location_to_save}.lp", "w") as clingo_rule:
            clingo_rule.writelines('\n'.join(rule_list))

    def write_clingo_facts(self, facts_list, location_to_save):

        unique_facts = list(set(facts_list))
        
        with open(location_to_save + "-facts.lp", 'a') as file:
            for fact in tqdm.tqdm(unique_facts, desc='Writing Facts to file: ', colour='blue'):
                file.write(fact + '\n')

        print(f'Facts File saved at location: {location_to_save}-facts.lp')

    def rulewerk_to_clingo(self, rules, facts, data_sources, saving_location):

        rules_list, head_predicates  = self.process_clingo_rules(rules)
        facts_list = self.process_clingo_facts(facts)
        data_sources_dict = self.processDataSources(data_sources)
        

        if len(facts_list) == 0 and len(rules_list) == 0 and len(data_sources_dict) == 0:
            print("The Rulewerk .rls provided file is Empty !!")

        elif len(facts_list) == 0 and len(rules_list) > 0 and len(data_sources_dict) > 0:
            print("Rules and DataSources")
            csvtofacts = CSVtoFacts()
            datasources_facts = csvtofacts.toFactsfile(data_sources_dict)

            self.write_clingo_rules(rules_list, saving_location)
            self.write_clingo_facts(datasources_facts, saving_location)
        
        elif len(facts_list) > 0 and len(rules_list) > 0 and len(data_sources_dict) == 0:
            print("Rules and Facts")
            
            self.write_clingo_rules(rules_list, saving_location)
            self.write_clingo_facts(facts_list, saving_location)
        
        elif len(facts_list) > 0 and len(rules_list) > 0 and len(data_sources_dict) > 0:
            print("Rules and Facts and Datasources")

            csvtofacts = CSVtoFacts()
            datasource_facts = csvtofacts.toFactsfile(data_sources_dict)

            final_facts = facts_list + datasource_facts
            
            self.write_clingo_rules(rules_list, saving_location)
            self.write_clingo_facts(final_facts, saving_location)


        else:
            print("The Rulewerk .rls file contains only Rules")
            self.write_clingo_rules(rules_list)

        return head_predicates

    # def rulewerk_to_souffle(self, rule_file, parser):
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


