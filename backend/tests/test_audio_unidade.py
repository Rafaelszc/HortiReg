import pytest

from app.services import audio
from app.services.audio import Rejeicao


@pytest.mark.parametrize(
    "mimetype, esperado",
    [
        ("audio/ogg; codecs=opus", "audio/ogg"),
        ("AUDIO/OGG", "audio/ogg"),
        ("audio/mpeg", "audio/mp3"),
        ("audio/aac", "audio/aac"),
        ("audio/x-wav", "audio/wav"),
        (None, "audio/ogg"),  # evento sem tipo: nota de voz
        ("", "audio/ogg"),
        ("audio/amr", None),
        ("video/mp4", None),
    ],
)
def test_mime_gemini(mimetype, esperado):
    assert audio.mime_gemini(mimetype) == esperado


@pytest.mark.parametrize(
    "msg_audio, esperado",
    [
        ({"mimetype": "audio/ogg; codecs=opus", "seconds": 59}, None),
        ({"mimetype": "audio/ogg; codecs=opus", "seconds": 60}, None),
        ({"mimetype": "audio/ogg; codecs=opus", "seconds": 61}, Rejeicao.LONGO),
        ({"mimetype": "audio/ogg", "seconds": "75"}, Rejeicao.LONGO),
        ({"mimetype": "audio/ogg"}, None),  # sem duração: vale a guarda por tamanho
        ({"mimetype": "audio/ogg", "seconds": "abc"}, None),
        ({"mimetype": "audio/amr", "seconds": 10}, Rejeicao.FORMATO),
        ({"mimetype": "audio/amr", "seconds": 90}, Rejeicao.FORMATO),  # formato vence a duração
    ],
)
def test_validar(msg_audio, esperado):
    assert audio.validar(msg_audio) is esperado


def test_tamanho_valido(monkeypatch):
    monkeypatch.setattr(audio.settings, "audio_max_bytes", 10)
    assert audio.tamanho_valido(b"x" * 10)
    assert not audio.tamanho_valido(b"x" * 11)
