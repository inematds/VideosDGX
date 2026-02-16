#!/usr/bin/env python3
"""
Patch diffusers LTX pipeline for video-only generation
Removes rope_interpolation_scale and adds audio parameter handling
Updated: 2026-02-16 02:17 - Using torch.zeros for audio tensors
"""

pipeline_path = '/usr/local/lib/python3.11/dist-packages/diffusers/pipelines/ltx/pipeline_ltx.py'

with open(pipeline_path, 'r') as f:
    content = f.read()

# Patch 1: Comment out rope_interpolation_scale (already done by sed, but include for completeness)
content = content.replace(
    '                        rope_interpolation_scale=rope_interpolation_scale,',
    '#                         rope_interpolation_scale=rope_interpolation_scale,'
)

# Patch 2: Add audio parameter handling for video-only generation
# Try to match either the original unpatch version or the old None-based patch
old_call_original = '''                with self.transformer.cache_context("cond_uncond"):
                    noise_pred = self.transformer(
                        hidden_states=latent_model_input,
                        encoder_hidden_states=prompt_embeds,
                        timestep=timestep,
                        encoder_attention_mask=prompt_attention_mask,
                        num_frames=latent_num_frames,
                        height=latent_height,
                        width=latent_width,
#                         rope_interpolation_scale=rope_interpolation_scale,
                        attention_kwargs=attention_kwargs,
                        return_dict=False,
                    )[0]'''

old_call_none = '''                # Create empty audio inputs for video-only generation
                batch_size_vid = latent_model_input.shape[0]
                audio_hidden_states = None  # Will use defaults in transformer
                audio_encoder_hidden_states = None  # Will use defaults in transformer

                with self.transformer.cache_context("cond_uncond"):
                    noise_pred = self.transformer(
                        hidden_states=latent_model_input,
                        audio_hidden_states=audio_hidden_states,
                        encoder_hidden_states=prompt_embeds,
                        audio_encoder_hidden_states=audio_encoder_hidden_states,
                        timestep=timestep,
                        encoder_attention_mask=prompt_attention_mask,
                        num_frames=latent_num_frames,
                        height=latent_height,
                        width=latent_width,
#                         rope_interpolation_scale=rope_interpolation_scale,
                        attention_kwargs=attention_kwargs,
                        return_dict=False,
                    )[0]'''

# Choose which pattern to match
old_call = old_call_none if old_call_none in content else old_call_original

new_call = '''                # Create empty audio inputs for video-only generation
                # torch is already imported at module level
                batch_size_vid = latent_model_input.shape[0]
                device = latent_model_input.device
                dtype = latent_model_input.dtype

                # Create dummy audio latents (empty tensor with correct shape)
                # Audio latents should have shape [batch, audio_frames, audio_channels]
                # Using minimal dimensions to avoid memory waste
                audio_hidden_states = torch.zeros(batch_size_vid, 1, 128, device=device, dtype=dtype)
                audio_encoder_hidden_states = torch.zeros(batch_size_vid, 1, 768, device=device, dtype=dtype)

                with self.transformer.cache_context("cond_uncond"):
                    noise_pred = self.transformer(
                        hidden_states=latent_model_input,
                        audio_hidden_states=audio_hidden_states,
                        encoder_hidden_states=prompt_embeds,
                        audio_encoder_hidden_states=audio_encoder_hidden_states,
                        timestep=timestep,
                        encoder_attention_mask=prompt_attention_mask,
                        num_frames=latent_num_frames,
                        height=latent_height,
                        width=latent_width,
#                         rope_interpolation_scale=rope_interpolation_scale,
                        attention_kwargs=attention_kwargs,
                        return_dict=False,
                    )[0]'''

if old_call in content:
    content = content.replace(old_call, new_call)
    print('✓ Audio parameters patch applied')
else:
    print('⚠ Warning: Audio parameters pattern not found')

with open(pipeline_path, 'w') as f:
    f.write(content)

print(f'✓ Pipeline patched: {pipeline_path}')
