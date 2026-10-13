import Mathlib
example : 1 + 1 = 2 := by decide
/- outer /- nested -/ comment -/
namespace Outer
@[simp] theorem first
 : 1 + 1 = 2 := by decide
namespace Inner
theorem second : 2 + 2 = 4 := by decide
end Inner
end Outer
