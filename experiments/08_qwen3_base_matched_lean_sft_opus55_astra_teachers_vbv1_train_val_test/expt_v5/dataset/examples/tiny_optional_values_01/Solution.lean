import Mathlib
namespace Tiny
def solution (opt : Option Int) : Bool := match opt with | none => true | some _ => false
theorem spec_some (x : Int) : solution (some x) = false := by rfl
theorem test_none : solution none = true := by decide
theorem test_value : solution (some (-2)) = false := by decide
end Tiny
