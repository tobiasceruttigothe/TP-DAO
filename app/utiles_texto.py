def pesos(monto: float) -> str:
    """$32.500 (formato argentino, sin decimales)."""
    return f"${monto:,.0f}".replace(",", ".")
