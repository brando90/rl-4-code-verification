import Mathlib
namespace Tiny
def solution (xs : List Int) : List Int := xs.map (fun a => a % 2)
theorem spec_cons (a : Int) (xs : List Int) : solution (a :: xs) = (a % 2) :: solution xs := by rfl
theorem test_negative : solution [-3, -2, -1] = [1, 0, 1] := by decide
theorem test_positive : solution [0, 1, 2, 3] = [0, 1, 0, 1] := by decide
end Tiny
