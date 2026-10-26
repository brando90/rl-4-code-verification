import Mathlib
namespace Tiny
def solution (x y : Int) : List Int := [x, y, x]
theorem spec_second (x y : Int) : (solution x y).get? 1 = some y := by simp [solution]
theorem test_order : solution 2 3 = [2, 3, 2] := by decide
theorem test_negative : solution (-1) 0 = [-1, 0, -1] := by decide
end Tiny
#print axioms Tiny.spec_second
#print axioms Tiny.test_order
#print axioms Tiny.test_negative
