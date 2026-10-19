import Mathlib
namespace Tiny
def solution (x y : Int) (p q : Bool) : Int := if p && q then x else y
theorem spec_both_true (x y : Int) : solution x y true true = x := by rfl
theorem test_both_true : solution 4 9 true true = 4 := by decide
theorem test_one_false : solution 4 9 true false = 9 := by decide
end Tiny
