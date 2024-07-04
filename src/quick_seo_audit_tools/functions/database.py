from typing import List
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy import select
import quick_seo_audit_tools.functions.network_graph as network_graph
import sqlite3
import argparse

class  Base(DeclarativeBase):
    pass

class Link(Base):
    __tablename__ = "all_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_url: Mapped[str]
    linked_url: Mapped[str]
    link_text: Mapped[str]

    def __repr__(self) -> str:
        return f"Link(id={self.id!r}, source_url={self.source_url!r}, linked_url={self.linked_url!r})"

class Request(Base):
    __tablename__ = "all_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_url: Mapped[str]
    resolved_url: Mapped[str]
    status_code: Mapped[Optional[int]]
    initial_status_code: Mapped[Optional[int]]
    no_of_redirects: Mapped[Optional[int]]
    content_type_header: Mapped[Optional[str]]

    def __repr__(self) -> str:
        return f"Request(id={self.id!r}, request_url={self.request_url!r}, resolved_url={self.resolved_url!r})"

class NetworkCentrality(Base):
    __tablename__ = "network_centrality"

    id: Mapped[int] = mapped_column(primary_key=True)
    resolved_url: Mapped[str]
    network_value: Mapped[int]

    def __repr__(self) -> str:
        return f"NetworkCentrality(id={self.id!r}, resolved_url={self.resolved_url!r}, network_value={self.network_value!r})" 

class NodeInDegree(Base):
    __tablename__ = "node_in_degree"

    id: Mapped[int] = mapped_column(primary_key=True)
    resolved_url: Mapped[str]
    network_value: Mapped[int]

    def __repr__(self) -> str:
        return f"NodeInDegree(id={self.id!r}, resolved_url={self.resolved_url!r}, network_value={self.network_value!r})" 


class PageRank(Base):
    __tablename__ = "page_rank"

    id: Mapped[int] = mapped_column(primary_key=True)
    resolved_url: Mapped[str]
    network_value: Mapped[int]

    def __repr__(self) -> str:
        return f"PageRank(id={self.id!r}, resolved_url={self.resolved_url!r}, network_value={self.network_value!r})" 

def init_output_db(path):
    global engine
    global Base

    output_db_path = f'/{path}'
    engine = create_engine(f"sqlite://{output_db_path}", echo=False)
    Base.metadata.create_all(engine)

def create_db_session():
    engine = create_engine("sqlite://", echo=True)
    return Session(engine)

def add_link_to_db(source_url, linked_url, link_text):
    with Session(engine) as session:
        new_link = Link(
            source_url=source_url,
            linked_url=linked_url,
            link_text=link_text
        )
        session.add_all([new_link])
        session.commit()

def add_request_to_db(request_url, resolved_url, status_code, initial_status_code, no_of_redirects, content_type_header):
    with Session(engine) as session:
        new_request = Request(
            request_url = request_url,
            resolved_url = resolved_url,
            status_code = status_code,
            initial_status_code = initial_status_code,
            no_of_redirects = no_of_redirects,
            content_type_header = content_type_header
        )
        session.add_all([new_request])
        session.commit()

def add_network_analysis_values(Db, url, value):
    with Session(engine) as session:
        new_value = Db(
            resolved_url = url,
            network_value = value
        )
        session.add_all([new_value])
        session.commit()

def list_all_links():
    with Session(engine) as session:
        stmt = select(Link)
        for test in session.scalars(stmt):
            print(test.linked_url)

def list_all_requests():
    with Session(engine) as session:
        stmt = select(Request)
        for test in session.scalars(stmt):
            print(test)

def list_link_data_join():
    with Session(engine) as session:
        stmt = (
            select(Link, Request)
            .join_from(Link, Request, Link.linked_url == Request.request_url)
        )
        print(stmt)

        data_join = [{
            'source URL': row.Link.source_url,
            'on-page linked URL': row.Link.linked_url,
            'destination URL': row.Request.resolved_url,
            'on-page link text': row.Link.link_text,
            'final status code': row.Request.status_code,
            'first status code': row.Request.initial_status_code,
            'number of redirects': row.Request.no_of_redirects
        } for row in session.execute(stmt)]
        return data_join

def list_network_analysis_values():
    with Session(engine) as session:
        stmt = (
            select(NetworkCentrality, PageRank, NodeInDegree)
            .join_from(NetworkCentrality, PageRank, NetworkCentrality.resolved_url == PageRank.resolved_url)
            .join_from(NetworkCentrality, NodeInDegree, NetworkCentrality.resolved_url == NodeInDegree.resolved_url)
        )
        print(stmt)
        data_join = [{
            'url': row.NetworkCentrality.resolved_url,
            'pages linking to URL': row.NodeInDegree.network_value,
            'centrality in network': row.NetworkCentrality.network_value,
            'pagerank in network': row.PageRank.network_value,
        } for row in session.execute(stmt)]
        return data_join

def create_link_graph(output_file=False):
    with Session(engine) as session:
        stmt = (
            select(Link, Request)
            .join_from(Link, Request, Link.linked_url == Request.request_url)
        )
        edges = [(row.Link.source_url, row.Request.resolved_url) for row in session.execute(stmt)]
        H = network_graph.create_graph_from_edge_list(edges)
        print(network_graph.degree_centrality_analysis(H))
        for key, value in network_graph.pagerank_analysis(H).items():
            print(f'{key}: pagerank of {value}')
            add_network_analysis_values(PageRank, key, value) 
        for key, value in network_graph.degree_centrality_analysis(H).items():
            print(f'{key}: centrality of {value}')
            add_network_analysis_values(NetworkCentrality, key, value)
        for tuple in network_graph.no_edges_per_node(H):
            add_network_analysis_values(NodeInDegree, tuple[0], tuple[1])
        network_graph.return_gravis_graph(H, output_file=output_file)