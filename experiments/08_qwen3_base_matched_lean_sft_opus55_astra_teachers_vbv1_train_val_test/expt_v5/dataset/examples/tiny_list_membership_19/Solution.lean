import Mathlib
namespace Tiny
def solution (x y : Int) (xs : List Int) : Bool := xs.any fun a => a + y == x
theorem spec_shifted (x y : Int) (xs : List Int) : solution x y xs = true ↔ ∃ a ∈ xs, a + y = x := by simp [solution]
theorem test_found : solution 5 2 [1, 3, 4] = true := by decide
theorem test_absent : solution 6 2 [1, 3] = false := by decide
end Tiny
