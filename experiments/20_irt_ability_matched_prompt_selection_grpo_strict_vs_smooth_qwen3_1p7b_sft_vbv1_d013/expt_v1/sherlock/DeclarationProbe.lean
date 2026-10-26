/- TLDR: Emit parser-backed command spans and declaration identities for experiment 13. -/
import Lean
import Lean.Data.Json

open Lean

def jsonLine (value : Json) : IO Unit := IO.println value.compress

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

def namespaceName? (stx : Syntax) : Option Name :=
  if stx.isOfKind ``Parser.Command.namespace && stx.getNumArgs > 1 && stx[1].isIdent then some stx[1].getId else none

partial def inspectFile (path : System.FilePath) : IO Unit := do
  let input ← IO.FS.readFile path
  let bound := input.utf8ByteSize + 1
  let inputCtx := Parser.mkInputContext input path.toString
  let (header, state, messages) ← Parser.parseHeader inputCtx
  let (env, headerMessages) ← Elab.processHeader header {} messages inputCtx
  let rec loop (s : Parser.ModuleParserState) (msgs : MessageLog) (ns : Name)
      (scopes : List Name) (index fuel : Nat) : IO Unit := do
    let pmctx : Parser.ParserModuleContext := { env := env, options := {} }
    let (cmd, next, nextMsgs) := Parser.parseCommand inputCtx pmctx s msgs
    if Parser.isTerminalCommand cmd then
      jsonLine <| Json.mkObj [
        ("event", toJson "terminal"), ("parse_error", toJson nextMsgs.hasErrors),
        ("commands", toJson index)]
    else
      jsonLine (commandJson cmd ns)
      let (nextNamespace, nextScopes) :=
        if let some opened := namespaceName? cmd then
          (ns.append opened, ns :: scopes)
        else if cmd.isOfKind ``Parser.Command.section then
          (ns, ns :: scopes)
        else if cmd.isOfKind ``Parser.Command.end then
          match scopes with
          | prior :: rest => (prior, rest)
          | [] => (ns, [])
        else (ns, scopes)
      match fuel with
      | 0 => jsonLine <| Json.mkObj [("event", toJson "terminal"), ("parse_error", toJson true), ("commands", toJson index)]
      | fuel + 1 => loop next nextMsgs nextNamespace nextScopes (index + 1) fuel
  loop state headerMessages Name.anonymous [] 0 bound

def main (args : List String) : IO UInt32 := do
  match args with
  | [path] => inspectFile path; pure 0
  | _ => IO.eprintln "usage: DeclarationProbe.lean <source.lean>"; pure 2
