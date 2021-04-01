from biologicalgraphs.utilities import dataIO
from biologicalgraphs.graphs.biological import node_generation, edge_generation
from biologicalgraphs.evaluation import comparestacks
from biologicalgraphs.cnns.biological import edges, nodes
from biologicalgraphs.transforms import seg2seg, seg2gold
from biologicalgraphs.skeletonization import generate_skeletons
from biologicalgraphs.algorithms import lifted_multicut
from biologicalgraphs.data_structures import meta_data
import h5py
import numpy as np
from intern.remote.boss import BossRemote
from intern import array

# the prefix name corresponds to the meta file in meta/{PREFIX}.meta
prefix = 'test'

# subset is either training, validation, or testing
subset = 'testing'

# Configure intern
config = {"protocol": "https",
        "host": "api.bossdb.io",
        "token": "public"}
rmt = BossRemote(config)

# Get data from bossdb
boss_data = array("bossdb://microns/pinky100_8x8x40/segmentation")
cutout = boss_data[1000:1020, 20000:21809, 30000:31336]
print('Cutout complete. \n')
print('Shape of cutout:', np.shape(cutout))

# Create metadata file
print('Creating metadata.. \n')
meta_data.WriteBossMetaFile(boss_data, cutout, prefix)
print('Metadata created. \n')

# Convert boss data to h5 for pipeline
print('Converting to h5... \n')
dataIO.WriteBossH5File(boss_data, cutout, prefix)
print('h5 created. \n')

# read the input segmentation data
segmentation = dataIO.ReadSegmentationData(prefix)

# remove the singleton slices
node_generation.RemoveSingletons(prefix, segmentation)

# need to update the prefix and segmentation
# removesingletons writes a new h5 file to disk
prefix = '{}-segmentation-wos'.format(prefix)
segmentation = dataIO.ReadSegmentationData(prefix)

# generate locations for segments that are too small
node_generation.GenerateNodes(prefix, segmentation, subset)

# run inference for node network
node_model_prefix = 'architectures/nodes-400nm-3x20x60x60-Kasthuri/nodes'
nodes.forward.Forward(prefix, node_model_prefix, segmentation, subset, evaluate=False)

# need to update the prefix and segmentation
# node generation writes a new h5 file to disk
prefix = '{}-reduced-{}'.format(prefix, node_model_prefix.split('/')[1])
segmentation = dataIO.ReadSegmentationData(prefix)

# generate the skeleton by getting high->low resolution mappings
# and running topological thinnings
seg2seg.DownsampleMapping(prefix, segmentation)
generate_skeletons.TopologicalThinning(prefix, segmentation)
generate_skeletons.FindEndpointVectors(prefix)

# run edge generation function
edge_generation.GenerateEdges(prefix, segmentation, subset)

# run inference for edge network
edge_model_prefix = 'architectures/edges-600nm-3x18x52x52-Kasthuri/edges'
edges.forward.Forward(prefix, edge_model_prefix, subset)

# run lifted multicut
lifted_multicut.LiftedMulticut(prefix, segmentation, edge_model_prefix)