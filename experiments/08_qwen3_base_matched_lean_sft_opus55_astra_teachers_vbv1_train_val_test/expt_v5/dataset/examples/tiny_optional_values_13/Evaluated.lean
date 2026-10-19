import Mathlib
namespace Tiny
def solution (opt : Option Int) : List Int := match opt with | none => [] | some x => [x]
theorem spec_some (x : Int) : solution (some x) = [x] := by rfl
theorem test_none : solution none = [] := by decide
theorem test_value : solution (some (-2)) = [-2] := by decide
end Tiny
#print axioms Tiny.spec_some
#print axioms Tiny.test_none
#print axioms Tiny.test_value
