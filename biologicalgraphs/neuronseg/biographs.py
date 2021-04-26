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
import numpy as np
from intern.remote.boss import BossRemote

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


def correct_splits(args):
    if args.config:
        rmt = BossRemote(args.config)
    else:
        cfg = _generate_config(args.token, args)
        with open("intern.cfg", "w") as f:
            cfg.write(f)
        rmt = BossRemote("intern.cfg")

    # Data will be in Z,Y,X format (anisotropic)
    coord_frame = rmt.get_coordinate_frame(rmt.get_experiment(args.coll, args.exp).coord_frame)
    chan = rmt.get_channel(args.chan, args.coll, args.exp)
    if chan.datatype != 'uint64':
        raise TypeError('Please choose an annotation channel for this pipeline.') 
    
    print('Getting boss cutout...')
    cutout = rmt.get_cutout(resource=chan,
                                 resolution=args.res,
                                 x_range=[args.xmin, args.xmax],
                                 y_range=[args.ymin, args.ymax],
                                 z_range=[args.zmin, args.zmax]
    )    
    print('Cutout complete.')

    # map boss cutout for error correction tool
    boss_ids = np.sort(np.unique(cutout))
    mapped_ids = list(range(len(boss_ids)))
    map_dict= dict(zip(boss_ids, mapped_ids))
    inv_map = dict(zip(mapped_ids, boss_ids))
    cutout = np.vectorize(map_dict.get)(cutout)

    # the prefix name corresponds to the meta file in meta/{PREFIX}.meta
    prefix = chan.exp_name

    # subset is either training, validation, or testing
    subset = 'testing'

    # Create metadata file
    print('Creating metadata.. \n')
    meta_data.WriteBossMetaFile(coord_frame, cutout, prefix)
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
    parser.set_defaults(func=correct_splits)

    parser.add_argument("-c", "--config", default=None, help="Boss config file")
    parser.add_argument("-t", "--token", default=None, help="Boss API Token")
    parser.add_argument("--host", required=False, default="api.bossdb.io", help="Name of boss host")
    parser.add_argument("--coll", required=True, help="Collection name")
    parser.add_argument("--exp", required=True, help="Experiment name")
    parser.add_argument("--chan", required=True, help="Channel name")
    parser.add_argument("--res", type=int, default=0, help="Resolution")
    parser.add_argument("--xmin", type=int, default=0, help="Xmin")
    parser.add_argument("--xmax", type=int, default=1, help="Xmax")
    parser.add_argument("--ymin", type=int, default=0, help="Ymin")
    parser.add_argument("--ymax", type=int, default=1, help="Ymax")
    parser.add_argument("--zmin", type=int, default=0, help="Zmin")
    parser.add_argument("--zmax", type=int, default=1, help="Zmax")

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
