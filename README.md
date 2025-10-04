# EduHub-MongoDB-Project
This project implements a complete MongoDB backend for an e‑learning platform called EduHub. It includes data modeling, sample data population, CRUD operations, aggregation analytics, indexing and performance analysis, schema validation, and error handling using Python (PyMongo) and a Jupyter Notebook.
# EduHub — MongoDB Project

**Repository name:** `mongodb-eduhub-project`

## Overview

This project implements a complete MongoDB backend for an e‑learning platform called **EduHub**. It includes data modeling, sample data population, CRUD operations, aggregation analytics, indexing and performance analysis, schema validation, and error handling using **Python (PyMongo)** and a Jupyter Notebook.

---

## Repository structure (required)

```
mongodb-eduhub-project/

├── README.md

├── notebooks/
│   └── eduhub_mongodb_project.ipynb

├── src/
│   └── eduhub_queries.py

├── data/
│   ├── sample_data.json
│   └── schema_validation.json

├── docs/
│   ├── performance_analysis.md
│   └── presentation.pptx

└── .gitignore
```

---

## Setup & Requirements

**Prerequisites:**

* Python 3.9+
* MongoDB server v8.0+ running locally (or remote URI)
* pip packages: `pymongo`, `pandas`, `dnspython` (only if using SRV URIs), `python-dateutil`

Install dependencies:

```bash
python -m pip install pymongo pandas python-dateutil
```

Start MongoDB locally (example):

```bash
# macOS / Linux (brew):
brew services start mongodb-community@8.0

# or with mongod manually:
mongod --config /usr/local/etc/mongod.conf
```

## How to run

1. Clone the repository and `cd mongodb-eduhub-project`.
2. Inspect/modify `src/eduhub_queries.py` for `MONGO_URI` and database name.
3. Run the script to create collections and sample data (optional):

```bash
python src/eduhub_queries.py --init
```

4. Open the notebook `notebooks/eduhub_mongodb_project.ipynb` in Jupyter and execute all cells to see queries and outputs.

---

## Deliverables included

* `notebooks/eduhub_mongodb_project.ipynb` — Interactive notebook with all tasks and outputs.
* `src/eduhub_queries.py` — Python backup with well‑structured functions for each task.
* `data/sample_data.json` — Exported JSON of sample data (collections).
* `data/schema_validation.json` — JSON validators used for collection creation.
* `docs/performance_analysis.md` — Explain results before/after indexing with timings and `explain()` outputs.
* `docs/presentation.pptx` — A 5–10 slide presentation summarizing design decisions.

---

## Schemas (summary)

**users**

* `userId` (string, unique)
* `email` (string, unique)
* `firstName`, `lastName` (string)
* `role` (enum: `student` or `instructor`)
* `dateJoined` (date)
* `profile` (object: bio, avatar, skills[])
* `isActive` (bool)

**courses**

* `courseId` (string, unique)
* `title`, `description` (string)
* `instructorId` (ref to users.userId)
* `category`, `level` (enum)
* `duration` (number hours), `price` (number)
* `tags` (array)
* `createdAt`, `updatedAt` (date)
* `isPublished` (bool)

**enrollments**

* `enrollmentId` (string)
* `courseId`, `studentId` (refs)
* `enrolledAt` (date)
* `progress` (0-100)
* `completed` (bool)

**lessons**

* `lessonId`, `courseId`, `title`, `content`, `order`, `duration`

**assignments**

* `assignmentId`, `courseId`, `title`, `description`, `dueDate`, `maxScore`


