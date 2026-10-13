import Mathlib
example : 1 + 1 = 2 := by decide
lemma helper : 1 + 1 = 2 := by sorry
theorem good : 1 + 1 = 2 := helper
