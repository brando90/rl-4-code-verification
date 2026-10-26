import Mathlib
namespace Tiny
def solution (xs : List Int) : List Int := xs.map (fun a => a + 1)
theorem spec_cons (a : Int) (xs : List Int) : solution (a :: xs) = (a + 1) :: solution xs := by rfl
theorem test_empty : solution [] = [] := by decide
theorem test_values : solution [-2, 0, 3] = [-1, 1, 4] := by decide
end Tiny
