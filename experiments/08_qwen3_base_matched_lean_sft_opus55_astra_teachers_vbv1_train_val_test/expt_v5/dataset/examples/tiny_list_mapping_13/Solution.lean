import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : List Bool := xs.map (fun a => decide (a = x))
theorem spec_cons (x a : Int) (xs : List Int) : solution x (a :: xs) = decide (a = x) :: solution x xs := by rfl
theorem test_matches : solution 2 [2, -2, 2] = [true, false, true] := by decide
theorem test_empty : solution 2 [] = [] := by decide
end Tiny
