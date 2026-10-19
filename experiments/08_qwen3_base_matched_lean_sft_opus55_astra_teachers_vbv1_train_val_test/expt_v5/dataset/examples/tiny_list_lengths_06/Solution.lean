import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Nat := (xs.map fun a => a + x).length
theorem spec_map (x : Int) (xs : List Int) : solution x xs = xs.length := by simp [solution]
theorem test_empty : solution 4 [] = 0 := by decide
theorem test_many : solution (-2) [1, 3, 5] = 3 := by decide
end Tiny
