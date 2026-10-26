import Mathlib
namespace Tiny
def solution (xs : List Int) : List Int := xs.map abs
theorem spec_cons (a : Int) (xs : List Int) : solution (a :: xs) = |a| :: solution xs := by rfl
theorem test_empty : solution [] = [] := by decide
theorem test_values : solution [-2, 0, 3] = [2, 0, 3] := by decide
end Tiny
