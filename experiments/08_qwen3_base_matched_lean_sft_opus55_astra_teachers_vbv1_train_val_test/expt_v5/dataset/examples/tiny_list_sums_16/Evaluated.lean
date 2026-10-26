import Mathlib
namespace Tiny
def solution (xs ys zs : List Int) : Int := xs.sum + ys.sum + zs.sum
theorem spec_append_first (xs ys zs : List Int) : solution (xs ++ ys) [] zs = solution xs ys zs := by simp [solution, add_assoc]
theorem test_empty : solution [] [] [] = 0 := by decide
theorem test_mixed : solution [3, -5] [2] [4] = 4 := by decide
end Tiny
#print axioms Tiny.spec_append_first
#print axioms Tiny.test_empty
#print axioms Tiny.test_mixed
