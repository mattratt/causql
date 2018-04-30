import sys
import random
import logging
import numpy as np
import networkx as nx
from pgmpy.models.BayesianModel import BayesianModel
from pgmpy.factors.discrete import TabularCPD
from pgmpy.sampling import BayesianModelSampling
from asciinet import graph_to_ascii
import pcalg
from gsq import ci_tests

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")


# def graph_complete(nodes, undirected=True):
#     if (undirected):
#         g = nx.Graph()
#     else:
#         g = nx.DiGraph()
#     for node in nodes:
#         g.add_node(node)
#     for s in range(0, len(nodes)):
#         for t in range(s+1, len(nodes)):
#             g.add_edge(nodes[s], nodes[t])
#             if not (undirected):
#                 g.add_edge(nodes[t], nodes[s])
#     return g


def get_node_name(n):
    return 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[n]


def create_random_skeleton(node_count, edge_count):
    nodes = [ get_node_name(i) for i in range(node_count) ]
    g = nx.DiGraph()
    g.add_nodes_from(nodes)

    edge_pool = [ (s, t) for s in nodes for t in nodes if (s != t) ]
    random.shuffle(edge_pool)
    while g.number_of_edges() < edge_count:
        s, t = edge_pool.pop(0)
        g.add_edge(s, t)
        if not nx.algorithms.dag.is_directed_acyclic_graph(g):
            logging.debug("rejected edge {} -> {}".format(s, t))
            g.remove_edge(s, t)
        else:
            logging.debug("added edge {} -> {}".format(s, t))
    return g


def create_random_cpds(g, card):
    node_pool = g.nodes()
    node_count = len(node_pool)
    random.shuffle(node_pool)
    cpds = {}
    dones = set()
    while len(dones) < node_count:
        node = node_pool.pop(0)
        parents = set(g.predecessors(node))
        logging.debug("creating cpd for {} (parents: {})".format(node, parents))
        if len(parents) == 0:
            cpds[node] = [ [p] for p in random_distrib(card) ]
            dones.add(node)
        elif parents.issubset(dones):
            # construct a cpd whose size depends on the number of parents and the cardinality
            distribs = [random_distrib(card) for i in range(card ** len(parents))]
            cpds[node] = zip(*distribs)
            dones.add(node)
        else:
            node_pool.append(node)
            continue

        if node in dones:
            logging.debug("cpd for {}: {})".format(node, cpds[node]))

    return cpds


def random_distrib(sz):
    vals = []
    slack = 1.0
    for i in range(sz - 1):
        val = random.uniform(0.0, slack)
        slack -= val
        vals.append(val)
    vals.append(slack)
    random.shuffle(vals)
    return vals


# >>> student = BayesianModel([('diff', 'grade'), ('intel', 'grade')])
# >>> cpd_d = TabularCPD('diff', 2, [[0.6], [0.4]])
# >>> cpd_i = TabularCPD('intel', 2, [[0.7], [0.3]])
# >>> cpd_g = TabularCPD('grade', 3, [[0.3, 0.05, 0.9, 0.5], [0.4, 0.25,
# ...                0.08, 0.3], [0.3, 0.7, 0.02, 0.2]],
# ...                ['intel', 'diff'], [2, 2])
# >>> student.add_cpds(cpd_d, cpd_i, cpd_g)
# >>> inference = BayesianModelSampling(student)
# >>> inference.forward_sample(size=2, return_type='recarray')
# rec.array([(0, 0, 1), (1, 0, 2)], dtype=
#           [('diff', '<i8'), ('intel', '<i8'), ('grade', '<i8')])
def create_random_dag(node_count, edge_count, card):
    logging.debug("creating skeleton")
    dag = create_random_skeleton(node_count, edge_count)
    logging.debug("creating cpds")
    cpds = create_random_cpds(dag, card)
    for node, cpd in cpds.items():
        dag.node[node]['cpd'] = cpd
    return dag


def sample_dag(dag, num):

    #zzz this loses disconnected nodes!!!
    # bayesmod = BayesianModel(dag.edges())
    # bayesmod = BayesianModel(dag)
    bayesmod = BayesianModel()
    bayesmod.add_nodes_from(dag.nodes())
    bayesmod.add_edges_from(dag.edges())

    tab_cpds = []
    cards = { node: len(dag.node[node]['cpd']) for node in dag.nodes() }
    for node in dag.nodes():
        parents = dag.predecessors(node)
        cpd = dag.node[node]['cpd']
        if parents:
            parent_cards = [ cards[par] for par in parents ]
            logging.debug("TablularCPD({}, {}, {}, {}, {})".format(node, cards[node], cpd,
                                                                   parents, parent_cards))
            tab_cpds.append(TabularCPD(node, cards[node], cpd, parents, parent_cards))
        else:
            logging.debug("TablularCPD({}, {}, {})".format(node, cards[node], cpd))
            tab_cpds.append(TabularCPD(node, cards[node], cpd))


    logging.debug("cpds add: {}".format(tab_cpds))

    print "model variables:", bayesmod.nodes()
    for tab_cpd in tab_cpds:
        print "cpd variables:", tab_cpd.variables

    bayesmod.add_cpds(*tab_cpds)

    logging.debug("cpds get: {}".format(bayesmod.get_cpds()))
    inference = BayesianModelSampling(bayesmod)

    logging.debug("generating data")
    recs = inference.forward_sample(size=num, return_type='recarray')
    return recs


def run_pc(data_orig, col_names=None):
    data = np.array([ list(r) for r in data_orig ])
    (skel_graph, sep_set) = pcalg.estimate_skeleton(indep_test_func=ci_tests.ci_test_dis,
                                     data_matrix=data,
                                     alpha=0.01)
    # gdir = nx.DiGraph()
    # gdir.add_nodes_from(g.nodes())
    # gdir.add_edges_from(g.edges())
    dag = pcalg.estimate_cpdag(skel_graph, sep_set)
    if col_names:
        name_map = { i: col_names[i] for i in range(len(dag.nodes())) }
        nx.relabel.relabel_nodes(dag, name_map, copy=False)
    return dag


#####################################

if __name__ == '__main__':

    num_nodes = int(sys.argv[1])
    num_edges = int(sys.argv[2])
    attr_card = int(sys.argv[3])

    dag = create_random_dag(num_nodes, num_edges, attr_card)
    print graph_to_ascii(dag)

    recs = sample_dag(dag, 10000)
    print dag.nodes()
    print recs[:10]
    for node in dag.nodes():
        print "col", node, recs[node][:10]

    gdir = run_pc(recs)
    print graph_to_ascii(gdir)
    print "graphs are isomorphic: ", nx.algorithms.isomorphism.is_isomorphic(dag, gdir)












