import Mathlib
namespace Tiny
def solution (pair : Int × Int) : Int × Int := (-pair.1, -pair.2)
theorem spec_involution (pair : Int × Int) : solution (solution pair) = pair := by
  rcases pair with ⟨x, y⟩
  simp [solution]
theorem test_positive : solution (2, 3) = (-2, -3) := by norm_num [solution]
theorem test_negative : solution (-2, 4) = (2, -4) := by norm_num [solution]
end Tiny
