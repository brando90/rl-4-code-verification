import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : List Int := xs.map (fun a => a * x)
theorem spec_cons (x a : Int) (xs : List Int) : solution x (a :: xs) = (a * x) :: solution x xs := by rfl
theorem test_zero : solution 0 [-2, 3] = [0, 0] := by decide
theorem test_negative : solution (-2) [-3, 4] = [6, -8] := by decide
end Tiny
