Tongyi-MAI/Z-Image-Turbo · Hugging Face



[![Hugging Face's logo](/front/assets/huggingface_logo-noborder.svg)
Hugging Face](/)

* [Models](/models)
* [Datasets](/datasets)
* [Spaces](/spaces)
* Community
* [Docs](/docs)
* [Enterprise](/enterprise)
* [Pricing](/pricing)
* ---
* [Log In](/login)
* [Sign Up](/join)

# [Tongyi-MAI](/Tongyi-MAI) / [Z-Image-Turbo](/Tongyi-MAI/Z-Image-Turbo) like 3.11k Follow Tongyi-MAI 2.03k

[Text-to-Image](/models?pipeline_tag=text-to-image)
[Diffusers](/models?library=diffusers)
[Safetensors](/models?library=safetensors)
[English](/models?language=en)
[ZImagePipeline](/models?other=diffusers%3AZImagePipeline)

arxiv:
2511.22699

arxiv:
2511.22677

arxiv:
2511.13649

License:
apache-2.0

[Model card](/Tongyi-MAI/Z-Image-Turbo)[Files
Files and versions


xet](/Tongyi-MAI/Z-Image-Turbo/tree/main)[Community

102](/Tongyi-MAI/Z-Image-Turbo/discussions)

Deploy

Use this model

* [✨ Z-Image](#✨-z-image "✨ Z-Image")
  + [📥 Model Zoo](#📥-model-zoo "📥 Model Zoo")
  + [🖼️ Showcase](#🖼️-showcase "🖼️ Showcase")
  + [🏗️ Model Architecture](#🏗️-model-architecture "🏗️ Model Architecture")
  + [📈 Performance](#📈-performance "📈 Performance")
  + [🚀 Quick Start](#🚀-quick-start "🚀 Quick Start")
* [🔬 Decoupled-DMD: The Acceleration Magic Behind Z-Image](#🔬-decoupled-dmd-the-acceleration-magic-behind-z-image "🔬 Decoupled-DMD: The Acceleration Magic Behind Z-Image")
* [🤖 DMDR: Fusing DMD with Reinforcement Learning](#🤖-dmdr-fusing-dmd-with-reinforcement-learning "🤖 DMDR: Fusing DMD with Reinforcement Learning")
* [⏬ Download](#⏬-download "⏬ Download")
* [📜 Citation](#📜-citation "📜 Citation")

# ⚡️- Image An Efficient Image Generation Foundation Model with Single-Stream Diffusion Transformer

[![Official Site](https://img.shields.io/badge/Official%20Site-333399.svg?logo=homepage)](https://tongyi-mai.github.io/Z-Image-blog/) 
[![GitHub](https://img.shields.io/badge/GitHub-Z--Image-181717?logo=github&logoColor=white)](https://github.com/Tongyi-MAI/Z-Image) 
[![Hugging Face](https://img.shields.io/badge/%F0%9F%A4%97%20Checkpoint-Z--Image--Turbo-yellow)](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo) 
[![Hugging Face](https://img.shields.io/badge/%F0%9F%A4%97%20Online_Demo-Z--Image--Turbo-blue)](https://huggingface.co/spaces/Tongyi-MAI/Z-Image-Turbo) 
[![Hugging Face](https://img.shields.io/badge/%F0%9F%A4%97%20Mobile_Demo-Z--Image--Turbo-red)](https://huggingface.co/spaces/akhaliq/Z-Image-Turbo) 
[![ModelScope Model](https://img.shields.io/badge/%F0%9F%A4%96%20Checkpoint-Z--Image--Turbo-624aff)](https://www.modelscope.cn/models/Tongyi-MAI/Z-Image-Turbo) 
[![ModelScope Space](https://img.shields.io/badge/%F0%9F%A4%96%20Online_Demo-Z--Image--Turbo-17c7a7)](https://www.modelscope.cn/aigc/imageGeneration?tab=advanced&versionId=469191&modelType=Checkpoint&sdVersion=Z_IMAGE_TURBO&modelUrl=modelscope%253A%252F%252FTongyi-MAI%252FZ-Image-Turbo%253Frevision%253Dmaster%7D%7BOnline) 
[![Art Gallery PDF](https://img.shields.io/badge/%F0%9F%96%BC%20Art_Gallery-PDF-ff69b4)](/Tongyi-MAI/Z-Image-Turbo/blob/main/assets/Z-Image-Gallery.pdf) 
[![Web Art Gallery](https://img.shields.io/badge/%F0%9F%8C%90%20Web_Art_Gallery-online-00bfff)](https://modelscope.cn/studios/Tongyi-MAI/Z-Image-Gallery/summary) 
[![](https://img.shields.io/badge/Report-b5212f.svg?logo=arxiv)](https://arxiv.org/abs/2511.22699)

Welcome to the official repository for the Z-Image（造相）project!

## ✨ Z-Image

Z-Image is a powerful and highly efficient image generation model with **6B** parameters. Currently there are three variants:

* 🚀 **Z-Image-Turbo** – A distilled version of Z-Image that matches or exceeds leading competitors with only **8 NFEs** (Number of Function Evaluations). It offers **⚡️sub-second inference latency⚡️** on enterprise-grade H800 GPUs and fits comfortably within **16G VRAM consumer devices**. It excels in photorealistic image generation, bilingual text rendering (English & Chinese), and robust instruction adherence.
* 🧱 **Z-Image-Base** – The non-distilled foundation model. By releasing this checkpoint, we aim to unlock the full potential for community-driven fine-tuning and custom development.
* ✍️ **Z-Image-Edit** – A variant fine-tuned on Z-Image specifically for image editing tasks. It supports creative image-to-image generation with impressive instruction-following capabilities, allowing for precise edits based on natural language prompts.

### 📥 Model Zoo

| Model | Hugging Face | ModelScope |
| --- | --- | --- |
| **Z-Image-Turbo** | [Hugging Face](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo)   [Hugging Face Space](https://huggingface.co/spaces/Tongyi-MAI/Z-Image-Turbo) | [ModelScope Model](https://www.modelscope.cn/models/Tongyi-MAI/Z-Image-Turbo)   [ModelScope Space](https://www.modelscope.cn/aigc/imageGeneration?tab=advanced&versionId=469191&modelType=Checkpoint&sdVersion=Z_IMAGE_TURBO&modelUrl=modelscope%3A%2F%2FTongyi-MAI%2FZ-Image-Turbo%3Frevision%3Dmaster) |
| **Z-Image-Base** | *To be released* | *To be released* |
| **Z-Image-Edit** | *To be released* | *To be released* |

### 🖼️ Showcase

📸 **Photorealistic Quality**: **Z-Image-Turbo** delivers strong photorealistic image generation while maintaining excellent aesthetic quality.

[![Showcase of Z-Image on Photo-realistic image Generation](/Tongyi-MAI/Z-Image-Turbo/resolve/main/assets/showcase_realistic.png)](/Tongyi-MAI/Z-Image-Turbo/blob/main/assets/showcase_realistic.png)

📖 **Accurate Bilingual Text Rendering**: **Z-Image-Turbo** excels at accurately rendering complex Chinese and English text.

[![Showcase of Z-Image on Bilingual Text Rendering](/Tongyi-MAI/Z-Image-Turbo/resolve/main/assets/showcase_rendering.png)](/Tongyi-MAI/Z-Image-Turbo/blob/main/assets/showcase_rendering.png)

💡 **Prompt Enhancing & Reasoning**: Prompt Enhancer empowers the model with reasoning capabilities, enabling it to transcend surface-level descriptions and tap into underlying world knowledge.

[![reasoning.jpg](/Tongyi-MAI/Z-Image-Turbo/resolve/main/assets/reasoning.png)](/Tongyi-MAI/Z-Image-Turbo/blob/main/assets/reasoning.png)

🧠 **Creative Image Editing**: **Z-Image-Edit** shows a strong understanding of bilingual editing instructions, enabling imaginative and flexible image transformations.

[![Showcase of Z-Image-Edit on Image Editing](/Tongyi-MAI/Z-Image-Turbo/resolve/main/assets/showcase_editing.png)](/Tongyi-MAI/Z-Image-Turbo/blob/main/assets/showcase_editing.png)

### 🏗️ Model Architecture

We adopt a **Scalable Single-Stream DiT** (S3-DiT) architecture. In this setup, text, visual semantic tokens, and image VAE tokens are concatenated at the sequence level to serve as a unified input stream, maximizing parameter efficiency compared to dual-stream approaches.

[![Architecture of Z-Image and Z-Image-Edit](/Tongyi-MAI/Z-Image-Turbo/resolve/main/assets/architecture.webp)](/Tongyi-MAI/Z-Image-Turbo/blob/main/assets/architecture.webp)

### 📈 Performance

According to the Elo-based Human Preference Evaluation (on [*Alibaba AI Arena*](https://aiarena.alibaba-inc.com/corpora/arena/leaderboard?arenaType=T2I)), Z-Image-Turbo shows highly competitive performance against other leading models, while achieving state-of-the-art results among open-source models.

[![Z-Image Elo Rating on AI Arena](/Tongyi-MAI/Z-Image-Turbo/resolve/main/assets/leaderboard.png)  
 Click to view the full leaderboard](https://aiarena.alibaba-inc.com/corpora/arena/leaderboard?arenaType=T2I)

### 🚀 Quick Start

Install the latest version of diffusers, use the following command:

Click here for details for why you need to install diffusers from source

We have submitted two pull requests ([#12703](https://github.com/huggingface/diffusers/pull/12703) and [#12715](https://github.com/huggingface/diffusers/pull/12715)) to the 🤗 diffusers repository to add support for Z-Image. Both PRs have been merged into the latest official diffusers release.
Therefore, you need to install diffusers from source for the latest features and Z-Image support.

```
pip install git+https://github.com/huggingface/diffusers
```

```
import torch
from diffusers import ZImagePipeline

# 1. Load the pipeline
# Use bfloat16 for optimal performance on supported GPUs
pipe = ZImagePipeline.from_pretrained(
    "Tongyi-MAI/Z-Image-Turbo",
    torch_dtype=torch.bfloat16,
    low_cpu_mem_usage=False,
)
pipe.to("cuda")

# [Optional] Attention Backend
# Diffusers uses SDPA by default. Switch to Flash Attention for better efficiency if supported:
# pipe.transformer.set_attention_backend("flash")    # Enable Flash-Attention-2
# pipe.transformer.set_attention_backend("_flash_3") # Enable Flash-Attention-3

# [Optional] Model Compilation
# Compiling the DiT model accelerates inference, but the first run will take longer to compile.
# pipe.transformer.compile()

# [Optional] CPU Offloading
# Enable CPU offloading for memory-constrained devices.
# pipe.enable_model_cpu_offload()

prompt = "Young Chinese woman in red Hanfu, intricate embroidery. Impeccable makeup, red floral forehead pattern. Elaborate high bun, golden phoenix headdress, red flowers, beads. Holds round folding fan with lady, trees, bird. Neon lightning-bolt lamp (⚡️), bright yellow glow, above extended left palm. Soft-lit outdoor night background, silhouetted tiered pagoda (西安大雁塔), blurred colorful distant lights."

# 2. Generate Image
image = pipe(
    prompt=prompt,
    height=1024,
    width=1024,
    num_inference_steps=9,  # This actually results in 8 DiT forwards
    guidance_scale=0.0,     # Guidance should be 0 for the Turbo models
    generator=torch.Generator("cuda").manual_seed(42),
).images[0]

image.save("example.png")
```

## 🔬 Decoupled-DMD: The Acceleration Magic Behind Z-Image

[![arXiv](https://img.shields.io/badge/arXiv-2511.22677-b31b1b.svg)](https://arxiv.org/abs/2511.22677)

Decoupled-DMD is the core few-step distillation algorithm that empowers the 8-step Z-Image model.

Our core insight in Decoupled-DMD is that the success of existing DMD (Distributaion Matching Distillation) methods is the result of two independent, collaborating mechanisms:

* **CFG Augmentation (CA)**: The primary **engine** 🚀 driving the distillation process, a factor largely overlooked in previous work.
* **Distribution Matching (DM)**: Acts more as a **regularizer** ⚖️, ensuring the stability and quality of the generated output.

By recognizing and decoupling these two mechanisms, we were able to study and optimize them in isolation. This ultimately motivated us to develop an improved distillation process that significantly enhances the performance of few-step generation.

[![Diagram of Decoupled-DMD](/Tongyi-MAI/Z-Image-Turbo/resolve/main/assets/decoupled-dmd.webp)](/Tongyi-MAI/Z-Image-Turbo/blob/main/assets/decoupled-dmd.webp)

## 🤖 DMDR: Fusing DMD with Reinforcement Learning

[![arXiv](https://img.shields.io/badge/arXiv-2511.13649-b31b1b.svg)](https://arxiv.org/abs/2511.13649)

Building upon the strong foundation of Decoupled-DMD, our 8-step Z-Image model has already demonstrated exceptional capabilities. To achieve further improvements in terms of semantic alignment, aesthetic quality, and structural coherence—while producing images with richer high-frequency details—we present **DMDR**.

Our core insight behind DMDR is that Reinforcement Learning (RL) and Distribution Matching Distillation (DMD) can be synergistically integrated during the post-training of few-step models. We demonstrate that:

* **RL Unlocks the Performance of DMD** 🚀
* **DMD Effectively Regularizes RL** ⚖️

[![Diagram of DMDR](/Tongyi-MAI/Z-Image-Turbo/resolve/main/assets/DMDR.webp)](/Tongyi-MAI/Z-Image-Turbo/blob/main/assets/DMDR.webp)

## ⏬ Download

```
pip install -U huggingface_hub
HF_XET_HIGH_PERFORMANCE=1 hf download Tongyi-MAI/Z-Image-Turbo
```

## 📜 Citation

If you find our work useful in your research, please consider citing:

```
@article{team2025zimage,
  title={Z-Image: An Efficient Image Generation Foundation Model with Single-Stream Diffusion Transformer},
  author={Z-Image Team},
  journal={arXiv preprint arXiv:2511.22699},
  year={2025}
}

@article{liu2025decoupled,
  title={Decoupled DMD: CFG Augmentation as the Spear, Distribution Matching as the Shield},
  author={Dongyang Liu and Peng Gao and David Liu and Ruoyi Du and Zhen Li and Qilong Wu and Xin Jin and Sihan Cao and Shifeng Zhang and Hongsheng Li and Steven Hoi},
  journal={arXiv preprint arXiv:2511.22677},
  year={2025}
}

@article{jiang2025distribution,
  title={Distribution Matching Distillation Meets Reinforcement Learning},
  author={Jiang, Dengyang and Liu, Dongyang and Wang, Zanyi and Wu, Qilong and Jin, Xin and Liu, David and Li, Zhen and Wang, Mengmeng and Gao, Peng and Yang, Harry},
  journal={arXiv preprint arXiv:2511.13649},
  year={2025}
}
```

Downloads last month
:   329,981

Inference Providers
[NEW](https://huggingface.co/docs/inference-providers)

fal

[Text-to-Image](/tasks/text-to-image "Learn more about text-to-image")

Generate

View Code Snippets

Maximize

## Model tree for Tongyi-MAI/Z-Image-Turbo

Adapters

[148 models](/models?other=base_model:adapter:Tongyi-MAI/Z-Image-Turbo)

Finetunes

[38 models](/models?other=base_model:finetune:Tongyi-MAI/Z-Image-Turbo)

Quantizations

[18 models](/models?other=base_model:quantized:Tongyi-MAI/Z-Image-Turbo)

## Spaces using Tongyi-MAI/Z-Image-Turbo 100

[![](https://cdn-avatars.huggingface.co/v1/production/uploads/64379d79fac5ea753f1c10f3/fxHO6QoYjdv9_LTyiUD3g.jpeg)

Tongyi-MAI/Z-Image-Turbo](/spaces/Tongyi-MAI/Z-Image-Turbo)[🖼️

mrfakename/Z-Image-Turbo](/spaces/mrfakename/Z-Image-Turbo)[🖼

AiSudo/ZIT-Controlnet](/spaces/AiSudo/ZIT-Controlnet)[🐢

anycoderapps/Z-Image-Turbo](/spaces/anycoderapps/Z-Image-Turbo)[🖼️

yingzhac/Z\_image\_NSFW](/spaces/yingzhac/Z_image_NSFW)[💃

AiSudo/ZIT-Inpaint](/spaces/AiSudo/ZIT-Inpaint)[🧪

prithivMLmods/Z-Image-Turbo-LoRA-DLC](/spaces/prithivMLmods/Z-Image-Turbo-LoRA-DLC)[💻

ovi054/Z-Image-LORA](/spaces/ovi054/Z-Image-LORA)[👩🏻‍🎤

linoyts/Z-Image-Portrait](/spaces/linoyts/Z-Image-Portrait)[🏃

jinguotianxin/Z-Image-Turbo](/spaces/jinguotianxin/Z-Image-Turbo)[🔥

prithivMLmods/TRELLIS.2-Text-to-3D](/spaces/prithivMLmods/TRELLIS.2-Text-to-3D)[🖼

qqnyanddld/its-my-party-time](/spaces/qqnyanddld/its-my-party-time)
+ 95 Spaces
+ 88 Spaces

## Collection including Tongyi-MAI/Z-Image-Turbo

[#### Z-Image

Collection

4 items
• 
Updated
19 days ago
•

91](/collections/Tongyi-MAI/z-image)



System theme

Company

[TOS](/terms-of-service)
[Privacy](/privacy)
[About](/huggingface)
[Careers](https://apply.workable.com/huggingface/)


Website

[Models](/models)
[Datasets](/datasets)
[Spaces](/spaces)
[Pricing](/pricing)
[Docs](/docs)