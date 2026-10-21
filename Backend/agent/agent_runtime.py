"""
Adaptive Context Intelligence Engine (ACIE)

Agent Runtime

Controls complete autonomous agent lifecycle
"""


from Backend.agent.task_manager import TaskManager
from Backend.agent.state_manager import StateManager
from Backend.agent.execution_engine import ExecutionEngine
from Backend.agent.tool_router import ToolRouter
from Backend.data_structures.queue import Queue


from Backend.pipeline.memory_pipeline import MemoryPipeline
from Backend.pipeline.retrieval_pipeline import RetrievalPipeline


from Backend.llm.llm_client import LLMClient


from Backend.agent.response_generator import ResponseGenerator



class AgentRuntime:


    def __init__(

        self,

        task_manager=None,

        state_manager=None,

        execution_engine=None,

        tool_router=None,

        memory_pipeline=None,

        retrieval_pipeline=None

    ):



        self.task_manager = (
            task_manager
            or TaskManager()
        )


        self.state_manager = (
            state_manager
            or StateManager()
        )



        self.tool_router = (
            tool_router
            or ToolRouter()
        )



        self.memory_pipeline = (
            memory_pipeline
            or MemoryPipeline()
        )



        self.retrieval_pipeline = (
            retrieval_pipeline
            or RetrievalPipeline()
        )



        # -------------------------------
        # AI Layer
        # -------------------------------


        self.llm_client = LLMClient(

            model="gemini"

        )



        self.response_generator = ResponseGenerator(

            llm_client=self.llm_client

        )

        # DSA Queue
        self.task_queue = Queue()



        self.execution_engine = (

            execution_engine

            or

            ExecutionEngine(

                task_manager=self.task_manager,

                state_manager=self.state_manager,

                tool_router=self.tool_router,

                llm_client=self.llm_client,

                response_generator=self.response_generator

            )

        )



    # ==================================================
    # Initialize Agent
    # ==================================================


    def initialize(self,query):


        print(
            "\n========== INITIALIZING ACIE AGENT ==========\n"
        )


        self.state_manager.start()


        self.state_manager.set_goal(query)

        # Clear previous queue
        self.task_queue = Queue()

        # Clear old tasks

        clear_tasks = getattr(self.task_manager, "clear_tasks", None)
        if callable(clear_tasks):
            clear_tasks()
        else:
            clear_method = getattr(self.task_manager, "clear", None)
            if callable(clear_method):
                clear_method()


        # Agent Plan


        task = "Collect Context"

        self.task_manager.add_task(task)

        self.task_queue.enqueue(task)


        task = "Retrieve Memories"

        self.task_manager.add_task(task)

        self.task_queue.enqueue(task)



        task = "Reason"

        self.task_manager.add_task(task)

        self.task_queue.enqueue(task)


        task = "Generate Response"

        self.task_manager.add_task(task)

        self.task_queue.enqueue(task)



    # ==================================================
    # Run Agent
    # ==================================================


    def run(

        self,

        query,

        conversation=None,

        documents=None

    ):



        conversation = conversation or []

        documents = documents or []



        try:



            self.initialize(query)



            print(
                "\n========== MEMORY PROCESS ==========\n"
            )



            memory_result = (

                self.memory_pipeline.process(

                    query=query,

                    conversation=conversation,

                    documents=documents

                )

            )




            print(
                "\n========== RETRIEVAL PROCESS ==========\n"
            )



            retrieval_result = (

                self.retrieval_pipeline.retrieve(

                    query=query,

                    memories=

                    memory_result[
                        "consolidated_memories"
                    ],

                    token_budget=500

                )

            )




            print(
                "\n========== AGENT EXECUTION ==========\n"
            )



            execution_context = {
                "query": query,
                "memory": memory_result,
                "retrieval": retrieval_result,
                "reasoning": {}
            }

            execution_result = self.execution_engine.run(
                execution_context
            )




            print(
                "\n========== RESPONSE GENERATION ==========\n"
            )



            final_response = (

                self.response_generator.generate(

                    query=query,

                    memory_result=memory_result,

                    retrieval_result=retrieval_result,

                    conversation=conversation,

                )

            )



            self.state_manager.stop()

            task_execution_order = self.task_queue.display()



            return {



                "status":

                "SUCCESS",



                "query":

                query,



                "answer":

                final_response["answer"],



                "metadata":

                final_response["metadata"],





                "execution":
                execution_result,

                "task_execution_order": task_execution_order,

            }





        except Exception as e:



            self.state_manager.stop()



            return {


                "status":

                "ERROR",



                "query":

                query,



                "error":

                str(e)

            }





if __name__=="__main__":



    agent = AgentRuntime()



    response = agent.run(

        "Explain Artificial Intelligence"

    )


    print("\n========== FINAL OUTPUT ==========\n")


    print(response)
