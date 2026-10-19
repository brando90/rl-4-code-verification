import Mathlib
namespace Tiny
def solution (x : Int) (p : Bool) : Option Int := if p then some x else none
theorem spec_true (x : Int) : solution x true = some x := by rfl
theorem spec_false (x : Int) : solution x false = none := by rfl
theorem test_true : solution 3 true = some 3 := by decide
theorem test_false : solution (-3) false = none := by decide
end Tiny
