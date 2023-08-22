import csv

class SouffleController:
    def write_souffle_rule_file(
        self, rulefile_save_location, souffle_type_declarations, souffle_facts_list, souffle_rules_list, query_list
    ):
        with open(rulefile_save_location, "w") as output_file:
            output_file.write("// Declarations\n")
            output_file.writelines("\n".join(souffle_type_declarations))
            output_file.write("\n\n")
            output_file.write("// Facts\n")
            output_file.writelines("\n".join(souffle_facts_list))
            output_file.write("\n\n")
            output_file.write("// Rules\n")
            output_file.writelines("\n".join(souffle_rules_list))
            output_file.write("\n\n")
            output_file.write("// Query list\n")
            output_file.writelines("\n".join(query_list))

    def csv_to_tsv(self, csv_path, tsv_path):
        with open(csv_path, 'r', newline='', encoding='utf-8-sig') as csv_file, \
                open(tsv_path, 'w', newline='', encoding='utf-8-sig') as tsv_file:
            csv_reader = csv.reader(csv_file)
            tsv_writer = csv.writer(tsv_file, delimiter='\t', lineterminator='\n')
            for row in csv_reader:
                tsv_writer.writerow(row)

        # The following is needed to remove the BOM from the tsv file.
        with open(tsv_path, 'rb') as input_file:
            file_content = input_file.read()
        file_content = file_content.decode('utf-8-sig').encode('utf-8')
        with open(tsv_path, 'wb') as output_file:
            output_file.write(file_content)



    def get_souffle_location(self):
        pass
