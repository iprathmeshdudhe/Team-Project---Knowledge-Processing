import sys
import json
import os
import nmo_python
import pandas as pd

rls_file_list = json.loads(sys.argv[1])


def nemo_reasoning(rls_file_list):
    # initialize counter to count number of results generated
    result_count = 0
    owd = os.getcwd()
    for rls_file in rls_file_list:
        rule_file_name = rls_file[0]
        rule_file_path = rls_file[1]
        # using the python nemo bings nmo_python to load the rule file
        cd = os.path.join(os.getcwd(), rule_file_path)
        os.chdir(cd)
        try:
            rule_file = nmo_python.load_file("{}\{}".format(cd, rule_file_name))
            nemo_rule = nmo_python.NemoEngine(rule_file)
            nemo_rule.reason()
            os.chdir(owd)

            # passing the loaded rls file to the nemo engine and running the nemo reasoner

            # the write_result function accepts parmaters: predicate of the query to  be executed, outfile_manager that takes the NemoOutputManager structure with parameters file dir as string, bool overrite?, bool gzip?
            # write_result writes the query results of the specified query to the specified output dir
            # for every output predicate in the rulefile, run the query and store results in a file
            for pred in rule_file.output_predicates():
                dir_name = rule_file_name.split(".")[0]
                nemo_rule.write_result(str(pred), nmo_python.NemoOutputManager(f"nemo\\{dir_name}", True, False))
                result_csv_file = f"nemo\\{dir_name}\\{pred}.csv"
                try:
                    result_csv = pd.read_csv(f"{result_csv_file}")
                    result_count = result_count + len(result_csv) + 1
                except pd.errors.EmptyDataError:
                    result_count = result_count

        except Exception as err:
            raise err
    return result_count


print(nemo_reasoning(rls_file_list))
