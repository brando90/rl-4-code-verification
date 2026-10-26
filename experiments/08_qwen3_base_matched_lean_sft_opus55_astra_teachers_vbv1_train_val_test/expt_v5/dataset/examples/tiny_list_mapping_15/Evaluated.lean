import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : List Int := xs.map (fun a => min a x)
theorem spec_cons (x a : Int) (xs : List Int) : solution x (a :: xs) = min a x :: solution x xs := by rfl
theorem test_values : solution 2 [-3, 2, 4] = [-3, 2, 2] := by decide
theorem test_negative : solution (-1) [-3, 2] = [-3, -1] := by decide
end Tiny
#print axioms Tiny.spec_cons
#print axioms Tiny.test_values
#print axioms Tiny.test_negative
