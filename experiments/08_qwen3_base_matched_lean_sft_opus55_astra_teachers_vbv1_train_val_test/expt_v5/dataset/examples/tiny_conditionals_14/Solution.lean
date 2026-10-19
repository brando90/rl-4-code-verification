import Mathlib
namespace Tiny
def solution (x : Int) (p : Bool) : Int := if p then -x else x
theorem spec_false (x : Int) : solution x false = x := by rfl
theorem test_negate : solution 4 true = -4 := by decide
theorem test_keep : solution (-4) false = -4 := by decide
end Tiny
