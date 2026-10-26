import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Bool := xs.count x == 0
theorem spec_cons (x a : Int) (xs : List Int) :
    solution x (a :: xs) = if a = x then false else solution x xs := by
  by_cases h : a = x <;> simp [solution, h]
theorem test_absent : solution 2 [1, 3] = true := by decide
theorem test_present : solution 2 [1, 2] = false := by decide
end Tiny
