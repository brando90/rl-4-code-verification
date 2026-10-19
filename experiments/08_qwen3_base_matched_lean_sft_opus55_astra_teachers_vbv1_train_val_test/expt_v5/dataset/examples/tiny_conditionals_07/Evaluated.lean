import Mathlib
namespace Tiny
def solution (x y : Int) (p q : Bool) : Int := if p || q then x else y
theorem spec_left_true (x y : Int) (q : Bool) : solution x y true q = x := by
  cases q <;> rfl
theorem test_both_false : solution 4 9 false false = 9 := by decide
theorem test_right_true : solution 4 9 false true = 4 := by decide
end Tiny
#print axioms Tiny.spec_left_true
#print axioms Tiny.test_both_false
#print axioms Tiny.test_right_true
