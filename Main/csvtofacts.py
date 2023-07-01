import csv
import tqdm
import gzip

class CSVtoFacts:

    def toFactsfile(self, source_dict, save_location):
        csv_files =[]
        facts = []
        print(source_dict)

        for key, value in source_dict.items():
            num_variables = int(value[0])
            variables = {f"Var_{x}" : None for x in range(num_variables)}
               
            with gzip.open(value[1].strip('"'), 'rt') as gz_file:
                print(gz_file)
                gz_data = gz_file.read()
                csv_data = gz_data.splitlines()
                csv_reader = csv.reader(csv_data)
                for row in csv_reader:
                    row = [x.lower() for x in row]
                    for key1, value1 in zip(variables, row):
                        variables[key1] = value1
                    p_fact = key + "(" + ", ".join(variables[k] for k in variables) +")."
                    facts.append(str(p_fact))

        with open(save_location + "-facts.lp", 'w') as file:
            for fact in tqdm.tqdm(facts, desc='Writing Facts to file: ', colour='blue'):
                file.write(fact + '\n')

        print(f'Facts File saved at location: {save_location}-facts.lp')