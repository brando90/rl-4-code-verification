import Mathlib
namespace Tiny
def solution (n : Nat) (xs ys : List Int) : List Int := (xs ++ ys).take n
theorem spec_zero (xs ys : List Int) : solution 0 xs ys = [] := by rfl
theorem test_crosses_boundary : solution 3 [1, 2] [3, 4] = [1, 2, 3] := by decide
theorem test_long : solution 5 [1] [2] = [1, 2] := by decide
end Tiny
#print axioms Tiny.spec_zero
#print axioms Tiny.test_crosses_boundary
#print axioms Tiny.test_long
