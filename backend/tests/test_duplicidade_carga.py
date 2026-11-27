"""RK-02 / DA-CONF-I2-01 (CT-51, Q-07): 1.000 mensagens com 20% reenviadas geram 0 pedidos duplicados."""

import pytest
from sqlalchemy import func, select

from app.models import Pedido
from tests.conftest import mensagem, rodar

TOTAL = 1000


@pytest.mark.regressao
def test_mil_mensagens_com_reenvio_sem_duplicidade(catalogo, client, whatsapp_fake, llm_fake):
    llm_fake["responder"](("tomate", 2, "kg"))
    # telefone distinto por mensagem: cada uma vira um pedido novo (sem cair na confirmação)
    eventos = [mensagem("quero 2 kg de tomate", telefone=f"55839{i:08d}") for i in range(TOTAL)]
    for i, evento in enumerate(eventos):
        assert client.post("/webhook/whatsapp", json=evento).status_code == 200
        if i % 5 == 0:  # 20% reenviadas pela Evolution
            assert client.post("/webhook/whatsapp", json=evento).status_code == 200

    assert rodar(lambda s: s.scalar(select(func.count()).select_from(Pedido))) == TOTAL
    assert len(whatsapp_fake) == TOTAL
