import Mathlib
namespace Tiny
def solution (xs : List Int) : Nat := xs.length
theorem spec_cons (x : Int) (xs : List Int) : solution (x :: xs) = solution xs + 1 := by rfl
theorem test_empty : solution [] = 0 := by decide
theorem test_three : solution [1, -2, 3] = 3 := by decide
end Tiny
#print axioms Tiny.spec_cons
#print axioms Tiny.test_empty
#print axioms Tiny.test_three
