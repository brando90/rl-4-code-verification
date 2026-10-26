/- Extract exact parser-owned proof term ranges from unchanged training files. -/
import Mathlib
import Lean

open Lean

partial def firstValue (s : Syntax) : Option Syntax := do
  if s.isOfKind ``Lean.Parser.Command.declValSimple then
    return s[1]
  for child in s.getArgs do
    if let some term := firstValue child then return term
  none

partial def declarationKind (s : Syntax) : Option String := do
  let k := s.getKind.toString
  if k == "Lean.Parser.Command.theorem" || k == "Lean.Parser.Command.example" then
    return k
  for child in s.getArgs do
    if let some kind := declarationKind child then return kind
  none

unsafe def main (args : List String) : IO UInt32 := do
  initSearchPath (← findSysroot)
  enableInitializersExecution
  let env ← importModules (loadExts := true) #[{ module := `Mathlib }] {}
  let listFile := args.head!
  for line in (← IO.FS.readFile listFile).splitOn "\n" do
    if line.trim.isEmpty then continue
    try
      let src ← IO.FS.readFile line
      let stx ← Lean.Parser.testParseModule env line src
      let mut ranges : Array Json := #[]
      for command in stx.raw[1].getArgs do
        if let some kind := declarationKind command then
          if let some term := firstValue command then
            let some r := term.getRange? | throw <| IO.userError "proof has no source range"
            let some c := command.getRange? | throw <| IO.userError "command has no source range"
            ranges := ranges.push <| Json.mkObj [
              ("kind", toJson kind), ("start_byte", toJson r.start.byteIdx),
              ("end_byte", toJson r.stop.byteIdx),
              ("command_start_byte", toJson c.start.byteIdx),
              ("command_end_byte", toJson c.stop.byteIdx)]
      IO.println <| (Json.mkObj [("path", toJson line), ("ranges", toJson ranges)]).compress
    catch e =>
      IO.println <| (Json.mkObj [("path", toJson line), ("error", toJson e.toString)]).compress
  return 0
