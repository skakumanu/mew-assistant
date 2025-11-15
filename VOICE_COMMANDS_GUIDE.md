# 🎤 Voice Commands - Multilingual Support

## Overview

Mew Assistant supports voice commands in **20+ languages** for hands-free scheduling and family assistance. Perfect for busy parents, caregivers, and families who need quick access to scheduling features while multitasking.

## Supported Languages

| Language | Code | Native Name |
|----------|------|-------------|
| English (US) | en-US | English |
| English (UK) | en-GB | English |
| Spanish (Spain) | es-ES | Español |
| Spanish (Mexico) | es-MX | Español |
| French | fr-FR | Français |
| German | de-DE | Deutsch |
| Italian | it-IT | Italiano |
| Portuguese (Brazil) | pt-BR | Português |
| Chinese (Simplified) | zh-CN | 中文 |
| Chinese (Traditional) | zh-TW | 中文 |
| Japanese | ja-JP | 日本語 |
| Korean | ko-KR | 한국어 |
| Arabic | ar-SA | العربية |
| Hindi | hi-IN | हिन्दी |
| Russian | ru-RU | Русский |
| Dutch | nl-NL | Nederlands |
| Polish | pl-PL | Polski |
| Turkish | tr-TR | Türkçe |
| Vietnamese | vi-VN | Tiếng Việt |
| Thai | th-TH | ไทย |

## Technology Stack

### Primary: Azure Speech Services
- Enterprise-grade speech recognition
- Real-time transcription
- Automatic language detection
- Continuous conversation mode

### Fallback: OpenAI Whisper
- When Azure is unavailable
- Automatic language detection
- High accuracy across languages

### Natural Language Understanding
- GPT-4 powered intent parsing
- Context-aware command interpretation
- Family-friendly language processing

## How It Works

```
┌─────────────┐
│ Voice Input │
│ (Any Lang)  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Speech-to-Text  │
│ (Azure/Whisper) │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Language Detect │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Parse Command   │
│ (NLU/GPT-4)     │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Execute Action  │
│ (Schedule, etc) │
└─────────────────┘
```

## API Usage

### Process Voice Command

```bash
curl -X POST "http://localhost:8000/voice/command" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "audio=@recording.wav" \
  -F "preferred_language=en-US"
```

**Response:**
```json
{
  "success": true,
  "command_id": 123,
  "transcription": "Schedule therapy session for tomorrow at 3pm",
  "detected_language": "en-US",
  "intent": "schedule",
  "entities": {
    "datetime": "2024-01-16T15:00:00",
    "activity": "therapy",
    "duration": 60
  },
  "confidence": 0.95,
  "suggested_action": {
    "type": "create_event",
    "parameters": {
      "datetime": "2024-01-16T15:00:00",
      "activity": "therapy",
      "duration": 60
    }
  }
}
```

### Get Supported Languages

```bash
curl -X GET "http://localhost:8000/voice/languages"
```

**Response:**
```json
{
  "languages": {
    "en-US": "English (US)",
    "es-ES": "Spanish (Spain)",
    "fr-FR": "French",
    ...
  },
  "count": 20
}
```

### Start Continuous Session

For hands-free operation with multiple commands:

```bash
curl -X POST "http://localhost:8000/voice/session/start" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "en-US"
  }'
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": 1,
  "language": "en-US",
  "started_at": "2024-01-15T10:00:00Z",
  "command_count": 0
}
```

## Example Voice Commands

### English
- "Schedule therapy session for tomorrow at 3pm"
- "Move Tuesday's appointment to Thursday"
- "Cancel dentist appointment"
- "What's on the schedule for today?"
- "Generate weekly summary"

### Spanish
- "Programa una sesión de terapia para mañana a las 3"
- "Mueve la cita del martes al jueves"
- "Cancela la cita del dentista"
- "¿Qué hay en el horario de hoy?"
- "Genera un resumen semanal"

### French
- "Planifier une séance de thérapie pour demain à 15h"
- "Déplacer le rendez-vous de mardi à jeudi"
- "Annuler le rendez-vous chez le dentiste"
- "Qu'est-ce qu'il y a à l'horaire aujourd'hui?"
- "Générer un résumé hebdomadaire"

### Chinese (Simplified)
- "明天下午三点安排治疗课程"
- "把周二的预约改到周四"
- "取消牙医预约"
- "今天的日程是什么?"
- "生成每周总结"

## Supported Intents

The system recognizes these intents across all languages:

1. **schedule** - Create new appointments/sessions
2. **reschedule** - Move existing appointments
3. **cancel** - Delete appointments
4. **summary** - Generate caregiver summaries
5. **tutoring** - Request homework help
6. **question** - Ask about schedule

## Setup Instructions

### 1. Azure Speech Services (Recommended)

```bash
# Get Azure Speech key
az cognitiveservices account keys list \
  --name mew-speech \
  --resource-group mew-assistant

# Add to .env
AZURE_SPEECH_KEY=your-key-here
AZURE_SPEECH_REGION=eastus
```

### 2. OpenAI Whisper (Fallback)

```bash
# Add to .env
OPENAI_API_KEY=your-openai-key
```

### 3. Install Dependencies

```bash
pip install azure-cognitiveservices-speech langdetect openai
```

## Audio Format Support

- **WAV** (recommended) - Uncompressed, best quality
- **MP3** - Compressed, smaller files
- **OGG** - Open format
- **FLAC** - Lossless compression

**Recommended Settings:**
- Sample Rate: 16kHz or 48kHz
- Bit Depth: 16-bit
- Channels: Mono

## Best Practices

### For Users
1. **Speak Clearly**: Enunciate words for better recognition
2. **Reduce Noise**: Use in quiet environments when possible
3. **Be Specific**: Include dates, times, and details
4. **Natural Language**: Speak naturally, no special commands needed
5. **Verify Results**: Always check transcription for accuracy

### For Developers
1. **Store Audio**: Keep recordings for audit and debugging
2. **Handle Fallbacks**: Gracefully degrade to Whisper if Azure fails
3. **Log Confidence**: Track confidence scores for quality monitoring
4. **Privacy First**: Encrypt stored audio files
5. **Delete Old Files**: Implement retention policies

## Privacy & Security

### Data Handling
- ✅ Audio encrypted at rest
- ✅ Transcriptions logged for audit
- ✅ HIPAA compliant storage
- ✅ Automatic deletion after 90 days
- ✅ User can request deletion anytime

### Parent Approval
All voice commands from kids require parental approval before execution. See [PARENTAL_APPROVAL_SUMMARY.md](PARENTAL_APPROVAL_SUMMARY.md).

## Troubleshooting

### Low Confidence Scores

If confidence < 0.7, the system may ask for confirmation:

```json
{
  "success": true,
  "transcription": "Schedule therapy tomorrow at 3",
  "confidence": 0.65,
  "warning": "Low confidence. Please confirm: Did you mean 'Schedule therapy session for tomorrow at 3pm'?"
}
```

### Language Detection Issues

Specify preferred language explicitly:

```bash
curl -X POST "http://localhost:8000/voice/command" \
  -F "audio=@recording.wav" \
  -F "preferred_language=es-ES"  # Force Spanish
```

### Azure Connection Errors

System automatically falls back to OpenAI Whisper. Check logs:

```bash
tail -f logs/app.log | grep "voice"
```

## Performance Metrics

| Metric | Azure Speech | Whisper |
|--------|--------------|---------|
| Latency | ~1-2s | ~3-5s |
| Accuracy | 95%+ | 90%+ |
| Languages | 20+ | 99+ |
| Cost | $1/hour | $0.006/min |
| Offline | ❌ | ❌ |

## Future Enhancements

- [ ] Offline voice recognition
- [ ] Voice biometrics for authentication
- [ ] Speaker diarization (identify who's speaking)
- [ ] Real-time streaming transcription
- [ ] Voice shortcuts/macros
- [ ] Custom wake words ("Hey Mew...")

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on adding:
- New language support
- Custom intents
- Voice command patterns
- NLU improvements

## Support

For voice-related issues:
- 📧 Email: support@mew-assistant.com
- 💬 Discord: #voice-commands
- 📚 Docs: https://docs.mew-assistant.com/voice

---

**Made with ❤️ for special needs families**
