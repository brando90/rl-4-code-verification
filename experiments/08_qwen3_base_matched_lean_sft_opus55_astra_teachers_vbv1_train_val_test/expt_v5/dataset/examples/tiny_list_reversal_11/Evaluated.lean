import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : List Int := xs.reverse.filter (fun a => a != x)
theorem spec_excludes (x : Int) (xs : List Int) : x ∉ solution x xs := by simp [solution]
theorem test_empty : solution 4 [] = [] := by decide
theorem test_filter : solution 2 [1, 2, 3, 2] = [3, 1] := by decide
end Tiny
#print axioms Tiny.spec_excludes
#print axioms Tiny.test_empty
#print axioms Tiny.test_filter
