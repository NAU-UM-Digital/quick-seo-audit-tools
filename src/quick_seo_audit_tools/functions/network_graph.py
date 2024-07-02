import networkx as nx
import quick_seo_audit_tools.functions.database as db
import matplotlib.pyplot as plt


def create_graph():
    return nx.Graph()

def create_graph_from_edge_list(edge_list):
    return nx.DiGraph(edge_list)

def add_graph_edge(Graph, node1, node2):
    Graph.add_edge(node1, node2)
    return Graph

def degree_centrality_analysis(Graph):
    return nx.degree_centrality(Graph)