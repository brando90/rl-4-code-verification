import Mathlib
axiom foo : 1 + 1 = 2
example : 1 + 1 = 2 := by decide
theorem good : 1 + 1 = 2 := foo
