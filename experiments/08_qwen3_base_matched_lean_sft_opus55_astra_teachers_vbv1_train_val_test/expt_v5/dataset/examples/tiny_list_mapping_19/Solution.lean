import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) (p : Bool) : List Int :=
  xs.map (fun a => if p then a + x else a - x)
theorem spec_true (x : Int) (xs : List Int) : solution x xs true = xs.map (fun a => a + x) := by rfl
theorem test_true : solution 2 [-3, 4] true = [-1, 6] := by decide
theorem test_false : solution 2 [-3, 4] false = [-5, 2] := by decide
end Tiny
