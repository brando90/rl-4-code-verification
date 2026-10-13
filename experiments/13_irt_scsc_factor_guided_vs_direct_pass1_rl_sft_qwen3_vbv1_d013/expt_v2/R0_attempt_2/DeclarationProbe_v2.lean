/- TLDR: Elaborate unchanged Lean commands, retaining complete diagnostics and final theorem dependencies. -/
import Lean
import Lean.Util.CollectAxioms

open Lean Elab Frontend

def rangeFields (stx : Syntax) : List (String × Json) :=
  match stx.getRange? with
  | some range => [("start", toJson range.start.byteIdx), ("stop", toJson range.stop.byteIdx)]
  | none => [("start", Json.null), ("stop", Json.null)]

def namedDeclarationKind (kind : Name) : Bool :=
  kind == ``Parser.Command.abbrev || kind == ``Parser.Command.definition ||
  kind == ``Parser.Command.theorem || kind == ``Parser.Command.opaque ||
  kind == ``Parser.Command.axiom || kind == ``Parser.Command.inductive ||
  kind == ``Parser.Command.classInductive || kind == ``Parser.Command.structure

def declarationName? (inner : Syntax) : Option Name :=
  if namedDeclarationKind inner.getKind && inner.getNumArgs > 1 then
    let declId := inner[1]
    if declId.getNumArgs > 0 && declId[0].isIdent then some declId[0].getId else none
  else none

def lemmaName? (stx : Syntax) : Option Name :=
  if stx.getKind == `lemma && stx.getNumArgs > 1 then
    let group := stx[1]
    if group.getNumArgs > 1 then
      let declId := group[1]
      if declId.getNumArgs > 0 && declId[0].isIdent then some declId[0].getId else none
    else none
  else none

def fullName (ns : Name) (short : Name) : Name :=
  if (`_root_).isPrefixOf short then short.replacePrefix `_root_ Name.anonymous
  else ns.append short

def commandJson (stx : Syntax) (ns : Name) : Json :=
  let fields := [("event", toJson "command"), ("command_kind", toJson stx.getKind.toString)] ++ rangeFields stx
  if stx.isOfKind ``Parser.Command.declaration then
    let inner := stx[1]
    let short? := declarationName? inner
    Json.mkObj <| fields ++ [
      ("declaration_kind", toJson inner.getKind.toString),
      ("short_name", toJson <| short?.map Name.toString),
      ("full_name", toJson <| short?.map (fun name => (fullName ns name).toString)),
      ("is_example", toJson (inner.getKind == ``Parser.Command.example)),
      ("is_axiom", toJson (inner.getKind == ``Parser.Command.axiom))]
  else if let some short := lemmaName? stx then
    Json.mkObj <| fields ++ [
      ("declaration_kind", toJson "Lean.Parser.Command.theorem"),
      ("short_name", toJson short.toString),
      ("full_name", toJson (fullName ns short).toString),
      ("is_example", toJson false), ("is_axiom", toJson false)]
  else
    Json.mkObj fields


def messagesJson (log : MessageLog) : IO Json := do
  let mut rows := #[]
  for m in log.reported.toArray ++ log.unreported.toArray do
    rows := rows.push <| Json.mkObj [
      ("severity", toJson (match m.severity with | .error => "error" | .warning => "warning" | .information => "information")),
      ("line", toJson m.pos.line), ("column", toJson m.pos.column),
      ("text", toJson (← m.data.toString))]
  return Json.arr rows

partial def inspectCommands : FrontendM (Array Json × Array (Nat × Name)) := do
  let mut rows := #[]
  let mut obligations := #[]
  repeat
    let before ← get
    let ns := before.commandState.scopes.head!.currNamespace
    setMessages {}
    let stdout ← IO.mkRef { : IO.FS.Stream.Buffer }
    let stderr ← IO.mkRef { : IO.FS.Stream.Buffer }
    let done ← IO.withStdout (IO.FS.Stream.ofBuffer stdout) <|
      IO.withStderr (IO.FS.Stream.ofBuffer stderr) processCommand
    let out := String.fromUTF8! (← stdout.get).data
    let err := String.fromUTF8! (← stderr.get).data
    let after ← get
    let cmd := after.commands.back!
    let msgs ← messagesJson after.commandState.messages
    let errors := after.commandState.messages.hasErrors
    if done && !errors then break
    let base := commandJson cmd ns
    let row := Json.mkObj [
      ("event", toJson "command"), ("index", toJson rows.size),
      ("syntax", base), ("start", toJson before.parserState.pos.byteIdx),
      ("stop", toJson after.parserState.pos.byteIdx),
      ("clean", toJson (!errors)), ("messages", msgs),
      ("stdout", toJson out), ("stderr", toJson err)]
    let kind := if cmd.isOfKind ``Parser.Command.declaration then cmd[1].getKind else cmd.getKind
    let short? := if kind == ``Parser.Command.theorem then declarationName? cmd[1] else lemmaName? cmd
    if kind == ``Parser.Command.theorem || short?.isSome then
      let mut actual := short?.map (fullName ns) |>.getD Name.anonymous
      -- Use source ranges to recover private/protected identities from elaboration.
      let nameSyntax := if kind == ``Parser.Command.theorem then cmd[1][1][0] else cmd[1][1][0]
      if let some pos := nameSyntax.getPos? then
        let position := (← getInputContext).fileMap.toPosition pos
        for (name, _) in after.commandState.env.constants.map₂.toList do
          if let some ranges := declRangeExt.find? (level := .server) after.commandState.env name then
            if ranges.selectionRange.pos == position then actual := name
      obligations := obligations.push (rows.size, actual)
    rows := rows.push row
    if done then break
    if after.parserState.pos.byteIdx <= before.parserState.pos.byteIdx then
      throw <| IO.Error.userError "frontend made no progress"
  return (rows, obligations)

def inspectFile (path output : System.FilePath) : IO Unit := do
  let input ← IO.FS.readFile path
  let ictx := Parser.mkInputContext input path.toString
  let (header, ps, msgs) ← Parser.parseHeader ictx
  let opts := ({} : Options).setBool `Elab.async false
  let (env, headerMsgs) ← Elab.processHeader header opts msgs ictx
  let initial : Frontend.State := {
    commandState := Command.mkState env {} opts
    parserState := ps
    cmdPos := ps.pos }
  let ((rows, obligations), final) ← (inspectCommands.run { inputCtx := ictx }).run initial
  let env := final.commandState.env
  let mut proofs := #[]
  for (index, name) in obligations do
    let info := env.checked.get.find? name
    let resolved := info.any (fun c => match c with | .thmInfo _ => true | _ => false)
    let (_, deps) := ((CollectAxioms.collect name).run env).run {}
    proofs := proofs.push <| Json.mkObj [
      ("command_index", toJson index), ("name", toJson name.toString),
      ("resolved", toJson resolved), ("axioms", toJson (deps.axioms.map Name.toString))]
  let result := Json.mkObj [
    ("schema", toJson "e13-declaration-probe-v2"),
    ("header_messages", ← messagesJson headerMsgs),
    ("header_clean", toJson (!headerMsgs.hasErrors)),
    ("commands", Json.arr rows), ("theorems", Json.arr proofs),
    ("terminal", toJson true)]
  IO.FS.writeFile output (result.compress ++ "\n")

def main (args : List String) : IO UInt32 := do
  match args with
  | ["--capture-control"] =>
    IO.println "e13v2-raw-stdout-control"
    IO.eprintln "e13v2-raw-stderr-control"
    pure 0
  | [path, output] => inspectFile path output; pure 0
  | _ => IO.eprintln "usage: DeclarationProbe_v2.lean <source> <json-output>"; pure 2
