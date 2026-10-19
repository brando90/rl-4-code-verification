import Mathlib
namespace Tiny
def solution (n k : Nat) : List Int := ((List.range n).filter (· < k)).map Int.ofNat
theorem spec_zero_cutoff (n : Nat) : solution n 0 = [] := by simp [solution]
theorem test_cutoff : solution 5 3 = [0, 1, 2] := by decide
theorem test_large_cutoff : solution 3 5 = [0, 1, 2] := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (6))))
