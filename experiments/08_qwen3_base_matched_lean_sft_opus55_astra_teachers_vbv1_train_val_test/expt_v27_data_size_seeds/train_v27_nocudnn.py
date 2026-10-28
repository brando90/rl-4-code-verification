import runpy, sys
import torch
torch.backends.cuda.enable_cudnn_sdp(False)
sys.argv = ["train_v27.py"] + sys.argv[1:]
runpy.run_path("train_v27.py", run_name="__main__")
