import Mathlib
example : 1 + 1 = 2 := by decide
theorem good : 1 + 1 = 2 := by decide
#eval IO.println (String.ofList (List.replicate 5000 'x'))
theorem bad : False := by decide
#eval IO.println (String.ofList (List.replicate 5000 'x'))
