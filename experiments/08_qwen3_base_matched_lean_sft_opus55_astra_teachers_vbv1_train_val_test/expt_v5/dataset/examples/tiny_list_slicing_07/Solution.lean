import Mathlib
namespace Tiny
def solution (xs : List Int) : List Int := []
theorem spec_empty (xs : List Int) : solution xs = [] := by rfl
theorem test_nonempty : solution [1, 2] = [] := by decide
theorem test_empty : solution [] = [] := by decide
end Tiny
