import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Nat := xs.count x
theorem spec_append (x : Int) (xs ys : List Int) :
    solution x (xs ++ ys) = solution x xs + solution x ys := by simp [solution]
theorem test_duplicates : solution 2 [2, 1, 2] = 2 := by decide
theorem test_absent : solution 4 [2, 1, 2] = 0 := by decide
end Tiny
