import Mathlib
namespace Tiny
def solution (x : Int) (xs ys : List Int) : Nat := (xs ++ ys).count x
theorem spec_split (x : Int) (xs ys : List Int) :
    solution x xs ys = xs.count x + ys.count x := by simp [solution]
theorem test_both : solution 2 [2, 1] [2, 2] = 3 := by decide
theorem test_empty : solution 1 [] [2] = 0 := by decide
end Tiny
