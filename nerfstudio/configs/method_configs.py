# Copyright 2022 the Regents of the University of California, Nerfstudio Team and contributors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Put all the method implementations in one location.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Dict, Union

import tyro

from nerfstudio.cameras.camera_optimizers import CameraOptimizerConfig
from nerfstudio.configs.base_config import ViewerConfig
from nerfstudio.configs.external_methods import ExternalMethodDummyTrainerConfig, get_external_methods
from nerfstudio.data.datamanagers.base_datamanager import VanillaDataManager, VanillaDataManagerConfig
from nerfstudio.data.datamanagers.full_images_datamanager import FullImageDatamanagerConfig
from nerfstudio.data.datamanagers.parallel_datamanager import ParallelDataManagerConfig
from nerfstudio.data.datamanagers.random_cameras_datamanager import RandomCamerasDataManagerConfig
from nerfstudio.data.dataparsers.blender_dataparser import BlenderDataParserConfig
from nerfstudio.data.dataparsers.dnerf_dataparser import DNeRFDataParserConfig
from nerfstudio.data.dataparsers.plenoptic_dataparser import PlenDataParserConfig
from nerfstudio.data.dataparsers.instant_ngp_dataparser import InstantNGPDataParserConfig
from nerfstudio.data.dataparsers.nerfstudio_dataparser import NerfstudioDataParserConfig
from nerfstudio.data.dataparsers.phototourism_dataparser import PhototourismDataParserConfig
from nerfstudio.data.dataparsers.sdfstudio_dataparser import SDFStudioDataParserConfig
from nerfstudio.data.dataparsers.sitcoms3d_dataparser import Sitcoms3DDataParserConfig
from nerfstudio.data.datasets.depth_dataset import DepthDataset
from nerfstudio.data.datasets.sdf_dataset import SDFDataset
from nerfstudio.data.datasets.semantic_dataset import SemanticDataset
from nerfstudio.data.pixel_samplers import PairPixelSamplerConfig
from nerfstudio.engine.optimizers import AdamOptimizerConfig, RAdamOptimizerConfig
from nerfstudio.engine.schedulers import (
    CosineDecaySchedulerConfig,
    ExponentialDecaySchedulerConfig,
    MultiStepSchedulerConfig,
)
from nerfstudio.engine.trainer import TrainerConfig
from nerfstudio.field_components.temporal_distortions import TemporalDistortionKind
from nerfstudio.fields.sdf_field import SDFFieldConfig
from nerfstudio.models.depth_nerfacto import DepthNerfactoModelConfig
from nerfstudio.models.generfacto import GenerfactoModelConfig
from nerfstudio.models.instant_ngp import InstantNGPModelConfig
from nerfstudio.models.mipnerf import MipNerfModel
from nerfstudio.models.nerfacto import NerfactoModelConfig
from nerfstudio.models.neus import NeuSModelConfig
from nerfstudio.models.neus_facto import NeuSFactoModelConfig
from nerfstudio.models.semantic_nerfw import SemanticNerfWModelConfig
from nerfstudio.models.splatfacto import SplatfactoModelConfig
from nerfstudio.models.splatfacto_ple import Splatfacto_pleModelConfig
from nerfstudio.models.tensorf import TensoRFModelConfig
from nerfstudio.models.vanilla_nerf import NeRFModel, VanillaModelConfig
from nerfstudio.pipelines.base_pipeline import VanillaPipelineConfig
from nerfstudio.pipelines.dynamic_batch import DynamicBatchPipelineConfig
from nerfstudio.plugins.registry import discover_methods

method_configs: Dict[str, Union[TrainerConfig, ExternalMethodDummyTrainerConfig]] = {}
descriptions = {
  
    "splatfacto": "Gaussian Splatting model",
}

method_configs["splatfacto"] = TrainerConfig(
    method_name="splatfacto",
    steps_per_eval_image=100,
    steps_per_eval_batch=0,
    steps_per_save=2000,
    steps_per_eval_all_images=1000,
    max_num_iterations=20000,
    mixed_precision=False,
    gradient_accumulation_steps={"camera_opt": 100},
    pipeline=VanillaPipelineConfig(
        datamanager=FullImageDatamanagerConfig(
            dataparser=DNeRFDataParserConfig(),
            cache_images_type="uint8",
        ),
        model=SplatfactoModelConfig(),
    ),
    optimizers={
        "xyz": {
            "optimizer": AdamOptimizerConfig(lr=1.6e-4*5, eps=1e-15),
            "scheduler": ExponentialDecaySchedulerConfig(
                lr_final=1.6e-6*5 ,
                max_steps=30000,
            ),
        },
        "t": {
            "optimizer": AdamOptimizerConfig(lr=1.6e-4, eps=1e-15),
            "scheduler": ExponentialDecaySchedulerConfig(
                lr_final=1.6e-6,
                max_steps=30000,
            ),
        },
        "features_dc": {
            "optimizer": AdamOptimizerConfig(lr=0.0025, eps=1e-15),
            "scheduler":None,
        },
        "features_rest": {
            "optimizer": AdamOptimizerConfig(lr=0.0025 / 20, eps=1e-15),
            "scheduler": None

        },
        "opacities": {
            "optimizer": AdamOptimizerConfig(lr=0.05, eps=1e-15),
            "scheduler": None,
        },
        "scales_xyz": {
            "optimizer": AdamOptimizerConfig(lr=0.005, eps=1e-15),
            "scheduler": None,
        },
        "scales_t": {
            "optimizer": AdamOptimizerConfig(lr=0.005, eps=1e-15),
            "scheduler": None,
        },
        "_objects_dc": {
            "optimizer": AdamOptimizerConfig(lr=0.005, eps=1e-15),
            "scheduler": None,
        },
        
        "quats1": {"optimizer": AdamOptimizerConfig(lr=0.001, eps=1e-15), "scheduler": None},
        "quats2": {"optimizer": AdamOptimizerConfig(lr=0.001, eps=1e-15), "scheduler": None},
        "camera_opt": {
            "optimizer": AdamOptimizerConfig(lr=1e-3, eps=1e-15),
            "scheduler": ExponentialDecaySchedulerConfig(lr_final=5e-5, max_steps=30000),
        },
    },
    viewer=ViewerConfig(num_rays_per_chunk=1 << 15),
    vis="viewer",
)

method_configs["splatfacto-big"] = TrainerConfig(
    method_name="splatfacto",
    steps_per_eval_image=100,
    steps_per_eval_batch=0,
    steps_per_save=2000,
    steps_per_eval_all_images=1000,
    max_num_iterations = 20000,
    mixed_precision=False,
    gradient_accumulation_steps={"camera_opt": 100},
    pipeline=VanillaPipelineConfig(
        datamanager=FullImageDatamanagerConfig(
            dataparser=PlenDataParserConfig(),
            cache_images_type="uint8",
        ),
        model=Splatfacto_pleModelConfig(),
    ),
    optimizers={
        "xyz": {
            "optimizer": AdamOptimizerConfig(lr=1.6e-4*6, eps=1e-15),
            "scheduler": ExponentialDecaySchedulerConfig(
                lr_final=1.6e-6*6 ,
                max_steps=30000,
            ),
        },
        "t": {
            "optimizer": AdamOptimizerConfig(lr=1.6e-4*6, eps=1e-15),
            "scheduler": ExponentialDecaySchedulerConfig(
                lr_final=1.6e-6*6,
                max_steps=30000,
            ),
        },
        "features_dc": {
            "optimizer": AdamOptimizerConfig(lr=0.0025, eps=1e-15),
            "scheduler":None
        },
        "features_rest": {
            "optimizer": AdamOptimizerConfig(lr=0.0025 / 20, eps=1e-15),
            "scheduler": None
        },
        "opacities": {
            "optimizer": AdamOptimizerConfig(lr=0.05, eps=1e-15),
            "scheduler": None,
        },
        "scales_xyz": {
            "optimizer": AdamOptimizerConfig(lr=0.005, eps=1e-15),
            "scheduler": None,
        },
        "scales_t": {
            "optimizer": AdamOptimizerConfig(lr=0.005, eps=1e-15),
            "scheduler": None,
        },
        
        "quats1": {"optimizer": AdamOptimizerConfig(lr=0.001, eps=1e-15), "scheduler": None},
        "quats2": {"optimizer": AdamOptimizerConfig(lr=0.001, eps=1e-15), "scheduler": None},
        "camera_opt": {
            "optimizer": AdamOptimizerConfig(lr=1e-3, eps=1e-15),
            "scheduler": ExponentialDecaySchedulerConfig(lr_final=5e-5, max_steps=30000),
        },
    },
    viewer=ViewerConfig(num_rays_per_chunk=1 << 15),
    vis="viewer",
)


def merge_methods(methods, method_descriptions, new_methods, new_descriptions, overwrite=True):
    """Merge new methods and descriptions into existing methods and descriptions.
    Args:
        methods: Existing methods.
        method_descriptions: Existing descriptions.
        new_methods: New methods to merge in.
        new_descriptions: New descriptions to merge in.
    Returns:
        Merged methods and descriptions.
    """
    methods = OrderedDict(**methods)
    method_descriptions = OrderedDict(**method_descriptions)
    for k, v in new_methods.items():
        if overwrite or k not in methods:
            methods[k] = v
            method_descriptions[k] = new_descriptions.get(k, "")
    return methods, method_descriptions


def sort_methods(methods, method_descriptions):
    """Sort methods and descriptions by method name."""
    methods = OrderedDict(sorted(methods.items(), key=lambda x: x[0]))
    method_descriptions = OrderedDict(sorted(method_descriptions.items(), key=lambda x: x[0]))
    return methods, method_descriptions


all_methods, all_descriptions = method_configs, descriptions
# Add discovered external methods
all_methods, all_descriptions = merge_methods(all_methods, all_descriptions, *discover_methods())
all_methods, all_descriptions = sort_methods(all_methods, all_descriptions)

# Register all possible external methods which can be installed with Nerfstudio
all_methods, all_descriptions = merge_methods(
    all_methods, all_descriptions, *sort_methods(*get_external_methods()), overwrite=False
)

AnnotatedBaseConfigUnion = tyro.conf.SuppressFixed[  # Don't show unparseable (fixed) arguments in helptext.
    tyro.conf.FlagConversionOff[
        tyro.extras.subcommand_type_from_defaults(defaults=all_methods, descriptions=all_descriptions)
    ]
]
"""Union[] type over config types, annotated with default instances for use with
tyro.cli(). Allows the user to pick between one of several base configurations, and
then override values in it."""
