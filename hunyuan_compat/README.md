# hunyuan_compat — `hy3dgen` compatibility shim

The Hunyuan3D **multi-view** model (`tencent/Hunyuan3D-2mv`) ships a `config.yaml`
that references classes under the original `hy3dgen.shapegen.*` namespace, but the
`Hunyuan3D-2.1-mac` fork renamed that package to `hy3dshape.*`. Without a bridge,
loading the 2mv model fails with `ModuleNotFoundError: No module named 'hy3dgen'`.

This package re-exports the six classes the 2mv config needs from their real
locations in the fork, so `get_obj_from_str("hy3dgen.shapegen.models.Hunyuan3DDiT")`
(etc.) resolves. `image_to_stl.py` adds this directory to `sys.path` automatically;
nothing needs to be copied into the third-party clone.

Maps:
- `hy3dgen.shapegen.models` → `Hunyuan3DDiT`, `ShapeVAE`, `SingleImageEncoder`, `DinoImageEncoderMV`, …
- `hy3dgen.shapegen.schedulers` → `FlowMatchEulerDiscreteScheduler`
- `hy3dgen.shapegen.preprocessors` → `ImageProcessorV2`, `MVImageProcessorV2`
- `hy3dgen.shapegen.pipelines` → `Hunyuan3DDiTFlowMatchingPipeline`
