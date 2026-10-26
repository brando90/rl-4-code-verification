import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Nat := (x :: xs).length
theorem spec_cons (x : Int) (xs : List Int) : solution x xs = xs.length + 1 := by rfl
theorem test_empty : solution 9 [] = 1 := by decide
theorem test_many : solution (-1) [2, 3] = 3 := by decide
end Tiny
#print axioms Tiny.spec_cons
#print axioms Tiny.test_empty
#print axioms Tiny.test_many
