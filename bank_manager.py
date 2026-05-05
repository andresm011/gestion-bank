from __future__ import annotations

import difflib
import json
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

ROUND_STEP_EUR = 1.0
TIPSTERS_FILE = Path(__file__).with_name("tipsters.json")
SETTINGS_FILE = Path(__file__).with_name("settings.json")


@dataclass
class Tipster:
    name: str
    base_unit: float
    usual_stake: float
    confidence_eur: float

    @property
    def usual_bet(self) -> float:
        return self.confidence_eur


def load_tipsters() -> List[Tipster]:
    if not TIPSTERS_FILE.exists():
        raise FileNotFoundError(f"No existe el archivo de tipsters: {TIPSTERS_FILE}")

    with TIPSTERS_FILE.open("r", encoding="utf-8") as f:
        raw_data = json.load(f)

    if not isinstance(raw_data, list) or not raw_data:
        raise ValueError("El archivo tipsters.json debe contener una lista con datos.")

    tipsters: List[Tipster] = []
    required_keys = {"name", "base_unit", "usual_stake", "confidence_eur"}
    for idx, item in enumerate(raw_data, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Entrada #{idx} invalida: debe ser un objeto JSON.")
        missing = required_keys - set(item.keys())
        if missing:
            missing_str = ", ".join(sorted(missing))
            raise ValueError(f"Entrada #{idx} invalida: faltan campos ({missing_str}).")

        tipsters.append(
            Tipster(
                name=str(item["name"]),
                base_unit=float(item["base_unit"]),
                usual_stake=float(item["usual_stake"]),
                confidence_eur=float(item["confidence_eur"]),
            )
        )

    return tipsters


TIPSTERS = load_tipsters()


def ask_float(prompt: str, min_value: float = 0.0) -> float:
    while True:
        raw = input(prompt).strip().replace(",", ".")
        try:
            value = float(raw)
            if value <= min_value:
                print(f"Introduce un numero mayor que {min_value}.")
                continue
            return value
        except ValueError:
            print("Valor no valido. Prueba otra vez.")


def load_settings() -> Optional[tuple[float, float]]:
    if not SETTINGS_FILE.exists():
        return None

    try:
        with SETTINGS_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        bank = float(data["bank"])
        max_percent = float(data["max_percent"])
        if bank <= 0 or max_percent <= 0:
            return None
        return bank, max_percent
    except (ValueError, TypeError, KeyError):
        return None


def save_settings(bank: float, max_percent: float) -> None:
    data = {"bank": bank, "max_percent": max_percent}
    with SETTINGS_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=True, indent=2)


def get_scale_factor(max_bet: float) -> float:
    max_confidence = max(t.confidence_eur for t in TIPSTERS)
    if max_confidence <= 0:
        return 1.0
    return max_bet / max_confidence


def get_scaled_confidence(confidence_eur: float, scale_factor: float) -> float:
    return confidence_eur * scale_factor


def round_to_step(amount: float, step: float = ROUND_STEP_EUR) -> float:
    if step <= 0:
        return amount
    return round(amount / step) * step


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return normalized.strip().lower()


def format_stake_value(stake: float) -> str:
    if stake.is_integer():
        return f"{int(stake)}"
    return f"{stake:.2f}".rstrip("0").rstrip(".")


def print_whatsapp_summary(bank: float, max_percent: float, max_bet: float, scale_factor: float) -> None:
    print("\n" + "=" * 132)
    print("FORMATO WHATSAPP (COPIAR/PEGAR)")
    print("=" * 132)
    print(
        f"Para un bankroll de **{bank:.2f}EUR** con un limite maximo del **{max_percent:.2f}%**, "
        f"tu apuesta tope absoluta es de **{max_bet:.2f}EUR**.\n"
    )
    print(
        "Aplicando el factor de escala correspondiente para mantener la jerarquia de confianza "
        "de la tabla original, aqui tienes la lista redondeada y lista para usar:\n"
    )
    print(
        f"### TABLA STAKES ACTUALIZADA (BANK {bank:.2f}EUR - MAX {max_percent:.2f}% = {max_bet:.2f}EUR)\n"
    )

    for t in TIPSTERS:
        scaled_confidence_raw = get_scaled_confidence(t.confidence_eur, scale_factor)
        scaled_confidence = round_to_step(scaled_confidence_raw)
        scaled_unit = round_to_step(scaled_confidence / t.usual_stake, step=0.01)
        stake_value = format_stake_value(t.usual_stake)

        print(f"**{t.name}**")
        print(f"Unidad: {scaled_unit:.2f}EUR")
        print(f"Stake {stake_value} -> **{scaled_confidence:.2f}EUR**\n")


def find_tipster(query: str) -> Optional[Tipster]:
    q = normalize_text(query)
    if not q:
        return None

    for tipster in TIPSTERS:
        if normalize_text(tipster.name) == q:
            return tipster

    for tipster in TIPSTERS:
        if q in normalize_text(tipster.name):
            return tipster

    tipster_names = [tipster.name for tipster in TIPSTERS]
    normalized_map = {normalize_text(tipster.name): tipster for tipster in TIPSTERS}
    close = difflib.get_close_matches(q, list(normalized_map.keys()), n=1, cutoff=0.6)
    if close:
        return normalized_map[close[0]]

    # Fallback: similarity by original names.
    close_original = difflib.get_close_matches(query.strip(), tipster_names, n=1, cutoff=0.6)
    if close_original:
        return next((tip for tip in TIPSTERS if tip.name == close_original[0]), None)

    return None


def print_summary(bank: float, max_percent: float) -> None:
    max_bet = bank * (max_percent / 100.0)
    scale_factor = get_scale_factor(max_bet)
    print("\n" + "=" * 132)
    print(f"Bank actual: {bank:.2f} EUR | Limite por apuesta: {max_percent:.2f}% ({max_bet:.2f} EUR)")
    print(f"Factor de escala aplicado: x{scale_factor:.4f}")
    print("=" * 132)
    print(
        f"{'Tipster':<18} {'Unidad base':>12} {'Stake hab.':>12} "
        f"{'Conf. original':>14} {'Conf. escalada':>14} {'Estado':>12}"
    )
    print("-" * 132)

    for t in TIPSTERS:
        scaled_confidence_raw = get_scaled_confidence(t.confidence_eur, scale_factor)
        scaled_confidence = round_to_step(scaled_confidence_raw)
        status = "OK" if scaled_confidence <= max_bet else "REVISAR"
        print(
            f"{t.name[:18]:<18} {t.base_unit:>12.2f} {t.usual_stake:>12.2f} "
            f"{t.confidence_eur:>14.2f} {scaled_confidence:>14.2f} {status:>12}"
        )

    print("-" * 132)
    print("Confianza original = valor entre parentesis en tu tabla.")
    print("Confianza escalada = importe ajustado automaticamente a tu bank.\n")
    print_whatsapp_summary(bank, max_percent, max_bet, scale_factor)


def calculate_pick(bank: float, max_percent: float) -> None:
    max_bet = bank * (max_percent / 100.0)
    scale_factor = get_scale_factor(max_bet)
    name = input("Nombre del tipster: ").strip()
    tipster = find_tipster(name)
    if not tipster:
        print("No se encontro ese tipster.")
        return

    print(f"Tipster detectado: {tipster.name}")
    stake = ask_float("Stake del pick (valor real del tipster, ej: 1.5): ", min_value=0.0)
    scaled_confidence_raw = get_scaled_confidence(tipster.confidence_eur, scale_factor)
    scaled_confidence = round_to_step(scaled_confidence_raw)
    scaled_unit = scaled_confidence / tipster.usual_stake
    amount = round_to_step(scaled_unit * stake)
    capped_amount = round_to_step(min(amount, max_bet))

    print("\nResultado del pick")
    print("-" * 30)
    print(f"Tipster: {tipster.name}")
    print(f"Unidad base actual: {tipster.base_unit:.2f} EUR")
    print(f"Confianza base del tipster: {tipster.confidence_eur:.2f} EUR")
    print(f"Confianza escalada a tu bank: {scaled_confidence:.2f} EUR")
    print(f"Stake habitual tipster: {tipster.usual_stake:.2f}")
    print(f"Stake introducido: {stake:.2f}")
    print(f"Unidad escalada usada: {scaled_unit:.2f} EUR")
    print(f"Importe sugerido: {capped_amount:.2f} EUR")
    if amount > max_bet:
        print("Nota: el stake introducido superaba tu limite y se recorto al maximo permitido.")
    print()


def main() -> None:
    print("=== Gestion de Bank para Apuestas ===")
    saved_settings = load_settings()
    if saved_settings:
        bank, max_percent = saved_settings
        print(f"Configuracion cargada: Bank {bank:.2f} EUR | Maximo {max_percent:.2f}%")
    else:
        bank = ask_float("Introduce tu bank total (EUR): ", min_value=0.0)
        max_percent = ask_float("Maximo por apuesta en % (ej: 4): ", min_value=0.0)
        save_settings(bank, max_percent)

    while True:
        print("Opciones:")
        print("1) Ver resumen de tipsters y unidades recomendadas")
        print("2) Calcular importe para un pick concreto")
        print("3) Cambiar bank / %")
        print("0) Salir")
        option = input("Elige una opcion: ").strip()

        if option == "1":
            print_summary(bank, max_percent)
        elif option == "2":
            calculate_pick(bank, max_percent)
        elif option == "3":
            bank = ask_float("Nuevo bank total (EUR): ", min_value=0.0)
            max_percent = ask_float("Nuevo maximo por apuesta en %: ", min_value=0.0)
            save_settings(bank, max_percent)
            print("Configuracion guardada.\n")
        elif option == "0":
            print("Hasta luego.")
            break
        else:
            print("Opcion no valida.\n")


if __name__ == "__main__":
    main()
