import Mathlib
namespace Tiny
def solution (opt : Option Int) : Bool := match opt with | none => false | some _ => true
theorem spec_some (x : Int) : solution (some x) = true := by rfl
theorem test_none : solution none = false := by decide
theorem test_value : solution (some (-2)) = true := by decide
end Tiny
