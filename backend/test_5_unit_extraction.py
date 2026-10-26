import os
import sys
from pathlib import Path

# Add backend and workspace directory to sys.path
backend_dir = Path(__file__).resolve().parent
workspace_dir = backend_dir.parent
sys.path.insert(0, str(workspace_dir))
sys.path.insert(0, str(backend_dir))

from app.services.ai_service import ai_service

sample_5_unit_planner = """
COURSE LECTURE PLANNER & DETAILED SYLLABUS: OPERATING SYSTEMS
Department of Computer Science & Engineering

UNIT 1: INTRODUCTION TO OPERATING SYSTEMS & SYSTEM STRUCTURES
- Evolution of Operating Systems, Batch, Multi-programmed, Time-sharing, Real-time systems
- System Calls and System Programs, OS Architecture, Monolithic and Microkernel structures
- Process Concept: Process Control Block (PCB), Process States, Context Switching
- Operations on Processes, Inter-process Communication (IPC), Shared Memory and Message Passing

UNIT 2: CPU SCHEDULING & SYNCHRONIZATION
- Scheduling Criteria, Preemptive and Non-Preemptive Scheduling
- FCFS, SJF, Priority Scheduling, Round Robin, Multi-level Queue Scheduling
- The Critical Section Problem, Peterson's Algorithm, Hardware Synchronization primitives
- Semaphores, Classic Problems of Synchronization (Producer-Consumer, Dining Philosophers, Readers-Writers)
- Monitors and Deadlock Characterization, Handling Deadlocks, Banker's Algorithm

UNIT 3: MEMORY MANAGEMENT & VIRTUAL MEMORY
- Memory Allocation Strategies: Contiguous vs Non-Contiguous allocation, Fragmentation
- Paging Architecture: Page Table Structure, Hierarchical Paging, TLB Translation Lookaside Buffer
- Segmentation: Hardware, Architecture, and Protection mechanisms
- Virtual Memory Concepts: Demand Paging, Page Fault Handling routine
- Page Replacement Algorithms: FIFO, Optimal (OPT), Least Recently Used (LRU), Thrashing

UNIT 4: STORAGE MANAGEMENT & FILE SYSTEMS
- File Concept: Attributes, Operations, File Types, Access Methods
- Directory Structure: Single-Level, Two-Level, Tree-Structured, Acyclic Graph
- File System Implementation: Allocation Methods (Contiguous, Linked, Indexed), Free-Space Management
- Mass-Storage Structure: Disk Structure, Disk Attachment, Disk Scheduling (FCFS, SSTF, SCAN, C-SCAN)
- RAID Levels and Redundancy Architecture

UNIT 5: PROTECTION, SECURITY & DISTRIBUTED SYSTEMS
- Goals of Protection, Principles of Protection, Domain of Protection, Access Matrix
- System Threats and Security: Program Threats, System and Network Threats, Cryptography basics
- User Authentication, Passwords, Biometrics, Access Control
- Introduction to Distributed Systems: Distributed File Systems (NFS), Network Operating Systems
- Case Studies: Linux Kernel Architecture, Windows System Internals
"""

print("[TEST] Running analyze_syllabus_hierarchy with 5-Unit lecture planner...")
try:
    result = ai_service.analyze_syllabus_hierarchy(
        syllabus_text=sample_5_unit_planner,
        is_single_chapter=False,
        doc_title="Operating Systems Lecture Planner"
    )
    units = result.get("units", [])
    print(f"[SUCCESS] Extracted {len(units)} units!")
    for u in units:
        print(f" -> Unit {u.get('unit_number')}: {u.get('title')}")
        topics = u.get("topics", [])
        print(f"    Topics count: {len(topics)}")
        for t in topics:
            print(f"      * {t.get('name')}")
            
    unit_numbers = [u.get("unit_number") for u in units]
    assert len(units) >= 3, f"Expected at least 3 units, got {len(units)}"
    print("[ALL TESTS PASSED] Comprehensive multi-unit topic extraction is working correctly!")
except Exception as e:
    print(f"[FAILED] Error: {e}")
    sys.exit(1)
