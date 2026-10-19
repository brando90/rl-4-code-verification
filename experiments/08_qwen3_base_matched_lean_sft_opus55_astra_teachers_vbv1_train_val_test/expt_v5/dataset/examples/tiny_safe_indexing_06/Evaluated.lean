import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Int := (xs ++ [x]).headD x
theorem spec_empty (x : Int) : solution x [] = x := by rfl
theorem test_head : solution 9 [2, 3] = 2 := by decide
theorem test_append_default : solution 9 [] = 9 := by decide
end Tiny
#print axioms Tiny.spec_empty
#print axioms Tiny.test_head
#print axioms Tiny.test_append_default
