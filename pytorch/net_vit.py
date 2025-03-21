import imp
from pydoc import cli
from traceback import print_tb
from grpc import ClientCallDetails
import torch
from torch import nn
from torchmtlr import MTLR

from typing import Sequence, Tuple, Union

from monai.networks.blocks.dynunet_block import UnetOutBlock
from monai.networks.blocks.unetr_block import UnetrBasicBlock, UnetrPrUpBlock, UnetrUpBlock
#from monai.networks.nets.vit import ViT
from monai.utils import ensure_tuple_rep
from einops import repeat, rearrange

import sys

#Number of clin_var
n_clin_var = 16
# n_clin_var = 12


def flatten_layers(arr):
    return [i for sub in arr for i in sub]


class UNETR(nn.Module):
    """
    UNETR based on: "Hatamizadeh et al.,
    UNETR: Transformers for 3D Medical Image Segmentation <https://arxiv.org/abs/2103.10504>"
    """

    def __init__(
                    self,
                    hparams : dict,
                    in_channels: int,
                    out_channels: int,
                    img_size: Union[Sequence[int], int],
                    feature_size: int = 16,
                    hidden_size: int = 768,
                    mlp_dim: int = 3072,
                    num_heads: int = 12,
                    pos_embed: str = "conv",
                    norm_name: Union[Tuple, str] = "instance",
                    conv_block: bool = True,
                    res_block: bool = True,
                    dropout_rate: float = 0.0,
                    spatial_dims: int = 3,
                ) -> None:


        super().__init__()

        if not (0 <= dropout_rate <= 1):
            raise ValueError("dropout_rate should be between 0 and 1.")

        if hidden_size % num_heads != 0:
            raise ValueError("hidden_size should be divisible by num_heads.")

        self.num_layers = hparams['num_layers']
        img_size = ensure_tuple_rep(img_size, spatial_dims)
        
        self.patch_size = ensure_tuple_rep(feature_size, spatial_dims)
        self.feat_size = tuple(img_d // p_d for img_d, p_d in zip(img_size, self.patch_size))
        self.hidden_size = hidden_size
        self.classification = False
        self.vit = ViT(
            in_channels=in_channels,
            img_size=img_size,
            patch_size=self.patch_size,
            hidden_size=hidden_size,
            mlp_dim=mlp_dim,
            num_layers=self.num_layers,
            num_heads=num_heads,
            pos_embed=pos_embed,
            classification=self.classification,
            dropout_rate=dropout_rate,
            spatial_dims=spatial_dims,
        )
        
        config = {}
        config['num_of_attention_heads'] = num_heads
        config['hidden_size'] = hidden_size

        if hparams['n_dense'] <=0:
            
            self.fc_layers1 = nn.Dropout(hparams['dropout']) 
            
            self.mtlr1 = MTLR(hparams['hidden_size'] + n_clin_var, hparams['time_bins'])
            self.mtlr2 = MTLR(hparams['hidden_size'] + n_clin_var, hparams['time_bins'])
            self.mtlr3 = MTLR(hparams['hidden_size'] + n_clin_var, hparams['time_bins'])
            self.mtlr4 = MTLR(hparams['hidden_size'] + n_clin_var, hparams['time_bins'])
            self.mtlr5 = MTLR(hparams['hidden_size'] + n_clin_var, hparams['time_bins'])

        elif hparams['n_dense'] ==1:
            self.fc_layers1 = nn.Sequential(nn.Linear(hparams['hidden_size'] + n_clin_var, 64*hparams['dense_factor']), 
                          nn.BatchNorm1d(64*hparams['dense_factor']),
                          nn.ReLU(inplace=True), 
                          nn.Dropout(hparams['dropout']))
            
            self.mtlr1 = MTLR(64*hparams['dense_factor'], hparams['time_bins'])
            self.mtlr2 = MTLR(64*hparams['dense_factor'], hparams['time_bins'])
            self.mtlr3 = MTLR(64*hparams['dense_factor'], hparams['time_bins'])
            self.mtlr4 = MTLR(64*hparams['dense_factor'], hparams['time_bins'])
            self.mtlr5 = MTLR(64*hparams['dense_factor'], hparams['time_bins'])
            
        elif hparams['n_dense'] > 1:    
            self.fc_layers1 = nn.Sequential(nn.Linear(hparams['hidden_size'] + n_clin_var , 128*hparams['dense_factor']), 
                          nn.BatchNorm1d(128*hparams['dense_factor']),
                          nn.ReLU(inplace=True), 
                          nn.Dropout(hparams['dropout']),
                          nn.Linear(128*hparams['dense_factor'] , 64*hparams['dense_factor']), 
                          nn.BatchNorm1d(64*hparams['dense_factor']),
                          nn.ReLU(inplace=True), 
                          nn.Dropout(hparams['dropout']))
            
            self.mtlr1 = MTLR(64*hparams['dense_factor'], hparams['time_bins'])
            self.mtlr2 = MTLR(64*hparams['dense_factor'], hparams['time_bins'])
            self.mtlr3 = MTLR(64*hparams['dense_factor'], hparams['time_bins'])
            self.mtlr4 = MTLR(64*hparams['dense_factor'], hparams['time_bins'])
            self.mtlr5 = MTLR(64*hparams['dense_factor'], hparams['time_bins'])


    def forward(self, sample):

        sample_img, clin_var = sample
        # print('sample[target_mask]', sample_img['target_mask'].shape)
        # print('sample[input]', sample_img['input'].shape)
        img = torch.cat((sample_img['target_mask'][:,0:1,:], sample_img['input'][:,0:1,:]), dim=1) # concate CT and GTVp_Mask
        # x_in = (img, clin_var)
        
        x, hidden_states_out = self.vit(img)
        x = torch.mean(x, dim=1)
        
        x = torch.cat((x, clin_var), dim=1)

        x = self.fc_layers1(x)
        risk_out1 = self.mtlr1(x)
        risk_out2 = self.mtlr2(x)
        risk_out3 = self.mtlr3(x)
        risk_out4 = self.mtlr4(x)
        risk_out5 = self.mtlr5(x)
        
        return risk_out1,  risk_out2, risk_out3, risk_out4, risk_out5





# Copyright 2020 - 2021 MONAI Consortium
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from typing import Sequence, Union

import torch
import torch.nn as nn

# from monai.networks.blocks.patchembedding import PatchEmbeddingBlock
from monai.networks.blocks.transformerblock import TransformerBlock

# __all__ = ["ViT"]


class ViT(nn.Module):
    """
    Vision Transformer (ViT), based on: "Dosovitskiy et al.,
    An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale <https://arxiv.org/abs/2010.11929>"
    """

    def __init__(
        self,
        in_channels: int,
        img_size: Union[Sequence[int], int],
        patch_size: Union[Sequence[int], int],
        hidden_size: int = 768,
        mlp_dim: int = 3072,
        num_layers: int = 12,
        num_heads: int = 12,
        pos_embed: str = "conv",
        classification: bool = False,
        num_classes: int = 2,
        dropout_rate: float = 0.0,
        spatial_dims: int = 3,
    ) -> None:
        """
        Args:
            in_channels: dimension of input channels.
            img_size: dimension of input image.
            patch_size: dimension of patch size.
            hidden_size: dimension of hidden layer.
            mlp_dim: dimension of feedforward layer.
            num_layers: number of transformer blocks.
            num_heads: number of attention heads.
            pos_embed: position embedding layer type.
            classification: bool argument to determine if classification is used.
            num_classes: number of classes if classification is used.
            dropout_rate: faction of the input units to drop.
            spatial_dims: number of spatial dimensions.

        Examples::

            # for single channel input with image size of (96,96,96), conv position embedding and segmentation backbone
            >>> net = ViT(in_channels=1, img_size=(96,96,96), pos_embed='conv')

            # for 3-channel with image size of (128,128,128), 24 layers and classification backbone
            >>> net = ViT(in_channels=3, img_size=(128,128,128), pos_embed='conv', classification=True)

            # for 3-channel with image size of (224,224), 12 layers and classification backbone
            >>> net = ViT(in_channels=3, img_size=(224,224), pos_embed='conv', classification=True, spatial_dims=2)

        """

        super().__init__()

        if not (0 <= dropout_rate <= 1):
            raise ValueError("dropout_rate should be between 0 and 1.")

        if hidden_size % num_heads != 0:
            raise ValueError("hidden_size should be divisible by num_heads.")

        self.classification = classification
        self.patch_embedding = PatchEmbeddingBlock(
            in_channels=in_channels,
            img_size=img_size,
            patch_size=patch_size,
            hidden_size=hidden_size,
            num_heads=num_heads,
            pos_embed=pos_embed,
            dropout_rate=dropout_rate,
            spatial_dims=spatial_dims,
        )
        self.blocks = nn.ModuleList(
            [TransformerBlock(hidden_size, mlp_dim, num_heads, dropout_rate) for i in range(num_layers)]
        )
        self.norm = nn.LayerNorm(hidden_size)
        if self.classification:
            self.cls_token = nn.Parameter(torch.zeros(1, 1, hidden_size))
            self.classification_head = nn.Sequential(nn.Linear(hidden_size, num_classes), nn.Tanh())
            


    def forward(self, x):
        
        x = self.patch_embedding(x) #img, clin_var = x


        
        if self.classification:
            cls_token = self.cls_token.expand(x.shape[0], -1, -1)
            x = torch.cat((cls_token, x), dim=1)
        hidden_states_out = []
        for blk in self.blocks:
            x = blk(x)
            hidden_states_out.append(x)
        x = self.norm(x)
        if self.classification:
            x = self.classification_head(x[:, 0])
            
        return x, hidden_states_out
    
    
    
    # Copyright 2020 - 2021 MONAI Consortium
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import math
from typing import Sequence, Union

import numpy as np
import torch
import torch.nn as nn

from monai.networks.layers import Conv
from monai.utils import ensure_tuple_rep, optional_import
from monai.utils.module import look_up_option

Rearrange, _ = optional_import("einops.layers.torch", name="Rearrange")
SUPPORTED_EMBEDDING_TYPES = {"conv", "perceptron"}


class PatchEmbeddingBlock(nn.Module):
    """
    A patch embedding block, based on: "Dosovitskiy et al.,
    An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale <https://arxiv.org/abs/2010.11929>"

    Example::

        >>> from monai.networks.blocks import PatchEmbeddingBlock
        >>> PatchEmbeddingBlock(in_channels=4, img_size=32, patch_size=8, hidden_size=32, num_heads=4, pos_embed="conv")

    """

    def __init__(
        self,
        in_channels: int,
        img_size: Union[Sequence[int], int],
        patch_size: Union[Sequence[int], int],
        hidden_size: int,
        num_heads: int,
        pos_embed: str,
        dropout_rate: float = 0.0,
        spatial_dims: int = 3,
    ) -> None:
        """
        Args:
            in_channels: dimension of input channels.
            img_size: dimension of input image.
            patch_size: dimension of patch size.
            hidden_size: dimension of hidden layer.
            num_heads: number of attention heads.
            pos_embed: position embedding layer type.
            dropout_rate: faction of the input units to drop.
            spatial_dims: number of spatial dimensions.


        """

        super().__init__()

        if not (0 <= dropout_rate <= 1):
            raise ValueError("dropout_rate should be between 0 and 1.")

        if hidden_size % num_heads != 0:
            raise ValueError("hidden size should be divisible by num_heads.")

        self.pos_embed = look_up_option(pos_embed, SUPPORTED_EMBEDDING_TYPES)

        img_size = ensure_tuple_rep(img_size, spatial_dims)
        patch_size = ensure_tuple_rep(patch_size, spatial_dims)
        for m, p in zip(img_size, patch_size):
            if m < p:
                raise ValueError("patch_size should be smaller than img_size.")
            if self.pos_embed == "perceptron" and m % p != 0:
                raise ValueError("patch_size should be divisible by img_size for perceptron.")
        self.n_patches = np.prod([im_d // p_d for im_d, p_d in zip(img_size, patch_size)])
        self.patch_dim = in_channels * np.prod(patch_size)

        self.patch_embeddings: nn.Module
        if self.pos_embed == "conv":
            self.patch_embeddings = Conv[Conv.CONV, spatial_dims](
                in_channels=in_channels, out_channels=hidden_size, kernel_size=patch_size, stride=patch_size
            )
        elif self.pos_embed == "perceptron":
            # for 3d: "b c (h p1) (w p2) (d p3)-> b (h w d) (p1 p2 p3 c)"
            chars = (("h", "p1"), ("w", "p2"), ("d", "p3"))[:spatial_dims]
            from_chars = "b c " + " ".join(f"({k} {v})" for k, v in chars)
            to_chars = f"b ({' '.join([c[0] for c in chars])}) ({' '.join([c[1] for c in chars])} c)"
            axes_len = {f"p{i+1}": p for i, p in enumerate(patch_size)}
            self.patch_embeddings = nn.Sequential(
                Rearrange(f"{from_chars} -> {to_chars}", **axes_len), nn.Linear(self.patch_dim, hidden_size)
            )
            


        self.position_embeddings = nn.Parameter(torch.zeros(1, self.n_patches, hidden_size))
        self.cls_token = nn.Parameter(torch.zeros(1, 1, hidden_size))
        self.dropout = nn.Dropout(dropout_rate)
        self.trunc_normal_(self.position_embeddings, mean=0.0, std=0.02, a=-2.0, b=2.0)
        self.apply(self._init_weights)

    def _init_weights(self, m):
        if isinstance(m, nn.Linear):
            self.trunc_normal_(m.weight, mean=0.0, std=0.02, a=-2.0, b=2.0)
            if isinstance(m, nn.Linear) and m.bias is not None:
                nn.init.constant_(m.bias, 0)
        elif isinstance(m, nn.LayerNorm):
            nn.init.constant_(m.bias, 0)
            nn.init.constant_(m.weight, 1.0)

    def trunc_normal_(self, tensor, mean, std, a, b):
        # From PyTorch official master until it's in a few official releases - RW
        # Method based on https://people.sc.fsu.edu/~jburkardt/presentations/truncated_normal.pdf
        def norm_cdf(x):
            return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

        with torch.no_grad():
            l = norm_cdf((a - mean) / std)
            u = norm_cdf((b - mean) / std)
            tensor.uniform_(2 * l - 1, 2 * u - 1)
            tensor.erfinv_()
            tensor.mul_(std * math.sqrt(2.0))
            tensor.add_(mean)
            tensor.clamp_(min=a, max=b)
            return tensor

    def forward(self, img):
        # img, clin_var = x
        x = self.patch_embeddings(img)      

        if self.pos_embed == "conv":
            x = x.flatten(2).transpose(-1, -2)
            
        # x = torch.cat([clin_var, x], dim=1)

        embeddings = x + self.position_embeddings
        embeddings = self.dropout(embeddings)
        return embeddings

