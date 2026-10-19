import Mathlib
namespace Tiny
def solution (x : Int) (xs ys : List Int) : Bool := (xs ++ ys).any fun a => a == x
theorem spec_empty_right (x : Int) (xs : List Int) : solution x xs [] = xs.any (fun a => a == x) := by simp [solution]
theorem test_found : solution (-1) [2] [-1, 3] = true := by decide
theorem test_missing : solution 4 [2] [-1, 3] = false := by decide
end Tiny
