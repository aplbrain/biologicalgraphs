from biologicalgraphs.utilities import dataIO
from biologicalgraphs.graphs.biological import node_generation, edge_generation
from biologicalgraphs.evaluation import comparestacks
from biologicalgraphs.cnns.biological import edges, nodes
from biologicalgraphs.transforms import seg2seg, seg2gold
from biologicalgraphs.skeletonization import generate_skeletons
from biologicalgraphs.algorithms import lifted_multicut
from intern.remote.boss import BossRemote

# Configure Boss
config = {"protocol": "https",
        "host": "api.bossdb.io",
        "token": "public"}
rmt = BossRemote(config)

# Load Minnie segmentation data
#pinky_dataset = array("bossdb://microns/pinky100_8x8x40/segmentation")
#segmentation = pinky_dataset[1000:1256, 10000:12048, 20000:22048]

print('Getting cutout \n')
#segmentation = rmt.get_cutout(rmt.get_channel('segmentation', 'microns', 'pinky100_8x8x40'), 0, [30000,30512], [20000,20512], [1000,1064])
segmentation = rmt.get_cutout(rmt.get_channel('segmentation', 'microns', 'pinky100_8x8x40'), 0, [30000,30020], [20000,20020], [1000,1020])

print('Cutout complete \n')

# prefix and subset are used for naming convention
prefix = 'pinky100-test'
subset = 'testing'

# remove the singleton slices
node_generation.RemoveSingletons(prefix, segmentation)
print('Removed Singletons \n')

# need to update the prefix and segmentation
# removesingletons writes a new h5 file to disk
prefix = '{}-segmentation-wos'.format(prefix)
segmentation = dataIO.ReadSegmentationData(prefix)

# generate locations for segments that are too small
node_generation.GenerateNodes(prefix, segmentation, subset)

# run inference for node network
node_model_prefix = 'architectures/nodes-400nm-3x20x60x60-Kasthuri/nodes' #json where hyperparanms live
nodes.forward.Forward(prefix, node_model_prefix, segmentation, subset, evaluate=True)

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
edge_model_prefix = 'architectures/edges-600nm-3x18x52x52-Kasthuri/edges' #json where hyperparams live
edges.forward.Forward(prefix, edge_model_prefix, subset)

# run lifted multicut
lifted_multicut.LiftedMulticut(prefix, segmentation, edge_model_prefix)
