"""
Pre-curated, academically accurate DBMS study materials and fixtures for ExamLoop.
"""

DBMS_SAMPLE_TEXT = """# Database Management Systems (DBMS) - Core Examination Notes

## Chapter 1: Relational Normalization and Integrity
Database normalization is the process of structuring a relational database in accordance with a series of normal forms to reduce data redundancy and improve data integrity.

1. First Normal Form (1NF):
   A relation is in 1NF if and only if every attribute domain contains only atomic (indivisible) values, and there are no repeating groups or multivalued attributes. Each column must contain single values, and each record must be unique.

2. Second Normal Form (2NF):
   A relation is in 2NF if it is in 1NF and every non-prime attribute is fully functionally dependent on the entire primary key. There must be no partial dependency where a non-key attribute depends on only a subset of a composite candidate key.

3. Third Normal Form (3NF):
   A relation is in 3NF if it is in 2NF and there is no transitive dependency: no non-prime attribute depends on another non-prime attribute. Formally, for every functional dependency X -> A, either X is a superkey or A is a prime attribute.

4. Boyce-Codd Normal Form (BCNF):
   A stricter version of 3NF. A relation is in BCNF if for every functional dependency X -> A, X is a superkey. BCNF eliminates anomalies that 3NF allows when multiple overlapping candidate keys exist.

Anomalies prevented by normalization:
- Insertion Anomaly: Inability to insert information without adding unrelated dummy records.
- Deletion Anomaly: Unintended loss of crucial auxiliary data when a record is deleted.
- Update Anomaly: Inconsistent data states resulting from partial record modifications.

---

## Chapter 2: SQL Joins and Query Processing
Relational databases leverage relational algebra operations to combine records from two or more tables based on related columns.

1. INNER JOIN:
   Returns rows where there is at least one match in both tables based on the join predicate. Unmatched rows from either table are excluded from the result set.

2. LEFT (OUTER) JOIN:
   Returns all rows from the left table, paired with matched rows from the right table. Where no matching row exists on the right, NULL values are populated for right-table attributes.

3. RIGHT (OUTER) JOIN:
   Returns all records from the right table, plus matched records from the left table, populating left-table attributes with NULL when no match exists.

4. FULL (OUTER) JOIN:
   Combines the result of both LEFT and RIGHT outer joins. Retains all rows from both tables, filling missing counterparts with NULLs.

5. CROSS JOIN (Cartesian Product):
   Produces the Cartesian product of the two relations, returning every combination of rows from the first table with rows from the second table (size = |R1| * |R2|).

---

## Chapter 3: Transaction Management, ACID Properties, and Concurrency Control
A transaction is a logical unit of database processing that includes one or more database operations (read, write, commit, abort).

The ACID Properties:
1. Atomicity:
   The "all-or-nothing" rule. Either all operations of the transaction are successfully executed and permanently recorded, or the database is rolled back to its state prior to transaction initiation. Managed by the DBMS write-ahead logging (WAL) mechanism.

2. Consistency:
   The transaction transforms the database from one valid state to another valid state, satisfying all explicit integrity constraints, foreign keys, cascades, and business rules.

3. Isolation:
   The execution of concurrent transactions must yield the same database state as if they were executed sequentially. Uncommitted changes made by one transaction must not be visible to other concurrently running transactions depending on the configured isolation level.

4. Durability:
   Once a transaction has committed, its updates are permanent and will not be lost, even in the event of an immediate system crash, power failure, or hardware outage. Guaranteed through non-volatile write-ahead log flush.

Transaction Isolation Levels and Anomalies:
- Read Uncommitted: Susceptible to Dirty Reads (reading uncommitted writes of another transaction), Non-Repeatable Reads, and Phantom Reads.
- Read Committed: Guarantees transactions read only committed modifications. Prevents Dirty Reads. Susceptible to Non-Repeatable Reads and Phantom Reads.
- Repeatable Read: Guarantees that any row read during a transaction will return identical values upon re-reading. Prevents Dirty Reads and Non-Repeatable Reads. Susceptible to Phantom Reads (new rows inserted by concurrent transactions).
- Serializable: Highest isolation level. Transactions behave strictly as if executed in a serial schedule. Prevents Dirty Reads, Non-Repeatable Reads, and Phantom Reads using range locks or multi-version concurrency control (MVCC) serialization checks.

Common Misconception Alert:
A common misconception is that "Repeatable Read prevents all concurrency anomalies." In standard SQL-92, Repeatable Read permits Phantom Reads because row-level shared locks do not lock the predicate gap where newly inserted rows may appear.

---

## Chapter 4: Database Storage and Indexing Structures
Indexing is a data structure technique used to quickly locate and access data in a database without scanning every row in a table.

1. B+ Tree Indexes:
   The industry-standard structure for relational indexing. Balanced tree where all leaf nodes reside at the exact same depth and are linked sequentially in a doubly-linked list.
   Internal nodes store search keys and child pointers; leaf nodes store actual record pointers or clustered data rows. Provides O(log N) search, insertion, and deletion complexity, and efficient range scans along the linked leaves.

2. Clustered vs Non-Clustered Indexes:
   - Clustered Index: Determines the physical storage order of rows in the table. Because physical data can only be sorted in one order, a table can possess only ONE clustered index (typically the Primary Key).
   - Non-Clustered (Secondary) Index: A separate auxiliary structure containing index keys and row pointers (such as tuple IDs or clustered key values) that refer back to the physical data rows. A table can have multiple non-clustered indexes.

3. Tradeoffs of Indexing:
   - Benefits: Dramatically reduces query response times, disk I/O, and avoids full table scans (O(N)).
   - Costs: Consumes additional storage space. Every INSERT, UPDATE, and DELETE statement incurs write amplification because index B+ trees must be rebalanced, split, and updated synchronously with data changes.
"""

DBMS_FIXTURE_CONCEPTS = [
    {
        "id": "c_norm",
        "name": "Relational Normalization & Normal Forms",
        "description": "Techniques for eliminating redundancy and modification anomalies through 1NF, 2NF, 3NF, and BCNF functional dependency decomposition.",
        "supporting_pages": [1, 2],
        "keywords": ["1NF", "2NF", "3NF", "BCNF", "normalization", "dependency", "anomaly"]
    },
    {
        "id": "c_joins",
        "name": "SQL Joins and Relational Algebra",
        "description": "Inner, outer (left, right, full), and cross joins, relational predicates, and NULL value semantics in relational query composition.",
        "supporting_pages": [2],
        "keywords": ["join", "inner join", "left join", "cartesian", "null"]
    },
    {
        "id": "c_acid",
        "name": "Transactions, ACID & Concurrency Control",
        "description": "Atomicity, Consistency, Isolation, and Durability, write-ahead logging, isolation levels (Read Committed, Repeatable Read, Serializable), and concurrency anomalies.",
        "supporting_pages": [3],
        "keywords": ["transaction", "acid", "atomicity", "isolation", "repeatable read", "phantom read", "dirty read"]
    },
    {
        "id": "c_index",
        "name": "Database Storage and B+ Tree Indexing",
        "description": "B+ tree structures, clustered vs non-clustered indexes, O(log N) lookup complexity, range scans, and index maintenance write penalties.",
        "supporting_pages": [4],
        "keywords": ["index", "b+ tree", "clustered", "non-clustered", "i/o", "write overhead"]
    }
]

# High-fidelity verified demo questions
DBMS_FIXTURE_QUESTIONS = [
    {
        "id": "q_mcq_1",
        "concept_ids": ["c_norm"],
        "question_type": "mcq",
        "question_text": "A relational table contains a composite primary key (StudentID, CourseID). The attribute 'CourseTitle' depends solely on 'CourseID'. Which normal form does this relation violate?",
        "options": [
            {"id": "A", "text": "First Normal Form (1NF)"},
            {"id": "B", "text": "Second Normal Form (2NF)"},
            {"id": "C", "text": "Third Normal Form (3NF)"},
            {"id": "D", "text": "Boyce-Codd Normal Form (BCNF)"}
        ],
        "correct_option_id": "B",
        "explanation": "Second Normal Form (2NF) requires that every non-prime attribute be fully functionally dependent on the entire candidate key. Since CourseTitle depends only on CourseID (a proper subset of the composite key), it is a partial dependency, violating 2NF.",
        "difficulty_label": "medium",
        "marks": 2,
        "source_page": 1,
        "excerpt": "A relation is in 2NF if it is in 1NF and every non-prime attribute is fully functionally dependent on the entire primary key. There must be no partial dependency..."
    },
    {
        "id": "q_mcq_2",
        "concept_ids": ["c_joins"],
        "question_type": "mcq",
        "question_text": "Table A has 10 rows and Table B has 5 rows. No rows share matching join keys. How many rows are returned by a LEFT OUTER JOIN from Table A to Table B?",
        "options": [
            {"id": "A", "text": "0 rows"},
            {"id": "B", "text": "5 rows"},
            {"id": "C", "text": "10 rows"},
            {"id": "D", "text": "50 rows"}
        ],
        "correct_option_id": "C",
        "explanation": "A LEFT OUTER JOIN preserves all rows from the left table (Table A). Since Table A contains 10 rows and none match Table B, all 10 rows from Table A appear in the result with NULL values for Table B attributes.",
        "difficulty_label": "easy",
        "marks": 2,
        "source_page": 2,
        "excerpt": "LEFT (OUTER) JOIN returns all rows from the left table, paired with matched rows from the right table. Where no matching row exists on the right, NULL values are populated..."
    },
    {
        "id": "q_mcq_3",
        "concept_ids": ["c_acid"],
        "question_type": "mcq",
        "question_text": "Under the SQL standard 'Repeatable Read' isolation level, which of the following concurrency anomalies is still permitted to occur?",
        "options": [
            {"id": "A", "text": "Dirty Read"},
            {"id": "B", "text": "Non-Repeatable Read"},
            {"id": "C", "text": "Phantom Read"},
            {"id": "D", "text": "Loss of Durability"}
        ],
        "correct_option_id": "C",
        "explanation": "Repeatable Read prevents Dirty Reads and Non-Repeatable Reads by locking rows read, but it permits Phantom Reads where a concurrent transaction inserts new qualifying rows that meet the query predicate.",
        "difficulty_label": "hard",
        "marks": 2,
        "source_page": 3,
        "excerpt": "Repeatable Read: Prevents Dirty Reads and Non-Repeatable Reads. Susceptible to Phantom Reads (new rows inserted by concurrent transactions)."
    },
    {
        "id": "q_subj_1",
        "concept_ids": ["c_acid"],
        "question_type": "subjective",
        "question_text": "Explain why the 'Repeatable Read' isolation level does not guarantee complete serializability. Contrast Non-Repeatable Reads with Phantom Reads and describe the mechanism used in Serializable isolation to eliminate phantoms.",
        "max_marks": 5,
        "expected_key_points": [
            "Difference between reading existing rows (Non-Repeatable) vs newly inserted qualifying rows (Phantom)",
            "How row-level locks hold existing records but do not prevent predicate range insertions",
            "Serializable isolation's use of range locking or multi-version serialization to eliminate phantoms"
        ],
        "reference_answer": "Repeatable Read ensures that any existing row retrieved during a transaction will return unchanged values upon re-reading. However, it only locks the specific rows that currently exist and match the query. It does not lock the gaps between records or prevent concurrent transactions from inserting brand new rows that satisfy the filter criteria. When the transaction re-executes the query, these newly inserted records appear like 'phantoms'. In contrast, a Non-Repeatable Read occurs when an existing row's values are modified or deleted by another transaction. Serializable isolation eliminates Phantom Reads by employing index-range locking (gap locks) or MVCC serializability conflict checks, guaranteeing the schedule is equivalent to strict sequential execution.",
        "difficulty_label": "hard",
        "marks": 5,
        "source_page": 3,
        "excerpt": "In standard SQL-92, Repeatable Read permits Phantom Reads because row-level shared locks do not lock the predicate gap where newly inserted rows may appear... Serializable employs range locks.",
        "rubric_criteria": [
            {
                "criterion_id": "crit_distinction",
                "description": "Accurately contrasts Non-Repeatable Read (modification/deletion of existing rows) with Phantom Read (insertion of new matching rows).",
                "max_marks": 2.0
            },
            {
                "criterion_id": "crit_mechanism",
                "description": "Explains why Repeatable Read permits phantoms (locks only existing rows rather than the predicate range).",
                "max_marks": 1.5
            },
            {
                "criterion_id": "crit_serializable",
                "description": "Identifies the Serializable isolation mechanism (range locks, gap locking, or MVCC validation) that prevents phantom insertions.",
                "max_marks": 1.5
            }
        ]
    },
    {
        "id": "q_subj_2",
        "concept_ids": ["c_index"],
        "question_type": "subjective",
        "question_text": "Compare Clustered and Non-Clustered B+ tree indexes. Explain why a table can have only one clustered index, and discuss the primary performance penalty of adding multiple secondary indexes to a write-heavy database.",
        "max_marks": 5,
        "expected_key_points": [
            "Clustered index dictates the physical on-disk ordering of data rows",
            "Physical storage can only be sorted in one order, hence only one clustered index per table",
            "Non-clustered indexes are auxiliary pointer structures",
            "Write overhead / write amplification penalty on INSERT/UPDATE/DELETE due to B+ tree rebalancing"
        ],
        "reference_answer": "A clustered index determines the actual physical storage sequence of rows on disk. Because physical data can only be sorted in a single order, a table can possess only one clustered index. A non-clustered (secondary) index is a separate auxiliary structure whose leaf nodes contain search keys and pointers (such as tuple IDs or clustered key values) referencing the physical data. The primary performance penalty of multiple secondary indexes on write-heavy workloads is write amplification: every INSERT, UPDATE, or DELETE operation must synchronously update and potentially rebalance, split, or merge each secondary B+ tree index structure, causing increased disk I/O and latency.",
        "difficulty_label": "medium",
        "marks": 5,
        "source_page": 4,
        "excerpt": "Clustered Index: Determines the physical storage order of rows... a table can possess only ONE clustered index... Non-Clustered is an auxiliary pointer structure... Every INSERT, UPDATE, and DELETE incurs write amplification because index B+ trees must be rebalanced.",
        "rubric_criteria": [
            {
                "criterion_id": "crit_clustered_def",
                "description": "Explains that a clustered index determines physical storage order and why only one can exist per table.",
                "max_marks": 2.0
            },
            {
                "criterion_id": "crit_non_clustered",
                "description": "Defines non-clustered index as an auxiliary structure with pointers referencing data rows.",
                "max_marks": 1.5
            },
            {
                "criterion_id": "crit_write_penalty",
                "description": "Articulates the write overhead penalty (B+ tree rebalancing/disk I/O on INSERT/UPDATE/DELETE).",
                "max_marks": 1.5
            }
        ]
    }
]

# Three distinct sample student answers for q_subj_1 as specified in prompt:
STUDENT_ANSWERS_DEMO = {
    "correct": (
        "Repeatable Read guarantees that any row that has already been read cannot be modified or deleted by another "
        "concurrent transaction, preventing Dirty Reads and Non-Repeatable Reads. However, it does not prevent Phantom Reads "
        "because it only places shared locks on existing rows that were read, leaving open gaps in the index range. If another "
        "transaction inserts a new record satisfying the query predicate and commits, a subsequent query in the first transaction "
        "will observe these newly created rows. Serializable isolation eliminates this anomaly by enforcing range locks or "
        "predicate locks (preventing insertions into qualifying key gaps) or via serializability conflict validation in MVCC."
    ),
    "partially_correct": (
        "Repeatable Read locks rows so nobody can change them while the transaction is running. This prevents dirty reads "
        "and non-repeatable reads. But if another transaction adds new data, those new rows might show up later as phantom reads. "
        "To fix this, Serializable mode does complete locking across the database so transactions run one after another."
    ),
    "misconception": (
        "Repeatable read means the database will repeat the exact same read every time without any differences, so it already "
        "guarantees complete serializability. A non-repeatable read is the same thing as a phantom read, just different names for "
        "when someone changes your rows. Serializable is just a faster version of repeatable read."
    )
}
