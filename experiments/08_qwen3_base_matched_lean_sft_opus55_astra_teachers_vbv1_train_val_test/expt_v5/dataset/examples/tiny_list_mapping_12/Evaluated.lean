import Mathlib
namespace Tiny
def solution (xs : List Int) : List Bool := xs.map (fun a => decide (a >= 0))
theorem spec_cons (a : Int) (xs : List Int) : solution (a :: xs) = decide (a >= 0) :: solution xs := by rfl
theorem test_signs : solution [-2, 0, 3] = [false, true, true] := by decide
theorem test_empty : solution [] = [] := by decide
end Tiny
#print axioms Tiny.spec_cons
#print axioms Tiny.test_signs
#print axioms Tiny.test_empty
