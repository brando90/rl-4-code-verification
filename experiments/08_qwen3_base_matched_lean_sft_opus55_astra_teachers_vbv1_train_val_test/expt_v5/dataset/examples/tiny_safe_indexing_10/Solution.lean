import Mathlib
namespace Tiny
def solution (n : Nat) (xs : List Int) : Option Int := xs.get? n
theorem spec_empty (n : Nat) : solution n [] = none := by rfl
theorem test_index : solution 1 [2, 3] = some 3 := by decide
theorem test_missing : solution 2 [2] = none := by decide
end Tiny
