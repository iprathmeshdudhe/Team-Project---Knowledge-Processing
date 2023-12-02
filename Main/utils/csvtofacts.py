import csv
import gzip
from urllib.parse import quote


class CSVtoFacts:
    def toFactsfile(self, source_dict):
        facts = []
        # print(source_dict)

        for key, value in source_dict.items():
            num_variables = int(value[0])
            variables = {f"Var_{x}": None for x in range(num_variables)}

            for i in range(len(value) - 1):
                if value[i + 1].strip('"').endswith("csv"):
                    with open(value[i + 1].strip('"'), "r", encoding='utf-8', errors='ignore') as csv_file:
                        reader = csv.reader(csv_file)
                        facts.extend(data_reader(reader, variables, key))

                elif value[i + 1].strip('"').endswith("gz"):
                    with gzip.open(value[i + 1].strip('"'), "rt") as gz_file:
                        # print(gz_file)
                        gz_data = gz_file.read()
                        csv_data = gz_data.splitlines()
                        csv_reader = csv.reader(csv_data)
                        facts.extend(data_reader(csv_reader, variables, key))

        return facts


def data_reader(csv_reader, var, key):
    facts_list = []

    for row in csv_reader:        
        updated_row = []

        for x in row:
            
            if x.replace(".", "").isdigit():
                updated_row.append(str(int(float(x))))
            else:
                x = quote(x.replace('"', ""))
                x = '"' + x + '"'
                updated_row.append(x.lower())
    
        for key1, value1 in zip(var, updated_row):
            var[key1] = value1
        p_fact = key + "(" + ", ".join(var[k] for k in var) + ") ."
        facts_list.append(str(p_fact))

    return facts_list
