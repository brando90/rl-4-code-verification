import Mathlib
namespace Tiny
def solution (n : Nat) (xs : List Int) : Nat := (xs.take n).length
theorem spec_take (n : Nat) (xs : List Int) : solution n xs = min n xs.length := by simp [solution]
theorem test_short : solution 2 [1, 2, 3] = 2 := by decide
theorem test_long : solution 8 [1, 2] = 2 := by decide
end Tiny
#print axioms Tiny.spec_take
#print axioms Tiny.test_short
#print axioms Tiny.test_long
