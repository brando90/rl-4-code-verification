import Mathlib
namespace Tiny
def solution (opt : Option Int) : Bool := match opt with | none => false | some x => decide (x > 0)
theorem spec_positive (x : Int) (h : x > 0) : solution (some x) = true := by simp [solution, h]
theorem test_none : solution none = false := by decide
theorem test_positive_value : solution (some 2) = true := by decide
end Tiny
