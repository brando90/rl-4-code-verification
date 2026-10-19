"""Check the fallback Transformers Qwen3 attention/backward path with a tiny random synthetic model."""
import argparse
import json
from pathlib import Path
import platform
import time


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    result=dict(status='FAILED',observed_unix=time.time(),host=platform.node(),pretrained_model_downloaded=False,
                experiment_training_started=False,synthetic_model_optimizer_control=True)
    try:
        import torch
        import transformers
        import datasets
        import accelerate
        from transformers import Qwen3Config,Qwen3ForCausalLM
        torch.manual_seed(0)
        config=Qwen3Config(vocab_size=128,hidden_size=128,intermediate_size=256,num_hidden_layers=2,
            num_attention_heads=4,num_key_value_heads=2,head_dim=32,max_position_embeddings=512,
            attention_dropout=0.0,use_cache=False)
        config._attn_implementation='sdpa'
        model=Qwen3ForCausalLM(config).to(device='cuda',dtype=torch.bfloat16)
        optimizer=torch.optim.AdamW(model.parameters(),lr=1e-4)
        tokens=torch.randint(0,128,(2,64),device='cuda')
        start=time.monotonic()
        loss=model(input_ids=tokens,labels=tokens).loss
        loss.backward()
        assert torch.isfinite(loss),'Nonfinite loss'
        assert all(torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None),'Nonfinite gradient'
        before=model.model.embed_tokens.weight.detach().float().clone()
        optimizer.step();torch.cuda.synchronize()
        assert not torch.equal(before,model.model.embed_tokens.weight.detach().float()),'No optimizer update'
        result.update(status='PASS',torch_version=torch.__version__,cuda_runtime=torch.version.cuda,
            transformers_version=transformers.__version__,datasets_version=datasets.__version__,
            accelerate_version=accelerate.__version__,device=torch.cuda.get_device_name(0),
            capability=torch.cuda.get_device_capability(0),parameters=sum(p.numel() for p in model.parameters()),
            attention='sdpa',loss=float(loss.detach()),elapsed_seconds=time.monotonic()-start,
            peak_allocated_bytes=torch.cuda.max_memory_allocated(),forward_backward_optimizer=True,
            limitation='Tiny random Qwen3 control only; no 1.7B throughput or peak-memory claim; runtime differs from SNAP')
    except Exception as exc:result['error']=f'{type(exc).__name__}: {exc}'
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True))
    raise SystemExit(0 if result['status']=='PASS' else 1)


if __name__=='__main__':main()
