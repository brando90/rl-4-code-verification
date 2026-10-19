import Mathlib
namespace Tiny
def solution (x : Int) : List Int := [x, x]
theorem spec_membership (x z : Int) : z ∈ solution x ↔ z = x := by simp [solution]
theorem test_positive : solution 4 = [4, 4] := by decide
theorem test_negative : solution (-2) = [-2, -2] := by decide
end Tiny
