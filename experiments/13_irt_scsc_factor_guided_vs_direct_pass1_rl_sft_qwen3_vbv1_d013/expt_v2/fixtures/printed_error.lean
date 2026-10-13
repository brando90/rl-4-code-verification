import Mathlib
example : 1 + 1 = 2 := by decide
theorem good : 1 + 1 = 2 := by decide
#eval IO.println "fixture.lean:1:1: error: pretend"
