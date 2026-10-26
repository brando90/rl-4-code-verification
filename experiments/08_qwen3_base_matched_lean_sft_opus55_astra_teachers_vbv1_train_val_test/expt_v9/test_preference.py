"""Check proof-preference boundaries and that saved tiny alternatives cannot alter implementations or statements."""
import unittest

from prefer_explicit import assemble,automations,tiny_parts


class ProofPreferenceTests(unittest.TestCase):
    def test_exact_term_is_distinct_from_proof_search(self):
        self.assertEqual(automations('exact h'),[])
        self.assertEqual(automations('exact?'),['exact?'])

    def test_inventory_additions_are_detected(self):
        for tactic in ('apply_rules','solve_by_elim','simp_rw','ring1','abel','linarith','omega','norm_num'):
            with self.subTest(tactic=tactic):self.assertIn(tactic,automations(tactic+' [h]'))

    def test_explicit_combination_and_basic_steps_remain_allowed(self):
        self.assertEqual(automations('intro h\nlinear_combination h\nexact h\nrw [h]\nrfl'),[])

    def test_comments_and_identifier_substrings_do_not_count(self):
        self.assertEqual(automations('-- simp or omega\nexact simply_named_lemma /- linarith -/'),[])

    def test_saved_tiny_alternative_must_preserve_definition_and_statement(self):
        original='namespace Tiny\ndef solution (x : Nat) := x + 1\ntheorem spec (x : Nat) : solution x = x + 1 := by rfl\nend Tiny\n'
        proof_change=original.replace('by rfl','by exact rfl')
        implementation_change=original.replace(':= x + 1',':= x + 2')
        statement_change=original.replace('= x + 1 :=','= x + 2 :=')
        self.assertEqual(tiny_parts(original)[1],tiny_parts(proof_change)[1])
        self.assertNotEqual(tiny_parts(original)[1],tiny_parts(implementation_change)[1])
        self.assertNotEqual(tiny_parts(original)[1],tiny_parts(statement_change)[1])

    def test_workbook_assembly_preserves_statement(self):
        statement='theorem t (n : Nat) : n = n := by sorry'
        result=assemble(dict(formal_statement=statement),'rfl')
        self.assertIn('theorem t (n : Nat) : n = n := by\n  rfl\n',result)
        self.assertNotIn('sorry',result)


if __name__=='__main__':unittest.main()
