import os
import jpype
import jpype.imports
from jpype.types import *

#JAVA_HOME setup not detected without explicitly mentioning in the code itself
os.environ["JAVA_HOME"] = "C:\Program Files\Java\jdk-20"
# Replace with the actual path to the lib folder
rulewerk_lib_path = "C:/Users/kansa/Desktop/Team Project TUD SoSe23/Team-Project---Knowledge-Processing/target/lib"

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


    def rulewerk_to_clingo(self, rulewerk_rule, parser):

        # Parse the Rulewerk rule into an object model
        kb = parser.parse(rulewerk_rule)
        print("RuleParser: ", kb)

        #Converting KnowledgeBase into Core Rule
        rule_List = kb.getRules()

        print("Rules: ", rule_List)

        # Convert the object model into a Clingo rule
        #Rule Head
        head = rule_List[0].getHead().getLiterals()[0]
        print("Head: ", head)
        head_pred = head.getPredicate().getName()
        print("Head Predicate: ", head_pred)
        head_args = [str(arg.toString()).replace("?", "") for arg in head.getArguments()]
        print("Head Args: ", head_args)

        #Rule Body
        body = rule_List[0].getBody()
        print("Body: ", body)

        body_preds = []
        for atom in rule_List[0].getBody():
            pred_name = atom.getPredicate().getName()
            pred_args = [str(arg.toString()).replace("?", "") for arg in atom.getArguments()]
            body_preds.append(str(pred_name.toString()).replace("?", "") + "(" + ", ".join(pred_args) + ")")
        body = ", ".join(body_preds)

        print("Body Predicates: ",body_preds)

        clingo_rule = head_pred + "(" + ", ".join(head_args) + ") :- " + body

        return clingo_rule