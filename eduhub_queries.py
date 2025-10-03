"""
eduhub_queries.py
Backup/reference file with functions to:
- create DB + collections with validators
- generate and insert sample data (counts required by the project)
- implement CRUD operations
- run aggregation examples
- create indexes and run explain()
- basic error handling
"""

import uuid
import random
from datetime import datetime, timedelta
import time
import json
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.errors import DuplicateKeyError, WriteError
import pandas as pd

# ======= CONFIG =======

MONGO_URI = "mongodb+srv://< eduhub_db  >:< 5d9W71bLyTJMEwNN  >@cluster0.bkcxczk.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "eduhub_db"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# ======= SCHEMA VALIDATORS (short versions) =======
users_validator = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["userId", "email", "firstName", "lastName", "role", "dateJoined"],
        "properties": {
            "userId": {"bsonType": "string"},
            "email": {"bsonType": "string", "pattern": r"^.+@.+\..+$"},
            "firstName": {"bsonType": "string"},
            "lastName": {"bsonType": "string"},
            "role": {"enum": ["student", "instructor"]},
            "dateJoined": {"bsonType": "date"},
            "isActive": {"bsonType": "bool"}
        }
    }
}

courses_validator = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["courseId", "title", "instructorId", "createdAt"],
        "properties": {
            "courseId": {"bsonType": "string"},
            "title": {"bsonType": "string"},
            "instructorId": {"bsonType": "string"},
            "category": {"bsonType": "string"},
            "level": {"enum": ["beginner", "intermediate", "advanced"]},
            "price": {"bsonType": ["double","int","decimal"]},
            "createdAt": {"bsonType": "date"},
            "isPublished": {"bsonType": "bool"}
        }
    }
}

# ======= UTILS =======
def gen_id(prefix="id"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

# ======= COLLECTION CREATION =======
def create_collections(drop_existing=False):
    if drop_existing:
        print("Dropping existing collections (if any)...")
        for c in ["users","courses","enrollments","lessons","assignments","submissions"]:
            try:
                db.drop_collection(c)
            except Exception:
                pass

    # Create with validators where appropriate
    try:
        db.create_collection("users", validator=users_validator)
    except Exception:
        pass
    try:
        db.create_collection("courses", validator=courses_validator)
    except Exception:
        pass

    # Create other collections without heavy validators for speed
    for name in ["enrollments","lessons","assignments","submissions"]:
        try:
            db.create_collection(name)
        except Exception:
            pass

    # Indexes: unique fields and common lookups
    db.users.create_index([("userId", ASCENDING)], unique=True)
    db.users.create_index([("email", ASCENDING)], unique=True)
    db.courses.create_index([("courseId", ASCENDING)], unique=True)
    db.courses.create_index([("title", TEXT), ("description", TEXT)])  # text search
    db.courses.create_index([("category", ASCENDING)])
    db.enrollments.create_index([("studentId", ASCENDING)])
    db.enrollments.create_index([("courseId", ASCENDING)])
    db.assignments.create_index([("assignmentId", ASCENDING)], unique=True)
    db.assignments.create_index([("dueDate", ASCENDING)])
    print("Collections created and indexes applied.")

# ======= SAMPLE DATA GENERATORS =======
FIRST_NAMES = ["Alex","Maria","John","Sara","Liam","Olivia","Noah","Emma","Ava","Mason"]
LAST_NAMES = ["Smith","Kovács","Nagy","Brown","Garcia","Wang","Patel","Dubois","Rossi","Müller"]
CATEGORIES = ["Data Science","Web Development","Design","Business","Math","Physics","Language","Arts"]
TAGS = ["python","mongodb","beginner","advanced","react","ml","statistics","ux"]

def generate_users(num_students=15, num_instructors=5):
    users = []
    for _ in range(num_students):
        uid = gen_id("stu")
        email = f"{uid}@example.com"
        users.append({
            "userId": uid,
            "email": email,
            "firstName": random.choice(FIRST_NAMES),
            "lastName": random.choice(LAST_NAMES),
            "role": "student",
            "dateJoined": datetime.utcnow() - timedelta(days=random.randint(0,400)),
            "profile": {"bio":"Learner","avatar":None,"skills":random.sample(TAGS, k=2)},
            "isActive": True
        })
    for _ in range(num_instructors):
        uid = gen_id("ins")
        email = f"{uid}@example.com"
        users.append({
            "userId": uid,
            "email": email,
            "firstName": random.choice(FIRST_NAMES),
            "lastName": random.choice(LAST_NAMES),
            "role": "instructor",
            "dateJoined": datetime.utcnow() - timedelta(days=random.randint(30,800)),
            "profile": {"bio":"Instructor","avatar":None,"skills":random.sample(TAGS, k=3)},
            "isActive": True
        })
    return users

def generate_courses(instructors, num_courses=8):
    courses = []
    for i in range(num_courses):
        course_id = gen_id("course")
        instr = random.choice(instructors)["userId"]
        title = f"{random.choice(CATEGORIES)} Basics {i+1}"
        price = random.choice([0,19.99,49.99,99.99,149.99,199.99])
        courses.append({
            "courseId": course_id,
            "title": title,
            "description": f"A practical course on {title}",
            "instructorId": instr,
            "category": random.choice(CATEGORIES),
            "level": random.choice(["beginner","intermediate","advanced"]),
            "duration": random.randint(2,40),
            "price": float(price),
            "tags": random.sample(TAGS, k=3),
            "createdAt": datetime.utcnow() - timedelta(days=random.randint(0,1000)),
            "updatedAt": datetime.utcnow(),
            "isPublished": random.choice([True, False])
        })
    return courses

def generate_enrollments(students, courses, num_enroll=15):
    enrolls = []
    for _ in range(num_enroll):
        stu = random.choice(students)["userId"]
        course = random.choice(courses)["courseId"]
        enrolls.append({
            "enrollmentId": gen_id("enr"),
            "courseId": course,
            "studentId": stu,
            "enrolledAt": datetime.utcnow() - timedelta(days=random.randint(0,300)),
            "progress": random.randint(0,100),
            "completed": random.choice([True, False])
        })
    return enrolls

def generate_lessons(courses, num_lessons=25):
    lessons = []
    for _ in range(num_lessons):
        course = random.choice(courses)["courseId"]
        lid = gen_id("les")
        lessons.append({
            "lessonId": lid,
            "courseId": course,
            "title": f"Lesson for {course} - {lid[-4:]}",
            "content": "Lesson content sample...",
            "order": random.randint(1,12),
            "duration": random.randint(5,60)
        })
    return lessons

def generate_assignments(courses, num_assign=10):
    assigns = []
    for _ in range(num_assign):
        course = random.choice(courses)["courseId"]
        aid = gen_id("asgn")
        assigns.append({
            "assignmentId": aid,
            "courseId": course,
            "title": f"Assignment {aid[-4:]}",
            "description": "Please complete...",
            "dueDate": datetime.utcnow() + timedelta(days=random.randint(1,30)),
            "maxScore": 100,
            "createdAt": datetime.utcnow()
        })
    return assigns

def generate_submissions(assignments, students, num_sub=12):
    subs = []
    for _ in range(num_sub):
        a = random.choice(assignments)["assignmentId"]
        s = random.choice(students)["userId"]
        subs.append({
            "submissionId": gen_id("sub"),
            "assignmentId": a,
            "studentId": s,
            "submittedAt": datetime.utcnow() - timedelta(days=random.randint(0,20)),
            "content": "Answer file or text...",
            "score": random.randint(40,100),
            "feedback": "Well done"
        })
    return subs

# ======= CRUD + OPERATIONS =======
def insert_many_safe(collection_name, docs):
    if not docs:
        return 0
    coll = db[collection_name]
    try:
        res = coll.insert_many(docs, ordered=False)
        return len(res.inserted_ids)
    except DuplicateKeyError as e:
        print("Duplicate key error during bulk insert:", e)
        return 0
    except Exception as e:
        print("Insert error:", e)
        return 0

def init_sample_data(drop_existing=False):
    create_collections(drop_existing=drop_existing)
    # generate
    users = generate_users(num_students=15, num_instructors=5)  # total 20
    instructors = [u for u in users if u["role"]=="instructor"]
    students = [u for u in users if u["role"]=="student"]
    courses = generate_courses(instructors, num_courses=8)
    enrollments = generate_enrollments(students, courses, num_enroll=15)
    lessons = generate_lessons(courses, num_lessons=25)
    assignments = generate_assignments(courses, num_assign=10)
    submissions = generate_submissions(assignments, students, num_sub=12)

    # insert
    print("Inserting users...", insert_many_safe("users", users))
    print("Inserting courses...", insert_many_safe("courses", courses))
    print("Inserting enrollments...", insert_many_safe("enrollments", enrollments))
    print("Inserting lessons...", insert_many_safe("lessons", lessons))
    print("Inserting assignments...", insert_many_safe("assignments", assignments))
    print("Inserting submissions...", insert_many_safe("submissions", submissions))
    print("Sample data insertion complete.")

# Basic Create operations
def add_student(firstName, lastName, email):
    coll = db.users
    doc = {
        "userId": gen_id("stu"),
        "email": email,
        "firstName": firstName,
        "lastName": lastName,
        "role": "student",
        "dateJoined": datetime.utcnow(),
        "profile": {"bio":"", "avatar": None, "skills": []},
        "isActive": True
    }
    try:
        coll.insert_one(doc)
        return doc
    except DuplicateKeyError:
        raise

def create_course(title, instructorId, **kwargs):
    coll = db.courses
    doc = {
        "courseId": gen_id("course"),
        "title": title,
        "description": kwargs.get("description",""),
        "instructorId": instructorId,
        "category": kwargs.get("category","General"),
        "level": kwargs.get("level","beginner"),
        "duration": kwargs.get("duration", 5),
        "price": float(kwargs.get("price", 0)),
        "tags": kwargs.get("tags", []),
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
        "isPublished": kwargs.get("isPublished", False)
    }
    return coll.insert_one(doc).inserted_id

def enroll_student(studentId, courseId):
    coll = db.enrollments
    doc = {
        "enrollmentId": gen_id("enr"),
        "studentId": studentId,
        "courseId": courseId,
        "enrolledAt": datetime.utcnow(),
        "progress": 0,
        "completed": False
    }
    return coll.insert_one(doc).inserted_id

# Read operations
def find_active_students():
    return list(db.users.find({"role":"student","isActive":True}))

def get_course_with_instructor(courseId):
    pipeline = [
        {"$match":{"courseId":courseId}},
        {"$lookup":{
            "from":"users",
            "localField":"instructorId",
            "foreignField":"userId",
            "as":"instructor"
        }},
        {"$unwind":"$instructor"}
    ]
    return list(db.courses.aggregate(pipeline))

def find_courses_by_category(category):
    return list(db.courses.find({"category":category}))

def find_students_in_course(courseId):
    pipeline = [
        {"$match":{"courseId":courseId}},
        {"$lookup":{
            "from":"enrollments",
            "localField":"courseId",
            "foreignField":"courseId",
            "as":"enrollments"
        }},
        {"$unwind":"$enrollments"},
        {"$lookup":{
            "from":"users",
            "localField":"enrollments.studentId",
            "foreignField":"userId",
            "as":"student"
        }},
        {"$unwind":"$student"},
        {"$replaceRoot":{"newRoot":"$student"}}
    ]
    return list(db.courses.aggregate(pipeline))

def search_courses_by_title(term):
    # case-insensitive partial match using regex
    regex = {"$regex": term, "$options": "i"}
    return list(db.courses.find({"title": regex}))

# Update operations
def update_user_profile(userId, profile_updates):
    return db.users.update_one({"userId":userId},{"$set":{"profile":profile_updates}})

def mark_course_published(courseId):
    return db.courses.update_one({"courseId":courseId},{"$set":{"isPublished":True,"updatedAt":datetime.utcnow()}})

def update_assignment_grade(submissionId, score, feedback=None):
    update = {"score":score}
    if feedback is not None:
        update["feedback"] = feedback
    return db.submissions.update_one({"submissionId":submissionId},{"$set":update})

def add_tags_to_course(courseId, tags):
    return db.courses.update_one({"courseId":courseId},{"$addToSet":{"tags":{"$each":tags}}})

# Delete (soft/hard)
def soft_delete_user(userId):
    return db.users.update_one({"userId":userId},{"$set":{"isActive":False}})

def delete_enrollment(enrollmentId):
    return db.enrollments.delete_one({"enrollmentId":enrollmentId})

def remove_lesson(lessonId):
    return db.lessons.delete_one({"lessonId":lessonId})

# ======= ADVANCED QUERIES =======
def find_courses_price_range(min_p, max_p):
    return list(db.courses.find({"price":{"$gte":min_p,"$lte":max_p}}))

def users_joined_last_n_months(n=6):
    cutoff = datetime.utcnow() - timedelta(days=30*n)
    return list(db.users.find({"dateJoined":{"$gte":cutoff}}))

def find_courses_with_tags(tags):
    return list(db.courses.find({"tags":{"$in":tags}}))

def assignments_due_next_week():
    now = datetime.utcnow()
    soon = now + timedelta(days=7)
    return list(db.assignments.find({"dueDate":{"$gte":now,"$lte":soon}}))

# Example aggregation: count enrollments per course
def enrollments_per_course(limit=20):
    pipeline = [
        {"$group":{"_id":"$courseId","totalEnrollments":{"$sum":1}}},
        {"$sort":{"totalEnrollments":-1}},
        {"$limit":limit}
    ]
    return list(db.enrollments.aggregate(pipeline))

# Average grade per student
def average_grade_per_student(limit=20):
    pipeline = [
        {"$group":{"_id":"$studentId","avgScore":{"$avg":"$score"}}},
        {"$sort":{"avgScore":-1}},
        {"$limit":limit}
    ]
    return list(db.submissions.aggregate(pipeline))

# Revenue per instructor (sum of course price * enrollments)
def revenue_per_instructor():
    pipeline = [
        {"$lookup":{"from":"courses","localField":"courseId","foreignField":"courseId","as":"course"}},
        {"$unwind":"$course"},
        {"$group":{
            "_id":"$course.instructorId",
            "revenue":{"$sum":"$course.price"}
        }},
        {"$sort":{"revenue":-1}}
    ]
    return list(db.enrollments.aggregate(pipeline))

# ======= PERFORMANCE & EXPLAIN HELPERS =======
def explain_query(collection, filter_doc):
    coll = db[collection]
    return coll.find(filter_doc).explain("executionStats")

def time_function(fn, *args, **kwargs):
    s = time.time()
    res = fn(*args, **kwargs)
    elapsed = time.time() - s
    return elapsed, res

# ======= SAVE/EXPORT FUNCTIONS =======
def export_collection_to_json(collection_name, path):
    docs = list(db[collection_name].find({}, {"_id":0}))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(docs, f, default=str, indent=2)
    return path

# ======= MAIN for quick run =======
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true", help="Create collections and insert sample data")
    parser.add_argument("--drop", action="store_true", help="Drop existing collections before init")
    args = parser.parse_args()

    if args.init:
        init_sample_data(drop_existing=args.drop)
        # Export sample data
        export_collection_to_json("users", "data/sample_users.json")
        export_collection_to_json("courses", "data/sample_courses.json")
        export_collection_to_json("enrollments", "data/sample_enrollments.json")
        export_collection_to_json("lessons", "data/sample_lessons.json")
        export_collection_to_json("assignments", "data/sample_assignments.json")
        export_collection_to_json("submissions", "data/sample_submissions.json")
        print("Exported sample data to data/*.json")
