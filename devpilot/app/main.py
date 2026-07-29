from flask import Flask, request, jsonify
from sqlalchemy.exc import IntegrityError

from app.models import db, Student, MarkAllocation

app = Flask(__name__)

# Configure database URI from environment variable or default to 'sqlite:///db.sqlite3'
DATABASE_URI = "postgresql://username:password@localhost/db_name"  # Replace with actual values
if DATABASE_URI.startswith("postgres://"):
    DATABASE_URI = DATABASE_URI.replace("postgres://", "postgresql://", 1)

@app.before_first_request
def create_tables():
    db.create_all()

# Define API endpoint for creating a new mark allocation
@app.route("/mark_allocation", methods=["POST"])
def add_mark_allocation():
    try:
        student_id = request.json.get("student_id")
        mark_value = request.json.get("mark_value")

        if not all([student_id, mark_value]):
            return jsonify({"error": "Missing required fields"}), 400

        new_allocation = MarkAllocation(student_id=Student.query.get(int(student_id)), mark_value=int(mark_value))
        db.session.add(new_allocation)
        db.session.commit()

        return jsonify({"message": f"Mark allocation for student {student_id} added successfully."}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Duplicate entry"}), 409

# Define API endpoint for retrieving all mark allocations
@app.route("/mark_allocations", methods=["GET"])
def get_mark_allocations():
    try:
        students = Student.query.all()

        if not students:
            return jsonify([])

        allocations = [allocation.serialize() for allocation in MarkAllocation.query.all()]
        return jsonify(allocations), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)