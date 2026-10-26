import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Int := xs.reverse.getD 1 x
theorem spec_pair (x a b : Int) : solution x [a, b] = a := by rfl
theorem test_penultimate : solution 9 [2, 3, 4] = 3 := by decide
theorem test_default : solution 9 [2] = 9 := by decide
end Tiny
