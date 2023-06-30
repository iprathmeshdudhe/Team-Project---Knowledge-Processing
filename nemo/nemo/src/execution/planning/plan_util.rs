//! Functionality that is useful for planing a rule application but is not specific to either part.

use std::{
    collections::{HashMap, HashSet},
    ops::Range,
};

use nemo_physical::{
    management::{
        database::{ColumnOrder, TableId},
        execution_plan::{ExecutionNodeRef, ExecutionPlan},
    },
    tabular::operations::{
        triescan_append::AppendInstruction, triescan_select::SelectEqualClasses, ValueAssignment,
    },
    util::interval::{Interval, IntervalBound},
};

use crate::{
    model::{Atom, Filter, FilterOperation, Identifier, Term, Variable},
    program_analysis::{analysis::RuleAnalysis, variable_order::VariableOrder},
    table_manager::TableManager,
    types::LogicalTypeEnum,
};

/// This function replaces each variable in the atom with its position in the variable ordering
/// Example:
///     * a(x, y, z) with atom order [0, 1, 2] and variable order [y, z, x] results in [1, 2, 0]
/// This function for computing JoinBindings:
///         - Example: For a leapfrog join a(x, y, z) b(z, y) with order [x, y, z] you'd obtain [[0, 1, 2], [2, 1]]
pub(super) fn atom_binding(atom: &Atom, variable_order: &VariableOrder) -> Vec<usize> {
    atom.terms().iter().map(|t| if let Term::Variable(variable) = t {
        *variable_order.get(variable).unwrap()
    } else {
        panic!("It is assumed that this function is only called on atoms which only contain variables.");
    }).collect()
}

/// Calculate helper structures that define the filters that need to be applied.
pub(super) fn compute_filters(
    variable_order: &VariableOrder,
    filters: &[Filter],
    variable_types: &HashMap<Variable, LogicalTypeEnum>,
) -> (SelectEqualClasses, Vec<ValueAssignment>) {
    let mut filter_assignments = Vec::<ValueAssignment>::new();
    let mut filter_classes = Vec::<HashSet<&Variable>>::new();
    for filter in filters {
        if !variable_order.contains(&filter.lhs) {
            continue;
        }

        match &filter.rhs {
            Term::Variable(right_variable) => {
                if !variable_order.contains(right_variable) {
                    continue;
                }

                let left_variable = &filter.lhs;

                let left_index = filter_classes
                    .iter()
                    .position(|s| s.contains(left_variable));
                let right_index = filter_classes
                    .iter()
                    .position(|s| s.contains(right_variable));

                match left_index {
                    Some(li) => match right_index {
                        Some(ri) => match ri.cmp(&li) {
                            std::cmp::Ordering::Less => {
                                let other_set = filter_classes[li].clone();
                                filter_classes[ri].extend(other_set);

                                filter_classes.remove(li);
                            }
                            std::cmp::Ordering::Equal => todo!(),
                            std::cmp::Ordering::Greater => {
                                let other_set = filter_classes[ri].clone();
                                filter_classes[li].extend(other_set);

                                filter_classes.remove(ri);
                            }
                        },
                        None => {
                            filter_classes[li].insert(right_variable);
                        }
                    },
                    None => match right_index {
                        Some(ri) => {
                            filter_classes[ri].insert(left_variable);
                        }
                        None => {
                            let mut new_set = HashSet::new();
                            new_set.insert(left_variable);
                            new_set.insert(right_variable);

                            filter_classes.push(new_set);
                        }
                    },
                }
            }
            _ => {
                let right_value = variable_types
                    .get(&filter.lhs)
                    .expect("Each variable should have been assigned a type.")
                    .ground_term_to_data_value_t(filter.rhs.clone()).expect("Trying to convert a ground type into an invalid logical type. Should have been prevented by the type checker.");
                let interval = filter_operation_to_interval(&filter.operation, right_value);

                filter_assignments.push(ValueAssignment {
                    column_idx: *variable_order.get(&filter.lhs).expect("We skip this loop iteration if one of the filter variables is not contained in the variable order."),
                    interval,
                });
            }
        }
    }

    let filter_classes: SelectEqualClasses = filter_classes
        .iter()
        .map(|s| {
            let mut r = s
                .iter()
                .map(|v| *variable_order.get(v).expect("The above loop skips iterations if one of the filter variables is not contained in the variable order."))
                .collect::<Vec<usize>>();
            r.sort();
            r
        })
        .collect();

    (filter_classes, filter_assignments)
}

fn filter_operation_to_interval<T: Clone>(operation: &FilterOperation, value: T) -> Interval<T> {
    match operation {
        FilterOperation::Equals => Interval::single(value),
        FilterOperation::LessThan => {
            Interval::new(IntervalBound::Unbounded, IntervalBound::Exclusive(value))
        }
        FilterOperation::GreaterThan => {
            Interval::new(IntervalBound::Exclusive(value), IntervalBound::Unbounded)
        }
        FilterOperation::LessThanEq => {
            Interval::new(IntervalBound::Unbounded, IntervalBound::Inclusive(value))
        }
        FilterOperation::GreaterThanEq => {
            Interval::new(IntervalBound::Inclusive(value), IntervalBound::Unbounded)
        }
    }
}

/// Compute the subplan that represents the union of a tables within a certain step range.
pub(super) fn subplan_union(
    plan: &mut ExecutionPlan,
    manager: &TableManager,
    predicate: Identifier,
    steps: &Range<usize>,
) -> ExecutionNodeRef {
    let base_tables: Vec<TableId> = manager.tables_in_range(predicate, steps);

    let mut union_node = plan.union_empty();
    for table_id in base_tables.into_iter() {
        let base_node = plan.fetch_existing(table_id);
        union_node.add_subnode(base_node);
    }

    union_node
}

/// Compute the subplan that represents the union of a tables within a certain step range.
pub(super) fn subplan_union_reordered(
    plan: &mut ExecutionPlan,
    manager: &TableManager,
    predicate: Identifier,
    steps: &Range<usize>,
    column_order: ColumnOrder,
) -> ExecutionNodeRef {
    let base_tables: Vec<TableId> = manager.tables_in_range(predicate, steps);

    let mut union_node = plan.union_empty();
    for table_id in base_tables.into_iter() {
        let base_node = plan.fetch_existing_reordered(table_id, column_order.clone());
        union_node.add_subnode(base_node);
    }

    union_node
}

/// Derived from head atoms which may contain duplicate (non-existential) variables or constants.
/// Represents a normal form which only contains non-duplicate universal variables and
/// the respective [`AppendInstruction`]s to obtain the intended result.
#[derive(Debug)]
pub(super) struct HeadInstruction {
    /// Reduced form of the the atom which only contains duplicate variables, constants or existential variables.
    pub reduced_atom: Atom,
    /// The [`AppendInstruction`]s to get the original atom.
    pub append_instructions: Vec<Vec<AppendInstruction>>,
    /// The arity of the original atom.
    pub _arity: usize,
}

/// Given an atom, bring compute the corresponding [`HeadInstruction`].
/// TODO: This needs to be revised once the Type System on the logical layer has been implemented.
pub(super) fn head_instruction_from_atom(atom: &Atom, analysis: &RuleAnalysis) -> HeadInstruction {
    let arity = atom.terms().len();
    let mut reduced_terms = Vec::<Term>::with_capacity(arity);
    let mut append_instructions = Vec::<Vec<AppendInstruction>>::new();

    append_instructions.push(vec![]);
    let mut current_append_vector = &mut append_instructions[0];

    let mut variable_map = HashMap::<Identifier, usize>::new();

    for (logical_type, term) in atom.terms().iter().enumerate().map(|(i, t)| {
        (
            analysis.predicate_types.get(&atom.predicate()).unwrap()[i],
            t,
        )
    }) {
        if let Term::Variable(variable) = term {
            let variable_identifier = match variable {
                Variable::Universal(id) => id,
                Variable::Existential(id) => id,
            };

            if let Some(repeat_index) = variable_map.get(variable_identifier) {
                let instruction = AppendInstruction::RepeatColumn(*repeat_index);
                current_append_vector.push(instruction);
            } else {
                let reduced_index = reduced_terms.len();
                reduced_terms.push(Term::Variable(variable.clone()));

                variable_map.insert(variable_identifier.clone(), reduced_index);

                append_instructions.push(vec![]);
                current_append_vector = append_instructions.last_mut().unwrap();
            }
        } else {
            let data_value_t = logical_type.ground_term_to_data_value_t(term.clone()).expect("Trying to convert a ground type into an invalid logical type. Should have been prevented by the type checker.");
            let instruction = AppendInstruction::Constant(data_value_t);
            current_append_vector.push(instruction);
        }
    }

    let reduced_atom = Atom::new(atom.predicate(), reduced_terms);

    HeadInstruction {
        reduced_atom,
        append_instructions,
        _arity: arity,
    }
}

pub(super) fn cut_last_layers(
    variable_order: &VariableOrder,
    used_variables: &HashSet<Variable>,
) -> usize {
    if variable_order.is_empty() || used_variables.is_empty() {
        return 0;
    }

    let mut last_index = 0;
    let variable_order_list = variable_order.as_ordered_list();

    for (index, variable) in variable_order_list.iter().enumerate() {
        if used_variables.contains(variable) {
            last_index = index;
        }
    }

    variable_order.len() - last_index - 1
}