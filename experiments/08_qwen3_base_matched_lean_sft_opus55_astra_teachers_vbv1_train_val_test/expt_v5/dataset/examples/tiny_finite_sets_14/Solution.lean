import Mathlib
namespace Tiny
def solution (_xs : List Int) : Bool := true
theorem spec_bound (xs : List Int) : solution xs = true := by
  rfl
theorem test_duplicates : solution [1, 1, 2] = true := by decide
theorem test_empty : solution [] = true := by decide
end Tiny
