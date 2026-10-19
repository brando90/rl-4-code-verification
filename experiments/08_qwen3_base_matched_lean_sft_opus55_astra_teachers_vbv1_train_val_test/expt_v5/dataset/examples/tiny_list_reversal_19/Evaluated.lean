import Mathlib
namespace Tiny
def solution (xs ys zs : List Int) : List Int := (xs ++ ys ++ zs).reverse
theorem spec_append (xs ys zs : List Int) : solution xs ys zs = zs.reverse ++ ys.reverse ++ xs.reverse := by simp [solution]
theorem test_empty : solution [] [] [1] = [1] := by decide
theorem test_order : solution [1] [2, 3] [4] = [4, 3, 2, 1] := by decide
end Tiny
#print axioms Tiny.spec_append
#print axioms Tiny.test_empty
#print axioms Tiny.test_order
