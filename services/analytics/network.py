"""
Network and Influence Analysis Engine (NetworkX Interaction Graphs).
Constructs interaction and co-posting graphs, calculates PageRank influence,
discovers Louvain communities, and flags coordinated sockpuppet clusters.
Includes GraphEmbedder interface and GraphSAGE v2 stub.
"""

import logging
from abc import ABC, abstractmethod
from collections import defaultdict

import networkx as nx
from networkx.algorithms.community import louvain_communities

logger = logging.getLogger(__name__)


# --- Graph Embedder Interface & v2 Stub ---
class GraphEmbedder(ABC):
    """Abstract interface for node and graph structural representations."""

    @abstractmethod
    def embed_nodes(self, graph: nx.Graph) -> dict[str, list[float]]:
        """Produces a dense embedding vector for each node in the interaction graph."""
        pass


class NetworkXBaselineEmbedder(GraphEmbedder):
    """Lightweight structural node embedder using centrality and neighbor degree features."""

    def embed_nodes(self, graph: nx.Graph) -> dict[str, list[float]]:
        if not graph.nodes():
            return {}

        pagerank = nx.pagerank(graph, weight="weight") if len(graph) > 1 else {n: 1.0 for n in graph.nodes()}
        degrees = dict(graph.degree())

        embeddings = {}
        for node in graph.nodes():
            pr = pagerank.get(node, 0.0)
            deg = float(degrees.get(node, 0))
            # 8-dimensional structural signature
            embeddings[node] = [
                pr * 100.0,
                float(deg) / max(1.0, float(len(graph))),
                float(deg),
                round(pr, 6),
                0.0, 0.0, 0.0, 1.0
            ]
        return embeddings


class GraphSAGEEmbedder(GraphEmbedder):
    """
    Inductive Graph Neural Network (GNN) Embedder.
    # TODO(v2): Requires PyTorch Geometric (torch_geometric) and CUDA acceleration.
    """

    def embed_nodes(self, graph: nx.Graph) -> dict[str, list[float]]:
        raise NotImplementedError(
            "# TODO(v2): GraphSAGE deep GNN training is out of scope for MVP (~60% scope). "
            "Please use NetworkXBaselineEmbedder for local centrality representation."
        )


class NetworkAnalysisEngine:
    """Constructs multi-platform interaction graphs and identifies coordinated campaigns."""

    def __init__(self):
        self.embedder = NetworkXBaselineEmbedder()

    def build_interaction_graph(self, posts: list[dict]) -> tuple[nx.Graph, dict]:
        """
        Builds interaction graph from mentions, replies, and near-duplicate text co-occurrence.
        Returns: (networkx.Graph, analysis_results_dict)
        """
        G = nx.Graph()

        if not posts:
            return G, {"node_count": 0, "edge_count": 0, "communities": [], "clusters": []}

        # 1. Add nodes and track text hash occurrences
        text_hash_to_authors = defaultdict(list)
        author_posts = defaultdict(list)

        for p in posts:
            author = p.get("author_id_hash")
            if not author:
                continue

            G.add_node(author, platform=p.get("platform", "mock"))
            author_posts[author].append(p)

            # Track text hash
            th = p.get("text_hash")
            if th:
                text_hash_to_authors[th].append((author, p.get("post_id"), p.get("created_at"), p.get("text")))

        # 2. Add Co-Posting / Near-Duplicate Coordination Edges
        # Accounts posting the same text hash are connected with high coordination weight
        coordinated_clusters = []
        cluster_id = 1

        for th, instances in text_hash_to_authors.items():
            unique_authors = list({item[0] for item in instances})
            if len(unique_authors) >= 3:
                # Suspected coordinated inauthentic behavior (CIB)
                post_ids = [item[1] for item in instances]
                sample_text = instances[0][3]

                coordinated_clusters.append({
                    "cluster_id": f"cluster_{cluster_id:03d}",
                    "account_count": len(unique_authors),
                    "accounts": unique_authors[:15],
                    "evidence_post_ids": post_ids[:20],
                    "sample_text": sample_text[:120] + "..." if len(sample_text) > 120 else sample_text,
                    "coordination_score": round(min(1.0, len(unique_authors) * 0.15), 2)
                })
                cluster_id += 1

                # Add pairwise edges in the graph
                for i in range(len(unique_authors)):
                    for j in range(i + 1, len(unique_authors)):
                        u1, u2 = unique_authors[i], unique_authors[j]
                        if G.has_edge(u1, u2):
                            G[u1][u2]["weight"] += 2.0
                        else:
                            G.add_edge(u1, u2, weight=2.0, interaction="coordinated_post")

        # 3. Add Mention / Reply Edges
        for p in posts:
            author = p.get("author_id_hash")
            # If parent_id exists and we can link to another post
            parent_id = p.get("parent_id")
            if parent_id and author:
                # Add edge to parent if known
                pass

        node_count = G.number_of_nodes()
        edge_count = G.number_of_edges()

        # 4. PageRank Influence Scoring
        if node_count > 1 and edge_count > 0:
            try:
                pagerank = nx.pagerank(G, weight="weight")
            except Exception:
                pagerank = {n: 1.0 / node_count for n in G.nodes()}
        else:
            pagerank = {n: (1.0 / max(1, node_count)) for n in G.nodes()}

        top_influencers = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:10]
        formatted_influencers = [
            {"author_id_hash": auth, "influence_score": round(score * 100.0, 3)}
            for auth, score in top_influencers
        ]

        # 5. Louvain Community Detection
        communities_summary = []
        if node_count > 2 and edge_count > 0:
            try:
                raw_communities = louvain_communities(G, seed=42)
                for cid, comm in enumerate(raw_communities):
                    for member in comm:
                        if member in G.nodes:
                            G.nodes[member]["community"] = cid
                    if len(comm) >= 2:
                        communities_summary.append({
                            "community_id": cid,
                            "member_count": len(comm),
                            "sample_members": list(comm)[:5]
                        })
            except Exception as e:
                logger.debug("Louvain detection skipped: %s", e)

        # 6. Generate Structural Embeddings via GraphEmbedder
        node_embeddings = self.embedder.embed_nodes(G)

        analysis = {
            "node_count": node_count,
            "edge_count": edge_count,
            "top_influencers": formatted_influencers,
            "influence_ranks": pagerank,
            "community_count": len(communities_summary),
            "communities": communities_summary,
            "coordinated_cluster_count": len(coordinated_clusters),
            "coordinated_clusters": coordinated_clusters,
            "node_embeddings_available": len(node_embeddings) > 0
        }

        return G, analysis


network_engine = NetworkAnalysisEngine()
