# API Documentation

Complete API reference for Mew Assistant - see README.md for quick examples.

## 📖 Interactive Documentation

The best way to explore the API is through the interactive Swagger UI:

**URL**: http://localhost:8000/docs

This provides:
- Complete endpoint documentation
- Request/response schemas
- Try-it-out functionality
- Schema definitions

---

## 🚀 Quick Reference

See the [main README](../README.md) for complete API examples with curl commands.

### Available Endpoints

**Sessions**:
- `POST /mew/session` - Create session
- `GET /mew/session/{id}` - Get session
- `GET /mew/sessions/user/{user_id}` - List user sessions
- `POST /mew/confirm` - Confirm session with cooldown

**Messages**:
- `POST /mew/ingest` - Ingest single message
- `POST /mew/ingest/batch` - Batch ingest
- `GET /mew/messages/unprocessed` - Get unprocessed

**Summaries**:
- `POST /mew/summary` - Generate summary
- `GET /mew/summaries/user/{user_id}` - Get user summaries

---

## 📥 Import into Postman

1. Export OpenAPI schema: Available at `/openapi.json`
2. Import into Postman: File → Import → Select openapi.json
3. Start testing!

---

For detailed examples, see [README.md](../README.md#-api-reference)
