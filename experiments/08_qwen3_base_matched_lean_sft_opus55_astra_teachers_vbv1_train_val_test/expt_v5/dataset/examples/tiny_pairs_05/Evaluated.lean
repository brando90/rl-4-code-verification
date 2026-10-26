import Mathlib
namespace Tiny
def solution (pair : Int × Int) : Int × Int := (pair.2, pair.1)
theorem spec_swap_twice (pair : Int × Int) : solution (solution pair) = pair := by
  rcases pair with ⟨x, y⟩
  rfl
theorem test_positive : solution (2, 3) = (3, 2) := by norm_num [solution]
theorem test_negative : solution (-2, 4) = (4, -2) := by norm_num [solution]
end Tiny
#print axioms Tiny.spec_swap_twice
#print axioms Tiny.test_positive
#print axioms Tiny.test_negative
