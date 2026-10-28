# Database Systems Lab 2: ERD-to-Relational Converter & Relational Algebra Executor

A two-part Python tool for Database Systems:

- **Part 1:** Converts an Entity-Relationship Diagram (ERD) defined in JSON into a visual Relational Schema diagram (`.png`) using the 7-step ER-to-Relational mapping rules and Graphviz.
- **Part 2:** Parses and executes Relational Algebra queries (`SELECT`, `PROJECT`, `JOIN`, `UNION`, `INTERSECT`, `DIFFERENCE`, `AGGREGATE`) on JSON datasets from scratch without external data manipulation libraries.

---

## Project Structure

```text
.
├── main.py
├── requirements.txt
├── part1/
│   ├── models.py          # Pydantic models for ERD and Relational Schema
│   ├── converter.py       # 7-step ER-to-Relational transformation engine
│   ├── renderer.py        # Orthogonal Graphviz schema diagram renderer
│   ├── input/             # Sample ERD JSON inputs
│   └── output/            # Generated PNG relational schema diagrams
└── part2/
    ├── models.py          # Relation, Database, and AST QueryNode models
    ├── parser.py          # Recursive-descent Relational Algebra query parser
    ├── condition.py       # Boolean & comparison expression evaluator
    ├── executor.py        # Relational Algebra execution engine
    ├── formatter.py       # ASCII tabular output formatter
    └── input/             # Sample JSON datasets
```

## Prerequisites & Installation

### 1. Install Graphviz

Install the Graphviz system package:

```bash
sudo apt-get install graphviz
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Part 1: ERD-to-Relational Model Visual Converter

Convert an ERD JSON file into a visual relational schema diagram.

**Syntax:**

```bash
python main.py part1 <path_to_erd.json> -o <output_path_without_extension>
```

**Examples:**

```bash
python main.py part1 part1/input/lab_example.json -o part1/output/relational_schema
```

```bash
python main.py part1 part1/input/full_company_test.json -o part1/output/full_company_schema
```

The output is a PNG diagram representing the generated relational schema.

### Part 2: Relational Algebra Query Executor

Execute Relational Algebra queries against a JSON dataset.

**Syntax:**

```bash
python main.py part2 <path_to_dataset.json> "<QUERY>"
```

#### SELECT

Filters tuples according to a Boolean condition.

**Syntax:**

```text
SELECT[condition](Relation)
```

**Example:**

```bash
python main.py part2 part2/input/data1.json "SELECT[Salary > 5000 AND DeptID = 10](Employee)"
```

#### PROJECT

Selects specific columns from a relation.

**Syntax:**

```text
PROJECT[col1, col2, ...](Relation)
```

**Example:**

```bash
python main.py part2 part2/input/data1.json "PROJECT[Name, Salary](Employee)"
```

#### JOIN

Supports both natural joins and theta joins.

**Natural join syntax:**

```text
JOIN(Rel1, Rel2)
```

**Theta join syntax:**

```text
JOIN[condition](Rel1, Rel2)
```

**Examples:**

```bash
python main.py part2 part2/input/data1.json "JOIN(Employee, Department)"
```

```bash
python main.py part2 part2/input/data1.json "JOIN[Employee.DeptID = Department.DeptID](Employee, Department)"
```

#### Set Operations

Supports `UNION`, `INTERSECT`, and `DIFFERENCE`.

**UNION:** Returns tuples appearing in either relation.

```bash
python main.py part2 part2/input/data1.json "UNION(SELECT[DeptID = 10](Employee), SELECT[Salary > 6000](Employee))"
```

**INTERSECT:** Returns tuples appearing in both relations.

```bash
python main.py part2 part2/input/data1.json "INTERSECT(SELECT[DeptID = 10](Employee), SELECT[Salary >= 5000](Employee))"
```

**DIFFERENCE:** Returns tuples appearing in the first relation but not the second.

```bash
python main.py part2 part2/input/data1.json "DIFFERENCE(Employee, SELECT[DeptID = 20](Employee))"
```

#### AGGREGATE

Performs aggregate calculations, optionally grouping tuples by specified columns.

**Syntax with grouping:**

```text
AGGREGATE[group_cols; FUNC(col), ...](Relation)
```

**Syntax without grouping:**

```text
AGGREGATE[FUNC(col)](Relation)
```

**Example:**

```bash
python main.py part2 part2/input/data1.json "AGGREGATE[DeptID; COUNT(*), AVG(Salary), MAX(Salary)](Employee)"
```

#### Nested Queries

Relational Algebra operations can be nested to build more complex queries.

**Example:** Retrieve the names of employees earning at least 6000, together with their department names.

```bash
python main.py part2 part2/input/data1.json "PROJECT[Employee.Name, Department.Name](JOIN[Employee.DeptID = Department.DeptID](SELECT[Salary >= 6000](Employee), Department))"
```

---

## Features Summary

- **ERD-to-Relational Mapping:** Applies the 7-step ER-to-Relational mapping rules.
- **Schema Visualization:** Generates PNG relational schema diagrams using Graphviz.
- **Relational Algebra Parser:** Parses queries using a recursive-descent parser.
- **Query Execution:** Executes relational operations on JSON datasets without external data manipulation libraries.
- **Condition Evaluation:** Supports Boolean expressions and comparison operators.
- **Join Operations:** Supports natural joins and theta joins.
- **Set Operations:** Supports union, intersection, and difference.
- **Aggregate Operations:** Supports grouping and aggregate functions.
- **Nested Queries:** Allows multiple operations to be combined into a single query.
- **Tabular Output:** Formats query results as ASCII tables.

## Technologies Used

- Python
- Pydantic
- Graphviz
- JSON
- Recursive-descent parsing
- Abstract Syntax Trees (AST)
- Relational Algebra

