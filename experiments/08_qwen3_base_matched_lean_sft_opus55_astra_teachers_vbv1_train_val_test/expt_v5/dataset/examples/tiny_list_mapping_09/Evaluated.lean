import Mathlib
namespace Tiny
def solution (xs : List Int) : List Int := xs.map (fun a => a * a)
theorem spec_cons (a : Int) (xs : List Int) : solution (a :: xs) = (a * a) :: solution xs := by rfl
theorem test_empty : solution [] = [] := by decide
theorem test_values : solution [-2, 0, 3] = [4, 0, 9] := by decide
end Tiny
#print axioms Tiny.spec_cons
#print axioms Tiny.test_empty
#print axioms Tiny.test_values
