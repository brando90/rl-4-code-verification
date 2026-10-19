import Mathlib
namespace Tiny
def solution (xs ys zs : List Int) : List Int := xs ++ ys ++ zs
theorem spec_length (xs ys zs : List Int) : (solution xs ys zs).length = xs.length + ys.length + zs.length := by simp [solution, Nat.add_assoc]
theorem test_empty : solution [] [1] [] = [1] := by decide
theorem test_order : solution [2] [-1, 3] [4] = [2, -1, 3, 4] := by decide
end Tiny
#print axioms Tiny.spec_length
#print axioms Tiny.test_empty
#print axioms Tiny.test_order
