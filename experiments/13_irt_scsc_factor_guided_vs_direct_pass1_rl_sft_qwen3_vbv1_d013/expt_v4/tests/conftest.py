"""TLDR: Import only v4 modules and keep the test suite CPU-only in the shared runtime."""
import os
from pathlib import Path
import sys
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ['HF_HUB_OFFLINE']='1'
os.environ['PYTHONDONTWRITEBYTECODE']='1'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'phase2'))
