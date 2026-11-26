# Changes made to cool_fox

A description of the local changes used in the tests. The code is not part of this repository.

## 1. FSR4 replaced by a plain upscale (`VICTORY_FSR4`)

On the Series S profile the title runs AMD's FSR4 neural network, which relies on FP8 matrix operations. On the RTX 2070, which lacks them, it took about 330 of 455 ms of GPU time per frame. The change leaves the network's programs out and replaces the one that applies its output with a bilinear upscale.

- Measured effect: from about 2.3 to about 6–7 fps in the prologue.
- Drawback: no temporal anti-aliasing, so edges look jagged.
- With `VICTORY_UPSCALER=6` this path is no longer used.

## 2. Fewer effects (`VICTORY_LOWFX`, off)

Leaves out some ray, reflection and fog programs. In manual sessions the difference was 0 to 8 % and unconfirmed. In the automated run it gave 12 % on its own and nothing clear on top of the best configuration.

## 3. Two compute programs translated for wave32

`CS_TransmissionVolumetrics_Tiled` (`5dc3b25986622949`) and its `_LocalLights` variant (`6f225b641c5b0708`) did not translate on a card with 32-thread waves. They now translate, pass the validator, create their pipeline and ran in an 8-minute session. Their visual output has not been reviewed.

`CS_DefragHeap_ComputeRelocations` (`02384a60fda6f2d0`) still does not work.

## 4. Texture size cap (`VICTORY_TEXTURE_MAX`)

Ported from VIctory-Belobug-AMD (commit `e942896`). It leaves out the larger mip levels of textures.

**Bug found while porting:** single-slice *array* views have to be adjusted too, not just 2D views. Without that, `CreateShaderResourceView` receives an out-of-range `MostDetailedMip` and the device is removed (`DXGI_ERROR_INVALID_CALL`). The Direct3D 12 debug layer names the call.

It only applies without `VICTORY_LEVELS_ON_DEMAND=1`.

## 5. Output size and upscaler (`VICTORY_OUTPUT`, `VICTORY_UPSCALER`)

Ported from the same code base VIctory-Belobug-AMD uses. It changes a few specific places of the executable in memory at load time, and only if they match the expected version.

## Settings without code changes

| Setting | Finding on NVIDIA |
|---|---|
| `VICTORY_CARD_AWAKE=1` | Adds a continuous workload on a compute queue. On this card it cost performance, and it also makes `nvidia-smi` report close to 100 % usage, which misleads when looking for the bottleneck |
| `VICTORY_CARD_BUFFERS_MB` | With 8 GB the default was 512 MB; at 2048 the copy-back time fell from 41 to about 15 ms |
