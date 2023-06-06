import os
import jpype
import jpype.imports
from jpype.types import *

# Replace with the actual path to the lib folder
rulewerk_lib_path = 'J:/Semester 2/5. Team Project/MyCode/Main/lib'

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

        # Parse the Rulewerk rule file into an object model
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
