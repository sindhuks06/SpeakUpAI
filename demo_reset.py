from db_manager import client_db

def reset_demo_db():
    client_db.delete_collection("mock_interview_memory")
    demo_collection = client_db.get_or_create_collection("mock_interview_memory")
    demo_collection.add(
        ids=["demo_1"],
        documents=["Q: What is normalization in DBMS?\nA: To reduce redundancy.\nConfidence: 0.9"],
        metadatas=[{"user_id": "demo"}]
    )
    print("✅ Demo DB reset complete!")


if __name__ == "__main__":
    reset_demo_db()