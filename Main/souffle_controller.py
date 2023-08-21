class SouffleController:
    def write_souffle_rule_file(self, rulefile_save_location, souffle_type_declarations, souffle_facts_list, souffle_rules_list):

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
    def run_souffle(self):
        pass

    def get_souffle_location(self):
        pass


