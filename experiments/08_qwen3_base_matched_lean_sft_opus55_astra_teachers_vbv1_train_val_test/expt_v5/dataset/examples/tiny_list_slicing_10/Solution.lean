import Mathlib
namespace Tiny
def solution (xs : List Int) : List Int := xs.drop xs.length
theorem spec_empty (xs : List Int) : solution xs = [] := by
  simp [solution]
theorem test_values : solution [1, -2, 1] = [] := by decide
theorem test_empty : solution [] = [] := by decide
end Tiny
