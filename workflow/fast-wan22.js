export default (prompt, options) => ({
    6: {
        inputs: {
            text: prompt,
            clip: ["38", 0],
        },
        class_type: "CLIPTextEncode",
        _meta: {
            title: "CLIP Text Encode (Positive Prompt)",
        },
    },
    7: {
        inputs: {
            text: "色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走",
            clip: ["38", 0],
        },
        class_type: "CLIPTextEncode",
        _meta: {
            title: "CLIP Text Encode (Negative Prompt)",
        },
    },
    8: {
        inputs: {
            samples: ["58", 0],
            vae: ["39", 0],
        },
        class_type: "VAEDecode",
        _meta: {
            title: "VAE Decode",
        },
    },
    37: {
        inputs: {
            unet_name: "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors",
            weight_dtype: "default",
        },
        class_type: "UNETLoader",
        _meta: {
            title: "Load Diffusion Model",
        },
    },
    38: {
        inputs: {
            clip_name: "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
            type: "wan",
            device: "default",
        },
        class_type: "CLIPLoader",
        _meta: {
            title: "Load CLIP",
        },
    },
    39: {
        inputs: {
            vae_name: "wan_2.1_vae.safetensors",
        },
        class_type: "VAELoader",
        _meta: {
            title: "Load VAE",
        },
    },
    50: {
        inputs: {
            width: 480,
            height: 480,
            length: 81,
            batch_size: 1,
            positive: ["6", 0],
            negative: ["7", 0],
            vae: ["39", 0],
            start_image: ["68", 0],
        },
        class_type: "WanImageToVideo",
        _meta: {
            title: "WanImageToVideo",
        },
    },
    52: {
        inputs: {
            image: "img1.png",
        },
        class_type: "LoadImage",
        _meta: {
            title: "Load Image",
        },
    },
    54: {
        inputs: {
            shift: 8.000000000000002,
            model: ["37", 0],
        },
        class_type: "ModelSamplingSD3",
        _meta: {
            title: "ModelSamplingSD3",
        },
    },
    55: {
        inputs: {
            shift: 8.000000000000002,
            model: ["56", 0],
        },
        class_type: "ModelSamplingSD3",
        _meta: {
            title: "ModelSamplingSD3",
        },
    },
    56: {
        inputs: {
            unet_name: "wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors",
            weight_dtype: "default",
        },
        class_type: "UNETLoader",
        _meta: {
            title: "Load Diffusion Model",
        },
    },
    57: {
        inputs: {
            add_noise: "enable",
            noise_seed: 194391468117728,
            steps: 6,
            cfg: 1,
            sampler_name: "euler",
            scheduler: "simple",
            start_at_step: 0,
            end_at_step: 3,
            return_with_leftover_noise: "enable",
            model: ["62", 0],
            positive: ["50", 0],
            negative: ["50", 1],
            latent_image: ["50", 2],
        },
        class_type: "KSamplerAdvanced",
        _meta: {
            title: "KSampler (Advanced)",
        },
    },
    58: {
        inputs: {
            add_noise: "disable",
            noise_seed: ["68", 1],
            steps: 6,
            cfg: 1,
            sampler_name: "euler",
            scheduler: "simple",
            start_at_step: 3,
            end_at_step: 10000,
            return_with_leftover_noise: "disable",
            model: ["63", 0],
            positive: ["50", 0],
            negative: ["50", 1],
            latent_image: ["57", 0],
        },
        class_type: "KSamplerAdvanced",
        _meta: {
            title: "KSampler (Advanced)",
        },
    },
    62: {
        inputs: {
            lora_name:
                "wan/Wan21_T2V_14B_lightx2v_cfg_step_distill_lora_rank32.safetensors",
            strength_model: 1.0000000000000002,
            model: ["54", 0],
        },
        class_type: "LoraLoaderModelOnly",
        _meta: {
            title: "LoraLoaderModelOnly",
        },
    },
    63: {
        inputs: {
            lora_name:
                "wan/Wan21_T2V_14B_lightx2v_cfg_step_distill_lora_rank32.safetensors",
            strength_model: 1.0000000000000002,
            model: ["55", 0],
        },
        class_type: "LoraLoaderModelOnly",
        _meta: {
            title: "LoraLoaderModelOnly",
        },
    },
    64: {
        inputs: {
            frame_rate: 24,
            loop_count: 0,
            filename_prefix: "wan2_2",
            format: "video/h264-mp4",
            pix_fmt: "yuv420p",
            crf: 19,
            save_metadata: true,
            trim_to_audio: false,
            pingpong: false,
            save_output: false,
            images: ["8", 0],
        },
        class_type: "VHS_VideoCombine",
        _meta: {
            title: "Video Combine 🎥🅥🅗🅢",
        },
    },
    68: {
        inputs: {
            width: 832,
            height: 832,
            interpolation: "lanczos",
            method: "fill / crop",
            condition: "always",
            multiple_of: 0,
            image: ["52", 0],
        },
        class_type: "ImageResize+",
        _meta: {
            title: "🔧 Image Resize",
        },
    },
});
