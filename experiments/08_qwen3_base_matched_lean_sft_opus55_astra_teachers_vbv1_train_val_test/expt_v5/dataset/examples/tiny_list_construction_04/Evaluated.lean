import Mathlib
namespace Tiny
def solution (x y z : Int) : List Int := [x, y, z]
theorem spec_length (x y z : Int) : (solution x y z).length = 3 := by simp [solution]
theorem test_order : solution 1 2 3 = [1, 2, 3] := by decide
theorem test_negative : solution (-1) 0 2 = [-1, 0, 2] := by decide
end Tiny
#print axioms Tiny.spec_length
#print axioms Tiny.test_order
#print axioms Tiny.test_negative
