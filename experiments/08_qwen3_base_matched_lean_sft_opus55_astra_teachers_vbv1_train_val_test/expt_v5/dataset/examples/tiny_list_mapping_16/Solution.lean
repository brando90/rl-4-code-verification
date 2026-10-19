import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : List Int := xs.map (fun a => max a x)
theorem spec_cons (x a : Int) (xs : List Int) : solution x (a :: xs) = max a x :: solution x xs := by rfl
theorem test_values : solution 2 [-3, 2, 4] = [2, 2, 4] := by decide
theorem test_negative : solution (-1) [-3, 2] = [-1, 2] := by decide
end Tiny
