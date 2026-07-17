"""Test per la rotazione community nel messaggio del recap."""
from datetime import date

from copyfunnel.weekly_recap import COMMUNITIES, community_della_settimana


def test_rotazione_deterministica_per_settimana():
    a = community_della_settimana(date(2026, 7, 18))
    assert a == community_della_settimana(date(2026, 7, 18))
    b = community_della_settimana(date(2026, 7, 25))
    assert a != b  # settimane consecutive → community diverse


def test_tutte_le_community_hanno_nome_e_url():
    assert len(COMMUNITIES) >= 4
    for nome, url in COMMUNITIES:
        assert nome and url.startswith("https://x.com/i/communities/")


def test_ciclo_completo_copre_tutte():
    viste = {community_della_settimana(date(2026, 7, 4 + 7 * i))[0]
             for i in range(len(COMMUNITIES))}
    assert len(viste) == len(COMMUNITIES)
