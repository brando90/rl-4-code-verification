import Mathlib
namespace Tiny
def solution (opt : Option Int) : Option Int := match opt with | some x => if 0 <= x then some x else none | none => none
theorem spec_nonnegative (x : Int) (h : 0 <= x) : solution (some x) = some x := by simp [solution, h]
theorem test_none : solution none = none := by decide
theorem test_negative : solution (some (-2)) = none := by decide
end Tiny
