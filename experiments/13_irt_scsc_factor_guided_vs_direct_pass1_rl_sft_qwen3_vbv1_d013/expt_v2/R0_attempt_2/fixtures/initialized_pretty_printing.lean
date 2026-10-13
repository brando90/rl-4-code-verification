import Mathlib
example : 1 + 1 = 2 := by decide
set_option pp.mathlib.binderPredicates true
theorem binder_failure : ∀ n : Nat, n < 0 := by intro n; trivial
theorem later : 2 + 2 = 4 := by decide
