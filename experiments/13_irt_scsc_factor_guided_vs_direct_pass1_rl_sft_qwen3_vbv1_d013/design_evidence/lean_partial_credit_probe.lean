-- TLDR: Probe showing Lean v4.22.0 keeps elaborating after a failed proof, so one compile yields per-theorem status (failed proof -> sorryAx).
def myAdd (a b : Nat) : Nat := a + b
example : myAdd 2 3 = 5 := by decide
theorem good (a b : Nat) : myAdd a b = myAdd b a := by simp [myAdd, Nat.add_comm]
theorem bad (a : Nat) : myAdd a 1 = a := by simp [myAdd]
theorem after : myAdd 0 0 = 0 := rfl
#print axioms good
#print axioms bad
#print axioms after
