import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : List Int := xs.map (fun a => a - x)
theorem spec_cons (x a : Int) (xs : List Int) : solution x (a :: xs) = (a - x) :: solution x xs := by rfl
theorem test_empty : solution 4 [] = [] := by decide
theorem test_values : solution (-2) [-3, 4] = [-1, 6] := by decide
end Tiny
#print axioms Tiny.spec_cons
#print axioms Tiny.test_empty
#print axioms Tiny.test_values
