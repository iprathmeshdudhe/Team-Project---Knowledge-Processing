import sys
import json
import os
import nmo_python

owd = sys.argv[1]
rls_file_list = json.loads(sys.argv[2])

print(owd)
print(rls_file_list)

def nemo_reasoning(owd, rls_file_list):
    for rls_file in rls_file_list:
        rule_file_name = rls_file[0]
        rule_file_path = rls_file[1]
        os.chdir(os.path.join(owd, rule_file_path))
        currPath = os.getcwd()        
    
        # using the python nemo bings nmo_python to load the rule file
        rls_file = nmo_python.load_file("{}\{}".format(currPath, rule_file_name))

        # passing the loaded rls file to the nemo engine and running the nemo reasoner
        nemo_rule = nmo_python.NemoEngine(rls_file)
        print("Running the reasoner...")
        nemo_rule.reason()

        # the write_result function accepts parmaters: predicate of the query to  be executed, outfile_manager that takes the NemoOutputManager structure with parameters file dir as string, bool overrite?, bool gzip? 
        # write_result writes the query results of the specified query to the specified output dir
        # for every output predicate in the rulefile, run the query and store results in a file
        for pred in rls_file.output_predicates():
            print(pred)
            nemo_rule.write_result(str(pred), nmo_python.NemoOutputManager(rule_file_name.split(".")[0], True, False)) 
        # mem_usage_end = memory_usage()[0]
        os.chdir(owd)

    
nemo_reasoning(owd, rls_file_list)