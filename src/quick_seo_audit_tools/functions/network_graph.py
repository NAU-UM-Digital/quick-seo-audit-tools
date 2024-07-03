import networkx as nx
import quick_seo_audit_tools.functions.database as db
import matplotlib.pyplot as plt
import gravis as gv


def create_graph():
    return nx.Graph()

def create_graph_from_edge_list(edge_list):
    return nx.DiGraph(edge_list)

def add_graph_edge(G, node1, node2):
    G.add_edge(node1, node2)
    return G

def degree_centrality_analysis(G):
    return nx.degree_centrality(G)

def no_edges_per_node(G):
    return G.in_degree() 

def pagerank_analysis(G):
    return nx.pagerank(G)

def return_gravis_graph(G, output_file=False):
    # Centrality calculation
    centrality = nx.algorithms.degree_centrality(G)

    # Community detection
    communities = nx.algorithms.community.greedy_modularity_communities(G, best_n=5)

    # Assignment of node sizes
    nx.set_node_attributes(G, centrality, 'size')

    # Assignment of node colors
    colors = ['red', 'blue', 'green', 'orange', 'pink']
    for community, color in zip(communities, colors):
        for node in community:
            G.nodes[node]['color'] = color

    fig = gv.d3(G, use_node_size_normalization=True, node_size_normalization_max=30,
      use_edge_size_normalization=True, edge_size_data_source='weight',edge_size_normalization_max=5, edge_curvature=0.3,
      graph_height=800, show_node_label=False,
      show_details=True, show_details_toggle_button=False)
    
    if output_file is not False:
        fig.export_html(output_file)
