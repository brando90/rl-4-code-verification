import Mathlib
namespace Tiny
def solution (xs : List Int) : List Int := xs.take (xs.length - 1)
theorem spec_singleton (x : Int) : solution [x] = [] := by rfl
theorem test_empty : solution [] = [] := by decide
theorem test_init : solution [2, 3, 4] = [2, 3] := by decide
end Tiny
