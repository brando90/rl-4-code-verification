import Mathlib
namespace Tiny
def solution (x : Int) (opt : Option Int) : Option Int := opt.map (fun value => if value <= x then value else x)
theorem spec_small (x value : Int) (h : value <= x) : solution x (some value) = some value := by simp [solution, h]
theorem test_none : solution 3 none = none := by decide
theorem test_larger : solution 3 (some 5) = some 3 := by decide
end Tiny
