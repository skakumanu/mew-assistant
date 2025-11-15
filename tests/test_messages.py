"""Test message endpoints"""


def test_ingest_message(client):
    """Test ingesting a message"""
    response = client.post(
        "/mew/ingest",
        json={
            "channel": "email",
            "sender": "parent@example.com",
            "subject": "Question about session",
            "body": "When is the next tutoring session?"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["channel"] == "email"
    assert data["sender"] == "parent@example.com"
    assert data["processed"] is False


def test_batch_ingest(client):
    """Test batch message ingestion"""
    batch_data = {
        "messages": [
            {
                "channel": "email",
                "sender": f"user{i}@example.com",
                "subject": f"Subject {i}",
                "body": f"Message {i}"
            }
            for i in range(5)
        ]
    }
    
    response = client.post("/mew/ingest/batch", json=batch_data)
    assert response.status_code == 201
    data = response.json()
    assert len(data) == 5


def test_get_unprocessed_messages(client):
    """Test retrieving unprocessed messages"""
    # Ingest some messages
    for i in range(3):
        client.post(
            "/mew/ingest",
            json={
                "channel": "sms",
                "sender": f"+1234567890{i}",
                "body": f"Test message {i}"
            }
        )
    
    # Get unprocessed
    response = client.get("/mew/messages/unprocessed")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3
