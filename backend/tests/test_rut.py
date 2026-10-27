"""Pruebas de normalizacion y validacion de RUT."""

import pytest

from app.core.rut import calcular_digito_verificador, es_rut_valido, normalizar_rut


@pytest.mark.parametrize(
    ("cuerpo", "esperado"),
    [
        ("12345678", "5"),
        ("11111111", "1"),
        ("22222222", "2"),
        ("1000005", "K"),
    ],
)
def test_digito_verificador(cuerpo, esperado):
    assert calcular_digito_verificador(cuerpo) == esperado


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("12.345.678-5", "12345678-5"),
        ("123456785", "12345678-5"),
        (" 11.111.111-1 ", "11111111-1"),
        ("11111111-1", "11111111-1"),
    ],
)
def test_normalizacion(entrada, esperado):
    assert normalizar_rut(entrada) == esperado


def test_k_minuscula_es_digito_valido():
    assert calcular_digito_verificador("1000005") == "K"
    assert normalizar_rut("1.000.005-k") == "1000005-K"


@pytest.mark.parametrize(
    "entrada",
    ["12345678-9", "abc", "", "12345678", "12.345.678", "12345678901-1"],
)
def test_ruts_invalidos(entrada):
    with pytest.raises(ValueError):
        normalizar_rut(entrada)


def test_es_rut_valido():
    assert es_rut_valido("12345678-5") is True
    assert es_rut_valido("12345678-9") is False
