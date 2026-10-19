import Mathlib
namespace Tiny
def solution (xs : List Int) : Bool := xs.any fun x => x % 2 != 0
theorem spec_cons (x : Int) (xs : List Int) : solution (x :: xs) = (x % 2 != 0 || solution xs) := by rfl
theorem test_empty : solution [] = false := by decide
theorem test_mixed : solution [2, -4, 3] = true := by decide
end Tiny
