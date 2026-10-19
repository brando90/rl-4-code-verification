import Mathlib
namespace Tiny
def solution (xs : List Int) : Nat × Int := (xs.length, xs.sum)
theorem spec_length (xs : List Int) : (solution xs).1 = xs.length := rfl
theorem test_empty : solution [] = (0, 0) := by norm_num [solution]
theorem test_values : solution [2, -3, 4] = (3, 3) := by norm_num [solution]
end Tiny
