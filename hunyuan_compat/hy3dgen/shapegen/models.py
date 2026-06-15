# Re-export model classes at the legacy hy3dgen.shapegen.models path.
from hy3dshape.models.denoisers.hunyuan3ddit import Hunyuan3DDiT
from hy3dshape.models.autoencoders import ShapeVAE
from hy3dshape.models.conditioner import (
    SingleImageEncoder, ImageEncoder, CLIPImageEncoder,
    DinoImageEncoder, DinoImageEncoderMV,
)
