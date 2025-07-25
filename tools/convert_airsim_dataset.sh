#!/usr/bin/env bash
DATA_ROOT=/home/liang/Projects/SurroundOcc/data/airsim_dataset
MAP_CLOUD_PATH=${DATA_ROOT}/map_cloud_1600x1600x600_0_50m.npy
POINT_CLOUD_RANGE="-50 -50 -5 50 50 3"
DEFAULT_SEMANTIC_LABEL=0
UAV_SEMANTIC_LABEL=30
EVTO_SEMANTIC_LABEL=31
RESOLUTION=0.5


python ./tools/data_converter/create_airsim_occupancy_gt.py \
    --airsim-data-root ${DATA_ROOT} \
    --map-cloud-path ${MAP_CLOUD_PATH} \
    --point-cloud-range ${POINT_CLOUD_RANGE} \
    --default-semantic-label ${DEFAULT_SEMANTIC_LABEL} \
    --uav-semantic-label ${UAV_SEMANTIC_LABEL} \
    --evtol-semantic-label ${EVTO_SEMANTIC_LABEL} \
    --resolution ${RESOLUTION}
