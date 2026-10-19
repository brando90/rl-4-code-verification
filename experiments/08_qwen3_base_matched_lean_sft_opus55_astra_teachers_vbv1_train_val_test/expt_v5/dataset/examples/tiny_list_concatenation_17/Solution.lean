import Mathlib
namespace Tiny
def solution (x : Int) (xs ys : List Int) : Bool := (xs ++ ys).contains x
theorem spec_contains (x : Int) (xs ys : List Int) : solution x xs ys = (xs.contains x || ys.contains x) := by simp [solution]
theorem test_found : solution (-1) [2, -1] [3] = true := by decide
theorem test_missing : solution 4 [2] [-1, 3] = false := by decide
end Tiny
