import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Nat := (xs.toFinset \ {x}).card
theorem spec_empty (x : Int) : solution x [] = 0 := by
  simp [solution]
theorem test_remove : solution 2 [1, 2, 2, 3] = 2 := by decide
theorem test_absent : solution 4 [1, 2] = 2 := by decide
end Tiny
#print axioms Tiny.spec_empty
#print axioms Tiny.test_remove
#print axioms Tiny.test_absent
