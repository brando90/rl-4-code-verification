import Mathlib
namespace Tiny
def solution (x : Int) (p : Bool) : Option Int := if p then none else some x
theorem spec_true (x : Int) : solution x true = none := by rfl
theorem spec_false (x : Int) : solution x false = some x := by rfl
theorem test_true : solution 3 true = none := by decide
theorem test_false : solution (-3) false = some (-3) := by decide
end Tiny
