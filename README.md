# DISTRIBUTED COMPUTE CLUSTER
*Distributed Software Systems Course Project - 2025-2026 - ISI LM, DISI, UNIBO*

## VISION:
The goal of this project is to design and implement a fault-tolerant distributed compute cluster, capable of executing computational workloads across multiple nodes in a coordinated, scalable and resilient manner. This system is conceived as a decentralized distributed system in which multiple coordinator nodes collaborate to manage the cluster state, schedule tasks, and recover from failures. The system is designed to remain operational even in the presence of node failures, network issues, or partial system outages.
The system allows users to submit computational jobs, which are automatically decomposed into smaller tasks and distributed across a set of worker nodes. Each worker executes tasks independently, while a group of coordinator nodes collaboratively manages task assignment, monitors execution progress, and ensures that the overall job is completed correctly.
The system is designed to operate relying on multiple coordinator nodes, that maintain internally a shared view of the system state and dynamically elect a leader responsible for scheduling decisions and replicating the cluster state among coordinators. If the leader fails, another coordinator seamlessly takes over, ensuring continuity of operation without manual intervention. Workers interact with the system using a pull-based model: they actively request tasks when available, enabling natural load balancing and scalability. The system continuously monitors node health through heartbeat mechanisms, allowing it to detect failures and automatically reassign unfinished tasks to other available workers.
The system supports structured job execution in the form of task graphs (Directed Acyclic Graphs), where tasks may depend on the results of others. This enables the execution of more complex workloads while ensuring correct ordering and synchronization.

## LEARNING GOALS:
- **Distributed Coordination**: design of a distributed system with multiple coordinators.
- **Distributed Consensus**: understanding of coordination challenges in distributed systems, including leader election in the presence of failures.
- **Fault Tolerance and Failure Models**: development of mechanisms to detect node failures and recover from them through task reassignment and persistent state management, considering different types of failures (e.g., crash failures, network partitions).
- **Distributed Scheduling**: implementation of a decentralized, pull-based scheduling model, in which worker nodes actively request tasks.
- **State Replication**: design of techniques for managing shared system state across multiple nodes, including replication strategies.
- **CAP Theorem**: conceptual exploration of the CAP theorem trade-offs.
- **Workflow Execution**: support for job execution as a set of interdependent tasks (DAG-based execution), ensuring correct ordering and synchronization.
- **Scalability**: design of the system to support dynamic addition and removal of worker nodes without requiring manual reconfiguration.
- **System Observability**: introduction of basic monitoring and metrics collection mechanisms.

## INTENDED TECHNOLOGIES:
- **Programming language**: Python.
- **Networking**: TCP sockets to implement low-level communication between nodes.
- **Concurrency**: asyncio for handling multiple concurrent connections.
- **Communication**: custom RPC protocol implemented over TCP, using JSON-based message serialization.
- **Containerization and deployment**: Docker and Docker Compose to simulate a distributed environment.

## INTENDED DELIVERABLES:
- **Source code**: complete implementation of the distributed compute cluster.
- **Testing suite**: unit and integration tests covering core system components.
- **Containerized deployment**: Docker-based multi-node setup for running the system in a simulate distributed environments, to easily start multiple coordinator and worker nodes.
- **Demonstration environment**: instructions to reproduce key system scenarios (normal execution, failures, scaling and network instability).
- **Final report**.

## USAGE SCENARIOS:
- **Normal Execution Scenario**: a user submits a job composed of multiple tasks. The system distributes the tasks across available worker nodes, executes them successfully and returns the results to the user.
- **Worker Failure Scenario**: if a worker node fails during task execution, the system detects the failure via heartbeat timeout. The affected tasks are automatically reassigned to other workers and completed without loss of progress.
- **Coordinator Failure Scenario**: when the active coordinator node becomes unavailable, a new leader is elected from the remaining coordinators. The system continues operating seamlessly, preserving the state of ongoing jobs.
- **Scaling Scenario**: additional worker nodes can be dynamically added to the cluster. The system automatically leverages the new resources to improve performance and increase throughput.
- **Workflow Execution Scenario**: when a job with task dependencies is submitted, the system executes that tasks according to its dependency order, ensuring correct synchronization and workflow completion.
- **Network Instability Scenario**: in the presence of network delays or partial failures, the system continues to operate under degraded conditions, maintaining overall functionality.

## WORKING PLAN:
The plan is to approach it incrementally, starting from a core system and then extending it if possible.
As a core implementation, I plan to include:
- multiple coordinators with leader election,
- basic state replication among coordinators,
- pull-based task distribution to workers,
- failure detection and task reassignment.

To keep the scope manageable, I will start with the simplest possible implementation and refine it progressively over time. The computational tasks will also be simplified (e.g., simulated workloads such as sleep, print, or basic operations), allowing me to focus on the distributed system aspects rather than heavy computation.
As an optional extension, if time allows, I would like to explore DAG-based task execution to support dependencies between tasks.

## GROUP MEMBERS:
Marco Paggetti - [marco.paggetti@studio.unibo.it] (Individual project)
