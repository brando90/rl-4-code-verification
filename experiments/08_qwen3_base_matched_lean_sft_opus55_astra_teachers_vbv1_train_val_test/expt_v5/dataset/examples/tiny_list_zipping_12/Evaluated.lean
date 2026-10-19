import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Nat := (xs.zip ys).length
theorem spec_cons (a b : Int) (xs ys : List Int) : solution (a :: xs) (b :: ys) = solution xs ys + 1 := rfl
theorem test_shorter_left : solution [1] [2, 3] = 1 := by decide
theorem test_empty : solution [] [2] = 0 := by decide
end Tiny
#print axioms Tiny.spec_cons
#print axioms Tiny.test_shorter_left
#print axioms Tiny.test_empty
