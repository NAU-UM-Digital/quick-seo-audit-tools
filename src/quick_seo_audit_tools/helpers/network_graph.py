import networkx as nx
from . import database as db
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

def assign_in_links(graph):
    for node_id in graph.nodes:
        node = graph.nodes[node_id]
        in_links = [f'<li>{u}</li>' for u, v in graph.in_edges(node_id)]
        out_links = [f'<li>{v}</li>' for u, v in graph.out_edges(node_id)]
        node['label'] = f"<p><strong>In links ({len(in_links)}):</strong></p><ul>{''.join(in_links)}</ul><p><strong>Out links ({len(out_links)}):</strong></p><ul>{''.join(out_links)}</ul>"
    return graph

def assign_red_few_inlinks(graph):
    for node_id in graph.nodes:
        node = graph.nodes[node_id]
        if len(graph.in_edges(node_id)) < 2:
            node['color'] = 'red'
    return graph

def assign_green_good_inlinks(graph):
    for node_id in graph.nodes:
        node = graph.nodes[node_id]
        if len(graph.in_edges(node_id)) >= 2:
            node['color'] = 'green'
    return graph

def assign_blue_many_inlinks(graph):
    for node_id in graph.nodes:
        node = graph.nodes[node_id]
        if len(graph.in_edges(node_id)) >= 10:
            node['color'] = 'blue'
    return graph

def assign_hover_node_id(graph):
    for node_id in graph.nodes:
        node = graph.nodes[node_id]
        node['hover'] = str(node_id)
    return graph
   

def return_gravis_graph(G, output_file=False):
    # Centrality calculation
    centrality = nx.algorithms.pagerank(G)

    # Community detection
    communities = nx.algorithms.community.greedy_modularity_communities(G, best_n=5)

    # Assignment of node sizes
    nx.set_node_attributes(G, centrality, 'size')

    # Assignment of node colors
    colors = ['purple', 'blue', 'green', 'orange', 'pink']
    for community, color in zip(communities, colors):
        for node in community:
            G.nodes[node]['color'] = color

    G = assign_in_links(G)
    G = assign_red_few_inlinks(G)
    G = assign_green_good_inlinks(G)
    G = assign_blue_many_inlinks(G)
    G = assign_hover_node_id(G)
    G.graph['node_click'] = (
        '$label'
    )

    fig = gv.d3(G, use_node_size_normalization=True, node_size_normalization_max=30,
      use_edge_size_normalization=True, edge_size_data_source='weight',edge_size_normalization_max=5, edge_curvature=0.3,
      graph_height=800, show_node_label=False,
      show_details=True, show_details_toggle_button=False)
    
    if output_file is not False:
        fig.export_html(output_file)
