import Mathlib
namespace Tiny
def solution (x y z : Int) (p q : Bool) : Int := if p then x else if q then y else z
theorem spec_first (x y z : Int) (q : Bool) : solution x y z true q = x := by rfl
theorem test_first : solution 1 2 3 true false = 1 := by decide
theorem test_last : solution 1 2 3 false false = 3 := by decide
end Tiny
#print axioms Tiny.spec_first
#print axioms Tiny.test_first
#print axioms Tiny.test_last
