from app.db import fetch_vagas_assignments, remove_vaga_assignment, save_vaga_assignment


def test_vagas_assignment_roundtrip():
    vaga_index = 12
    item = {
        'LT': 'LT-123',
        'Driver': 'Motorista Teste',
        'Station Name': 'Estação 1',
        'Vehicle Plate Number': 'ABC1234',
        'Schedule Arrival Time': '08:00',
        'TO': 'TO-99',
    }

    saved = save_vaga_assignment(vaga_index, item)
    assert saved['vaga_index'] == vaga_index
    assert saved['lt'] == 'LT-123'

    vagas = fetch_vagas_assignments()
    assert any(v['vaga_index'] == vaga_index and v['lt'] == 'LT-123' for v in vagas)

    removed = remove_vaga_assignment(vaga_index=vaga_index)
    assert removed is True

    vagas_after = fetch_vagas_assignments()
    assert not any(v['vaga_index'] == vaga_index for v in vagas_after)
