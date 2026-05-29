from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Generator, AsyncGenerator, Literal
from graph_builder import build_graph
from services.graph.utils import set_graph, init_graph
from langchain_neo4j import Neo4jGraph
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage


@dataclass
class Message:
    role: Literal["USER", "ASSISTANT"]
    content: str    

class PipelineFacade:
    """A facade class to manage and execute the LangGraph pipeline.

    Provides support for configuring the Neo4j connection through credentials,
    and offers methods for direct execution as well as node-by-node streaming.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        graph_instance: Optional[Neo4jGraph] = None,
        evaluate: bool = False,
    ):
        """Initializes the pipeline facade.

        If a custom graph_instance is provided, it is injected directly.
        Otherwise, if URL/credentials are provided, a new Neo4jGraph
        instance is initialized and registered.
        """
        if graph_instance is not None:
            set_graph(graph_instance)
        elif (
            url is not None
            or username is not None
            or password is not None
        ):
            init_graph(url=url, username=username, password=password)

        # Build and compile the langgraph runnable pipeline
        self.graph_runnable = build_graph(evaluate=evaluate)

    def run(
        self,
        context: List[Message],
        expected_nodes: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Executes the pipeline directly and returns the final state."""
        from helper import convert_messages
        converted_context = convert_messages(context)
        
        inputs: Dict[str, Any] = {"context": converted_context}
        
        inputs.update(kwargs)

        return self.graph_runnable.invoke(inputs)

    async def arun(
        self,
        context: List[Message],
        expected_nodes: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Executes the pipeline directly and asynchronously, returning the final state."""
        from helper import convert_messages
        converted_context = convert_messages(context)
        
        inputs: Dict[str, Any] = {"context": converted_context}
        
        inputs.update(kwargs)

        return await self.graph_runnable.ainvoke(inputs)

    def stream_by_node(
        self,
        context: List[Message],
        expected_nodes: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Generator[Dict[str, Any], None, None]:
        """Streams the pipeline execution step-by-step (node-by-node)."""
        from helper import convert_messages
        converted_context = convert_messages(context)
        
        inputs: Dict[str, Any] = {"context": converted_context}
        
        inputs.update(kwargs)

        for chunk in self.graph_runnable.stream(inputs, subgraphs=True, stream_mode="updates", version="v2"):
            yield chunk

    async def astream_by_node(
        self,
        context: List[Message],
        expected_nodes: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Streams the pipeline execution step-by-step (node-by-node) asynchronously."""
        from helper import convert_messages
        converted_context = convert_messages(context)
        
        inputs: Dict[str, Any] = {"context": converted_context}
        
        inputs.update(kwargs)

        async for chunk in self.graph_runnable.astream(inputs, subgraphs=True, stream_mode="updates", version="v2"):
            yield chunk
