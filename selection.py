import sys
import random
import networkx as nx
import dag_generate as dg
from asciinet import graph_to_ascii


num_nodes = int(sys.argv[1])
num_edges = int(sys.argv[2])
attr_card = int(sys.argv[3])
num_nodes_sel = int(sys.argv[4])

# start with a randomly created DAG
dag_source = dg.create_random_dag(num_nodes, num_edges, attr_card)
print "source dag:", graph_to_ascii(dag_source)

# generate data from the DAG
data_recs = dg.sample_dag(dag_source, 10000)

# learn a DAG (should match above)
dag_learn = dg.run_pc(data_recs, data_recs.dtype.names)
print "learned dag:"
print graph_to_ascii(dag_learn)
if not nx.algorithms.isomorphism.is_isomorphic(dag_source, dag_learn):
    print "oh no, learned graph not isomorphic"

# now try hiding some data columns and learning a new dag
nodes_keep = random.sample(dag_source.nodes(), num_nodes_sel)
print "keeping nodes:", nodes_keep
data_keep_arr = zip(*[data_recs[col] for col in nodes_keep])
print data_keep_arr[:10]
dag_keep_learn = dg.run_pc(data_keep_arr, nodes_keep)

print "full dag:"
print graph_to_ascii(dag_learn)

print "select dag:"
print graph_to_ascii(dag_keep_learn)

matcher = nx.algorithms.isomorphism.GraphMatcher(dag_learn, dag_keep_learn)
if not matcher.subgraph_is_isomorphic():
    print "oh no, select graph not subgraph isomorphic"










