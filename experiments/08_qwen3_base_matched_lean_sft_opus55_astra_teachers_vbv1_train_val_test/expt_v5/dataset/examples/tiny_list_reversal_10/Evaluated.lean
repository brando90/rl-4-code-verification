import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : List Int := xs.reverse.map (fun a => a + x)
theorem spec_length (x : Int) (xs : List Int) : (solution x xs).length = xs.length := by simp [solution]
theorem test_empty : solution 4 [] = [] := by decide
theorem test_order : solution 2 [1, -3, 4] = [6, -1, 3] := by decide
end Tiny
#print axioms Tiny.spec_length
#print axioms Tiny.test_empty
#print axioms Tiny.test_order
