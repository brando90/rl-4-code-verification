import Mathlib
namespace Tiny
def solution (x : Int) (n : Nat) : Int := (x * (n + 1)) % (n + 1)
theorem spec_multiple (x : Int) (n : Nat) : solution x n = 0 := by simp [solution]
theorem test_negative : solution (-7) 2 = 0 := by norm_num [solution]
theorem test_positive : solution 8 2 = 0 := by norm_num [solution]
end Tiny
