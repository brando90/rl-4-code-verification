import Mathlib
namespace Tiny
def solution (xs ys : List Int) : List Int := xs ++ ys ++ xs
theorem spec_length (xs ys : List Int) : (solution xs ys).length = xs.length + ys.length + xs.length := by simp [solution, Nat.add_assoc]
theorem test_empty : solution [] [1] = [1] := by decide
theorem test_repeat : solution [2, -1] [3] = [2, -1, 3, 2, -1] := by decide
end Tiny
#print axioms Tiny.spec_length
#print axioms Tiny.test_empty
#print axioms Tiny.test_repeat
