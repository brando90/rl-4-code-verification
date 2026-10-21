"""TLDR: Compare experiment 20's scoring smoke on Sherlock (frozen scorer via the D-109 logged entry, and experiment 13's adapter) against experiment 08 v16's recorded per-task scorer rows for the same trials, column by column, and print the adapter's strict/factored values and statuses."""
import csv, glob, json, sys
ref = {r["task"]: r for r in csv.DictReader(open(glob.glob(sys.argv[1] + "/*per_task.csv")[0]))}
new = {r["task"]: r for r in csv.DictReader(open(glob.glob(sys.argv[2] + "/*per_task.csv")[0]))}
part = {r["task_id"]: r for r in json.load(open(sys.argv[3]))["records"]}
print("scorer rows:", len(new), "statuses:", sorted({(r["scoring_status"], r["submission_status"]) for r in new.values()}))
cols = ("IC_ap", "IC_pp", "agent_compiles", "agent_n_ex", "agent_n_thm", "kernel_n_theorems", "kernel_n_honest", "kernel_probe_ok")
for t in part:
    r, q, x = ref[t], new[t], part[t]
    s_ref = float(r["IC_ap"] == "1.0" and r["IC_pp"] == "1.0")
    s_new = float(q["IC_ap"] == "1.0" and q["IC_pp"] == "1.0")
    same = all(r[c] == q[c] for c in cols)
    print(t[:58], "| v16 strict", s_ref, "| e20 strict", s_new, "| cols equal", same, "| adapter strict", x.get("strict"),
          "factored", x.get("factored_reward"), "status", x["status"], "compiles", x.get("compiles"), "thm", x.get("theorem_count"),
          "proved", x.get("proved_count"), "err", str(x.get("error", ""))[:60])
