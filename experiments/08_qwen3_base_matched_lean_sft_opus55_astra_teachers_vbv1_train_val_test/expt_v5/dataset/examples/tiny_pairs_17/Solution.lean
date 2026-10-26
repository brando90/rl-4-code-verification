import Mathlib
namespace Tiny
def solution (pair : Int × Int) : Bool := pair.1 <= pair.2
theorem spec_reflexive (x : Int) : solution (x, x) = true := by simp [solution]
theorem test_true : solution (-2, 4) = true := by norm_num [solution]
theorem test_false : solution (5, 3) = false := by norm_num [solution]
end Tiny
