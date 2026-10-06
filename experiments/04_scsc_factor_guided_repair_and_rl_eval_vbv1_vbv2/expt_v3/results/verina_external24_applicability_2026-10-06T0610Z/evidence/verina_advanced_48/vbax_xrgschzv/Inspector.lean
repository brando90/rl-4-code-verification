import Lean
import _stdin

run_cmd do
  let env ← Lean.getEnv
  let target := Lean.Name.fromJson? (Lean.Json.str "_stdin")
  let .ok target := target | throwError "invalid target module"
  let some idx := env.getModuleIdx? target | throwError "target module missing"
  let mut out : Array String := #[]
  for ci in env.header.moduleData[idx]!.constants do
    let n := ci.name
    let kind := match ci with
      | .thmInfo _ => "theorem"
      | .axiomInfo _ => "axiom"
      | _ => "other"
    if kind != "other" then
      let axs ← Lean.collectAxioms n
      let r ← Lean.findDeclarationRangesCore? n
      let row := Lean.Json.mkObj [
        ("name", Lean.toJson n.toString),
        ("kind", Lean.toJson kind),
        ("axioms", Lean.toJson (axs.map (·.toString))),
        ("line", Lean.toJson (r.map (·.selectionRange.pos.line))),
        ("column", Lean.toJson (r.map (·.selectionRange.pos.column))),
        ("range_line", Lean.toJson (r.map (·.range.pos.line))),
        ("range_column", Lean.toJson (r.map (·.range.pos.column)))]
      out := out.push row.compress
  IO.println "VBAX_296e3bdfdee442e0b8b735db6bb2069c:BEGIN"
  for row in out.qsort (· < ·) do
    IO.println ("VBAX_296e3bdfdee442e0b8b735db6bb2069c:ROW " ++ row)
  IO.println ("VBAX_296e3bdfdee442e0b8b735db6bb2069c:END " ++ toString out.size)
