from biologicalgraphs.utilities import dataIO
from biologicalgraphs.graphs.biological import node_generation, edge_generation
from biologicalgraphs.evaluation import comparestacks
from biologicalgraphs.cnns.biological import edges, nodes
from biologicalgraphs.transforms import seg2seg, seg2gold
from biologicalgraphs.skeletonization import generate_skeletons
from biologicalgraphs.algorithms import lifted_multicut
from biologicalgraphs.data_structures import meta_data
import argparse
import configparser
import os
import h5py
import numpy as np
from intern.remote.boss import BossRemote
from intern import array

def _generate_config(token, args):
    boss_host = os.getenv("BOSSDB_HOST", args.host)
    print(boss_host)

    cfg = configparser.ConfigParser()
    cfg["Project Service"] = {}
    cfg["Metadata Service"] = {}
    cfg["Volume Service"] = {}

    project = cfg["Project Service"]
    project["protocol"] = "https"
    project["host"] = boss_host
    project["token"] = token

    metadata = cfg["Metadata Service"]
    metadata["protocol"] = "https"
    metadata["host"] = boss_host
    metadata["token"] = token

    volume = cfg["Volume Service"]
    volume["protocol"] = "https"
    volume["host"] = boss_host
    volume["token"] = token

    return cfg


def boss_cutout(args):
    if args.config:
        rmt = BossRemote(args.config)
    else:
        cfg = _generate_config(args.token, args)
        with open("intern.cfg", "w") as f:
            cfg.write(f)
        rmt = BossRemote("intern.cfg")

    # Data will be in Z,Y,X format (anisotropic)
    boss_data = array(f"bossdb://{args.coll}/{args.exp}/{args.chan}")
    if boss_data.dtype != 'uint64':
        raise TypeError('Please choose an annotation channel for this pipeline.')
    print('Getting boss cutout...')
    cutout = boss_data[args.zmin:args.zmax, args.ymin:args.ymax, args.xmin:args.xmax]
    print('Cutout complete.')

# the prefix name corresponds to the meta file in meta/{PREFIX}.meta
prefix = 'Pinky-test'

# subset is either training, validation, or testing
subset = 'testing'

# Create metadata file
print('Creating metadata.. \n')
meta_data.WriteBossMetaFile(boss_data, cutout, prefix)
print('Metadata created. \n')

# Convert boss data to h5 for pipeline
print('Converting to h5... \n')
dataIO.WriteBossH5File(cutout, prefix)
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

def main():
    parser = argparse.ArgumentParser(description="Error correction tool")
    parent_parser = argparse.ArgumentParser(add_help=False)
    subparsers = parser.add_subparsers(title="commands")

    parser.set_defaults(func=lambda _: parser.print_help())

    group = parent_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-c", "--config", default=None, help="Boss config file")
    group.add_argument("-t", "--token", default=None, help="Boss API Token")

    parent_parser.add_argument("--host", required=False, default="api.bossdb.io", help="Name of boss host")
    parent_parser.add_argument("--coll", required=True, help="Collection name")
    parent_parser.add_argument("--exp", required=True, help="Experiment name")
    parent_parser.add_argument("--chan", required=True, help="Channel name")
    parent_parser.add_argument("--res", type=int, default=0, help="Resolution")
    parent_parser.add_argument("--xmin", type=int, default=0, help="Xmin")
    parent_parser.add_argument("--xmax", type=int, default=1, help="Xmax")
    parent_parser.add_argument("--ymin", type=int, default=0, help="Ymin")
    parent_parser.add_argument("--ymax", type=int, default=1, help="Ymax")
    parent_parser.add_argument("--zmin", type=int, default=0, help="Zmin")
    parent_parser.add_argument("--zmax", type=int, default=1, help="Zmax")

    pull_parser = subparsers.add_parser("pull", help="Pull images from boss", parents=[parent_parser])
    pull_parser.set_defaults(func=boss_cutout)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
