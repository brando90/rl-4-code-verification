"""Plots and the full per env x model table for Exp 18a, from results/envs_18a.jsonl (CPU, matplotlib)."""
import json, sys, collections
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
R="expt_v1/results/"
rows=[json.loads(l) for l in open(R+"envs_18a.jsonl")]
M=["qwen3_0p6b","qwen3_1p7b","qwen3_4b"]; L={"qwen3_0p6b":"0.6B","qwen3_1p7b":"1.7B","qwen3_4b":"4B"}
C={"qwen3_0p6b":"#4c78a8","qwen3_1p7b":"#f58518","qwen3_4b":"#54a24b"}
by={(r["env_id"],r["model_tag"]):r for r in rows}
envs=sorted({r["env_id"] for r in rows})
# 1 pass rate by env per model
fig,ax=plt.subplots(figsize=(14,4.5))
for i,m in enumerate(M):
    ax.bar([j+(i-1)*0.27 for j in range(len(envs))],[by[(e,m)]["pass_rate"] for e in envs],0.27,label=L[m],color=C[m])
ax.axhspan(0.1,0.9,color="grey",alpha=0.08); ax.set_xticks(range(len(envs))); ax.set_xticklabels([e[3:] for e in envs],rotation=90,fontsize=6)
ax.set_ylabel("pass rate"); ax.set_title("Exp 18a: pass rate per environment and model (grey = learnable pass band)"); ax.legend()
fig.tight_layout(); fig.savefig(R+"plots/pass_by_env.png",dpi=130); plt.close(fig)
# 2 size transfer scatter
pairs=[("qwen3_0p6b","qwen3_1p7b"),("qwen3_0p6b","qwen3_4b"),("qwen3_1p7b","qwen3_4b")]
fig,axs=plt.subplots(1,3,figsize=(12,4))
for ax,(a,b) in zip(axs,pairs):
    for e in envs:
        ra,rb=by[(e,a)],by[(e,b)]; fd=ra["format_dominated"] or rb["format_dominated"]
        ax.scatter(ra["pass_rate"],rb["pass_rate"],c="red" if fd else "black",s=14,marker="x" if fd else "o")
    ax.plot([0,1],[0,1],"k:",lw=.7); ax.set_xlabel(L[a]+" pass"); ax.set_ylabel(L[b]+" pass")
fig.suptitle("Size transfer of difficulty (red x = a format-dominated cell)"); fig.tight_layout(); fig.savefig(R+"plots/size_transfer.png",dpi=130); plt.close(fig)
# 3 level vs pass by family
fams=sorted({r["family"] for r in rows}); fig,axs=plt.subplots(2,4,figsize=(14,6),sharey=True)
for ax,f in zip(axs.flat,fams):
    for m in M:
        ax.plot([0,1,2,3],[by[(f"rg/{f}/L{l}",m)]["pass_rate"] for l in range(4)],marker="o",color=C[m],label=L[m])
    ax.set_title(f,fontsize=9); ax.set_xticks(range(4))
axs[0,0].legend(); fig.suptitle("RG difficulty level vs pass rate"); fig.tight_layout(); fig.savefig(R+"plots/level_vs_pass.png",dpi=130); plt.close(fig)
# 4 coordinates
fig,axs=plt.subplots(1,3,figsize=(12,4))
for ax,k in zip(axs,["rho","H","alignment"]):
    for m in M:
        ax.scatter([r["pass_rate"] for r in rows if r["model_tag"]==m],[r[k] for r in rows if r["model_tag"]==m],s=12,color=C[m],label=L[m])
    ax.set_xlabel("pass rate"); ax.set_ylabel(k)
    if k=="rho": ax.set_yscale("symlog")
axs[0].legend(); fig.tight_layout(); fig.savefig(R+"plots/coordinates_vs_pass.png",dpi=130); plt.close(fig)
# table
with open(R+"table_18a.md","w") as f:
    f.write("| env | model | n items | n samples | pass | rho | H | align | tag rate | band | fmt-dom |\n|---|---|---|---|---|---|---|---|---|---|---|\n")
    for e in envs:
        for m in M:
            r=by[(e,m)]
            f.write(f"| {e[3:]} | {L[m]} | {r['n_items_observed']} | {r['n_responses']} | {r['pass_rate']:.3f} | {r['rho']:.3g} | {r['H']:.3f} | {r['alignment']:.3f} | {r['answer_tag_rate']:.2f} | {'Y' if r['in_learnable_band'] else ''} | {'Y' if r['format_dominated'] else ''} |\n")
