Below is a concise “recipe” that reflects what is working **right now (July 2025)** for people running the very latest PyTorch 2.8 nightly and ComfyUI inside a RunPod Serverless worker.
It combines the commands shown in the official install matrix, the RunPod worker-comfyui docs, and the freshest Reddit / forum threads where early adopters are already on CUDA 12.8 GPUs such as the RTX 5090.

---

## 1 · Why PyTorch 2.8 is _nightly-only_ (so far)

-   PyTorch 2.8 has not yet hit the stable channel; the binary wheels live on the _nightly_ index and are required for GPUs with the new **sm_90 / sm_120** compute capabilities (50-series cards). ([PyTorch Forums][1], [PyTorch Forums][2])
-   The nightly wheels are published for CUDA 12.8 (`cu128`) and can be installed in one line (see next section). ([PyTorch Forums][3])

---

## 2 · Get PyTorch 2.8 nightly + helpers inside any image

```bash
# ALWAYS run inside the image you intend to ship
pip install --upgrade pip setuptools wheel
pip install --pre torch torchvision torchaudio \
  --index-url https://download.pytorch.org/whl/nightly/cu128
# Optional speed-ups often used with ComfyUI
pip install xformers flash-attn==2.5.3 triton
```

-   The `--pre` flag pulls the nightly build; the URL is taken directly from the PyTorch install wizard when you select “Nightly / Linux / CUDA 12.8”. ([PyTorch Documentation][4])
-   Forum mods confirmed this is the only officially-supported path right now. ([PyTorch Forums][5])

---

## 3 · Pick a base image (two practical choices)

| Approach                                    | Image tag                                                        | Pros                                                               | Cons                               |
| ------------------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------ | ---------------------------------- |
| **A. PyTorch-first**                        | `runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04` | Clean, 12 GB, Torch already present                                | You must add ComfyUI yourself      |
| **B. ComfyUI-first** (most people use this) | `runpod/worker-comfyui:5.3.0-base-cuda12.8.1`                    | ComfyUI server, API wrapper & handler already wired for Serverless | Torch may lag; upgrade it as in §2 |

Docker Hub lists both tags, each built within the last two weeks. ([Docker Hub][6])

---

## 4 · Example Dockerfile for **Option B** (upgrade Torch + add nodes)

```dockerfile
FROM runpod/worker-comfyui:5.3.0-base-cuda12.8.1

# --- 1. Make the image Torch-2.8 ready ---
RUN pip install --no-cache-dir --pre torch torchvision torchaudio \
      --index-url https://download.pytorch.org/whl/nightly/cu128 \
 && pip install --no-cache-dir xformers flash-attn==2.5.3 triton

# --- 2. Install any custom ComfyUI nodes you need ---
RUN comfy-node-install \
      comfyui-essentials \
      ComfyUI-VideoHelperSuite \
      comfyui_ipadapter_plus

# --- 3. Minor CUDA env tweaks often recommended on RunPod ---
ENV TORCH_CUDA_ARCH_LIST="9.0" \
    CUDA_LAUNCH_BLOCKING="1" \
    TORCH_USE_CUDA_DSA="1"

# --- 4. Keep original entrypoint; ComfyUI handler.py expects it ---
CMD ["./start.sh"]
```

-   `comfy-node-install` is recommended by the RunPod worker-comfyui docs and Reddit guides because it resolves Python deps automatically. ([GitHub][7], [Reddit][8])

---

## 5 · Create & deploy the Serverless worker

1. **Repo**: push the Dockerfile above (or your own) to GitHub.
2. **runpodctl** (or web UI):

    ```bash
    runpodctl create endpoint \
      --name comfy-torch28 \
      --image ghcr.io/<you>/my-comfy:latest \
      --gpu "NVIDIA-RTX5090-24GB" \
      --timeout 600
    ```

3. Attach a **Network Volume** that already contains your models (`/runpod-volume/ComfyUI`).
4. In the _Start-Script_ field use the common symlink trick so the worker sees your volume:

    ```bash
    bash -c 'ln -sf /runpod-volume/ComfyUI /workspace/ComfyUI && exec /start.sh'
    ```

Detailed steps are documented in the RunPod “custom worker” tutorial. ([Runpod Documentation][9], [Runpod Documentation][10])

---

## 6 · Running a workflow

The deployed endpoint follows the JSON spec in _worker-comfyui_; you POST `workflow` and optional `inputs` to `/runsync` and receive images as Base64 or S3 URLs. ([GitHub][7])

---

## 7 · Common pitfalls & fixes

| Symptom                                                            | Fix                                                                                                            |                                            |
| ------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| `sm_120 is not compatible`                                         | You are still on a stable Torch 2.7 wheel; uninstall and reinstall **nightly** as in §2. ([PyTorch Forums][2]) |                                            |
| `Cannot execute because a node is missing the class_type property` | The JSON came from an older ComfyUI build; open it in latest desktop ComfyUI and re-export.                    |                                            |
| `CUDA error: no kernel image…` on first run                        | Ensure image tag ends in **cuda12.8.1**, and that \`pip list                                                   | grep torch\` only shows one Torch version. |
| Worker fetches no images (`success_no_images`)                     | The workflow lacks a “Save Image” node connected to the graph’s final output.                                  |                                            |

---

## 8 · Extra resources & community recipes

-   Detailed blog guide with step-by-step screenshots. ([mikedegeofroy.com][11])
-   DEV article showing an end-to-end Serverless deployment (earlier but still valid). ([DEV Community][12])
-   RunPod guide on automating ComfyUI + Flux pipelines at scale (good for batch jobs). ([Runpod][13])

---

### TL;DR

1. **Use the nightly wheel**: `pip install --pre torch ... --index-url …/cu128`.
2. **Base the image** on either `runpod/pytorch:2.8` (add ComfyUI) _or_ `runpod/worker-comfyui:5.3.0-base-cuda12.8.1` (upgrade Torch).
3. **Deploy** as a RunPod Serverless worker, mount your models, and call the `/runsync` endpoint with a valid ComfyUI workflow JSON.
   Follow this recipe and you’ll be on the _freshest_ stack available today, fully compatible with 50-series GPUs and the latest ComfyUI custom nodes.

[1]: https://discuss.pytorch.org/t/pytorch-support-for-sm120/216099?utm_source=chatgpt.com "Pytorch support for sm120 - deployment"
[2]: https://discuss.pytorch.org/t/rtx-5090-error-with-nightly-cu128-install/217478?utm_source=chatgpt.com "Rtx 5090 Error with nightly cu128 install - PyTorch Forums"
[3]: https://discuss.pytorch.org/t/error-could-not-find-a-version-that-satisfies-the-requirement-torch-from-versions-none/218843?utm_source=chatgpt.com "ERROR: Could not find a version that satisfies the requirement torch ..."
[4]: https://docs.pytorch.org/TensorRT/getting_started/installation.html?utm_source=chatgpt.com "Installing Torch-TensorRT - PyTorch documentation"
[5]: https://discuss.pytorch.org/t/my-rtx5080-gpu-cant-work-with-pytorch/217301?utm_source=chatgpt.com "My RTX5080 GPU can't work with PyTorch"
[6]: https://hub.docker.com/r/runpod/worker-comfyui/tags?utm_source=chatgpt.com "runpod/worker-comfyui Tags - Docker Hub"
[7]: https://github.com/runpod-workers/worker-comfyui?utm_source=chatgpt.com "runpod-workers/worker-comfyui - GitHub"
[8]: https://www.reddit.com/r/StableDiffusion/comments/1jdfs6e/automatic_installation_of_pytorch_28_nightly/?utm_source=chatgpt.com "Automatic installation of Pytorch 2.8 (Nightly), Triton & SageAttention ..."
[9]: https://docs.runpod.io/serverless/workers/custom-worker?utm_source=chatgpt.com "Build your first worker - Runpod Documentation"
[10]: https://docs.runpod.io/tutorials/serverless/run-your-first?utm_source=chatgpt.com "Run your first serverless endpoint with Stable Diffusion"
[11]: https://www.mikedegeofroy.com/blog/comfyui-serverless?utm_source=chatgpt.com "Deploying a ComfyUI Workflow on a Serverless Runpod Worker"
[12]: https://dev.to/husnain/deploy-comfyui-with-runpod-serverless-1i25?utm_source=chatgpt.com "Deploy ComfyUI with RunPod Serverless - DEV Community"
[13]: https://www.runpod.io/articles/guides/comfy-ui-flux?utm_source=chatgpt.com "Automate AI Image Workflows with ComfyUI + Flux on Runpod"
