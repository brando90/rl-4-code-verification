import Mathlib
namespace Tiny
def solution (xs : List Int) : List Int := xs.map (fun a => max a 0)
theorem spec_cons (a : Int) (xs : List Int) : solution (a :: xs) = max a 0 :: solution xs := by rfl
theorem test_values : solution [-2, 0, 3] = [0, 0, 3] := by decide
theorem test_empty : solution [] = [] := by decide
end Tiny
#print axioms Tiny.spec_cons
#print axioms Tiny.test_values
#print axioms Tiny.test_empty
