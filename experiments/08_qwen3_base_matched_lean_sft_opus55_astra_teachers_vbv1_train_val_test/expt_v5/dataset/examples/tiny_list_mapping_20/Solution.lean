import Mathlib
namespace Tiny
def solution (xs : List Int) : List Int := xs.reverse.map (fun a => a + 1)
theorem spec_length (xs : List Int) : (solution xs).length = xs.length := by simp [solution]
theorem test_empty : solution [] = [] := by decide
theorem test_values : solution [-2, 0, 3] = [4, 1, -1] := by decide
end Tiny
