import Mathlib
namespace Tiny
def solution (pair : Int × Int) : Int × Int := (|pair.1|, |pair.2|)
theorem spec_nonnegative (pair : Int × Int) : 0 ≤ (solution pair).1 ∧ 0 ≤ (solution pair).2 := by
  exact ⟨abs_nonneg _, abs_nonneg _⟩
theorem test_positive : solution (2, -3) = (2, 3) := by norm_num [solution]
theorem test_negative : solution (-2, 4) = (2, 4) := by norm_num [solution]
end Tiny
