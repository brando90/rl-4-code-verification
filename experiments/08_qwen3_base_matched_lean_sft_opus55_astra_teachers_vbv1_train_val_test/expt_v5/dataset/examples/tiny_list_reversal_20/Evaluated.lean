import Mathlib
namespace Tiny
def solution (n : Nat) (xs : List Int) : List Int := (List.replicate n xs).flatten.reverse
theorem spec_zero (xs : List Int) : solution 0 xs = [] := by simp [solution]
theorem test_empty : solution 3 [] = [] := by decide
theorem test_repeat : solution 2 [1, 2] = [2, 1, 2, 1] := by decide
end Tiny
#print axioms Tiny.spec_zero
#print axioms Tiny.test_empty
#print axioms Tiny.test_repeat
