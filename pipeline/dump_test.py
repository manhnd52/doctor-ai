from pyvis.network import Network

net = Network(height="800px", width="100%")

net.add_node(
    "Gene",
    label="Gene",
    title="""
    geneId: string
    symbol: string
    chromosome: string
    """
)

net.add_node(
    "Disease",
    label="Disease",
    title="""
    diseaseId: string
    name: string
    """
)

net.add_edge(
    "Gene",
    "Disease",
    label="ASSOCIATED_WITH"
)

net.show("schema.html")