import Mathlib
namespace Tiny
def solution (xs : List Int) : Bool := xs.all fun x => x % 2 == 0
theorem spec_cons (x : Int) (xs : List Int) : solution (x :: xs) = (x % 2 == 0 && solution xs) := by rfl
theorem test_empty : solution [] = true := by decide
theorem test_mixed : solution [2, -4, 3] = false := by decide
end Tiny
#print axioms Tiny.spec_cons
#print axioms Tiny.test_empty
#print axioms Tiny.test_mixed
