from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

TIPSTERS_FILE = Path(__file__).with_name("tipsters.json")
ORIGINAL_TIPSTERS_FILE = Path(__file__).with_name("tipsters_original.json")
SETTINGS_FILE = Path(__file__).with_name("settings.json")
ROUND_STEP_EUR = 1.0
BASE_UNIT_COL = "Unidad base (€)"
USUAL_STAKE_COL = "Stake habitual"
CONFIDENCE_COL = "Confianza (€)"
SCALED_UNIT_COL = "Unidad escalada (€)"
SCALED_STAKE_COL = "Stake escalado (€)"
PUBLIC_APP_MODE = True


def inject_custom_styles(mobile_mode: bool) -> None:
    app_bg = (
        "radial-gradient(circle at top left, #0f172a 0%, #111827 45%, #0b1020 100%)"
    )
    hero_bg = (
        "linear-gradient(135deg, rgba(37, 99, 235, 0.22), rgba(14, 116, 144, 0.2))"
    )
    border_color = "rgba(148, 163, 184, 0.28)"
    subtitle_color = "#cbd5e1"
    metric_bg = "rgba(15, 23, 42, 0.45)"
    text_color = "#e5e7eb"
    panel_bg = "rgba(15, 23, 42, 0.3)"

    mobile_extra = (
        """
    @media (max-width: 768px) {
        .main .block-container {
            padding-top: 0.7rem;
            padding-bottom: 1.2rem;
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }
        .hero-card {
            border-radius: 12px;
            padding: 0.85rem 0.85rem 0.7rem 0.85rem;
        }
        .hero-title { font-size: 1.02rem; }
        .hero-subtitle { font-size: 0.84rem; }
        .section-title { font-size: 0.98rem; }
        .section-help { font-size: 0.84rem; }
        .stButton > button { width: 100%; }
    }
    """
        if mobile_mode
        else ""
    )

    css = """
    <style>
    .stApp {
        background: __APP_BG__;
        color: __TEXT_COLOR__;
    }
    .main .block-container {
        max-width: 1200px;
        padding-top: 1.4rem;
        padding-bottom: 2rem;
    }
    .hero-card {
        background: __HERO_BG__;
        border: 1px solid __BORDER_COLOR__;
        border-radius: 14px;
        padding: 1rem 1.1rem 0.85rem 1.1rem;
        margin-bottom: 0.85rem;
    }
    .hero-title {
        font-size: 1.15rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .hero-subtitle {
        color: __SUBTITLE_COLOR__;
        font-size: 0.92rem;
        margin: 0;
    }
    .section-title {
        font-size: 1.06rem;
        font-weight: 700;
        margin-top: 0.3rem;
        margin-bottom: 0.1rem;
    }
    .section-help {
        color: __SUBTITLE_COLOR__;
        font-size: 0.91rem;
        margin-bottom: 0.7rem;
    }
    div[data-testid="stMetric"] {
        background: __METRIC_BG__;
        border: 1px solid __BORDER_COLOR__;
        border-radius: 12px;
        padding: 0.5rem 0.7rem;
    }
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        border: 1px solid __BORDER_COLOR__;
    }
    div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] {
        border: 1px solid __BORDER_COLOR__;
        border-radius: 12px;
        background: __PANEL_BG__;
    }
    __MOBILE_EXTRA__
    </style>
    """
    css = (
        css.replace("__APP_BG__", app_bg)
        .replace("__TEXT_COLOR__", text_color)
        .replace("__HERO_BG__", hero_bg)
        .replace("__BORDER_COLOR__", border_color)
        .replace("__SUBTITLE_COLOR__", subtitle_color)
        .replace("__METRIC_BG__", metric_bg)
        .replace("__PANEL_BG__", panel_bg)
        .replace("__MOBILE_EXTRA__", mobile_extra)
    )
    st.markdown(css, unsafe_allow_html=True)


def section_header(title: str, description: str, icon: str = "") -> None:
    title_text = f"{icon} {title}".strip()
    st.markdown(
        f"""
        <div class="section-title">{title_text}</div>
        <div class="section-help">{description}</div>
        """,
        unsafe_allow_html=True,
    )


def round_to_step(amount: float, step: float = ROUND_STEP_EUR) -> float:
    if step <= 0:
        return amount
    return round(amount / step) * step


def load_tipsters() -> list[dict]:
    if not TIPSTERS_FILE.exists():
        st.error(f"No existe `tipsters.json` en: {TIPSTERS_FILE}")
        st.stop()
    with TIPSTERS_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list) or not data:
        st.error("`tipsters.json` debe contener una lista con tipsters.")
        st.stop()
    return data


def load_saved_settings() -> tuple[float, float]:
    if not SETTINGS_FILE.exists():
        return 1000.0, 3.0
    try:
        with SETTINGS_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return float(data["bank"]), float(data["max_percent"])
    except (ValueError, TypeError, KeyError):
        return 1000.0, 3.0


def save_tipsters(tipsters: list[dict]) -> None:
    with TIPSTERS_FILE.open("w", encoding="utf-8") as f:
        json.dump(tipsters, f, ensure_ascii=True, indent=2)


def load_original_tipsters() -> list[dict]:
    if not ORIGINAL_TIPSTERS_FILE.exists():
        return []
    with ORIGINAL_TIPSTERS_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list) or not data:
        return []
    return data


def validate_tipsters(tipsters: list[dict]) -> tuple[bool, str]:
    if not tipsters:
        return False, "La tabla no puede quedarse vacia."

    names_seen: set[str] = set()
    for idx, item in enumerate(tipsters, start=1):
        name = str(item.get("name", "")).strip()
        if not name:
            return False, f"Fila {idx}: el nombre del tipster es obligatorio."
        if name.lower() in names_seen:
            return False, f"Nombre repetido detectado: {name}"
        names_seen.add(name.lower())

        try:
            base_unit = float(item.get("base_unit", 0))
            usual_stake = float(item.get("usual_stake", 0))
            confidence = float(item.get("confidence_eur", 0))
        except (ValueError, TypeError):
            return False, f"Fila {idx} ({name}): revisa valores numericos."

        if base_unit <= 0 or usual_stake <= 0 or confidence <= 0:
            return False, f"Fila {idx} ({name}): base, stake y confianza deben ser > 0."

    return True, ""


def save_settings(bank: float, max_percent: float) -> None:
    with SETTINGS_FILE.open("w", encoding="utf-8") as f:
        json.dump(
            {"bank": bank, "max_percent": max_percent}, f, ensure_ascii=True, indent=2
        )


def ensure_session_state(
    default_tipsters: list[dict], default_bank: float, default_percent: float
) -> None:
    if "tipsters_working" not in st.session_state:
        st.session_state.tipsters_working = json.loads(json.dumps(default_tipsters))
    if "bank" not in st.session_state:
        st.session_state.bank = float(default_bank)
    if "max_percent" not in st.session_state:
        st.session_state.max_percent = float(default_percent)


def build_rows(
    tipsters: list[dict], bank: float, max_percent: float
) -> tuple[list[dict], float, float]:
    max_bet = bank * (max_percent / 100.0)
    max_confidence = max(float(t["confidence_eur"]) for t in tipsters)
    scale_factor = max_bet / max_confidence if max_confidence > 0 else 1.0

    rows: list[dict] = []
    for t in tipsters:
        name = str(t["name"])
        base_unit = float(t["base_unit"])
        usual_stake = float(t["usual_stake"])
        confidence = float(t["confidence_eur"])

        scaled_confidence = round_to_step(confidence * scale_factor)
        scaled_unit = round((scaled_confidence / usual_stake), 2)
        rows.append(
            {
                "Tipster": name,
                BASE_UNIT_COL: round(base_unit, 2),
                USUAL_STAKE_COL: usual_stake,
                "Conf. original (€)": round(confidence, 2),
                SCALED_UNIT_COL: scaled_unit,
                "Stake escalado (€)": scaled_confidence,
                "Estado": "OK" if scaled_confidence <= max_bet else "REVISAR",
            }
        )

    return rows, max_bet, scale_factor


def whatsapp_text(
    rows: list[dict], bank: float, max_percent: float, max_bet: float
) -> str:
    lines: list[str] = [
        f"Para un bankroll de *{bank:.2f}€* con un limite maximo del *{max_percent:.2f}%*, tu apuesta tope absoluta es de *{max_bet:.2f}€*.",
        "",
        "Aplicando el factor de escala para mantener la jerarquia de confianza original:",
        "",
        f"TABLA STAKES ACTUALIZADA (BANK {bank:.2f}€ - MAX {max_percent:.2f}% = {max_bet:.2f}€)",
        "",
    ]
    for row in rows:
        stake_text = f"{row[USUAL_STAKE_COL]}".rstrip("0").rstrip(".")
        lines.append(f"*{row['Tipster']}*")
        lines.append(f"Unidad: {row[SCALED_UNIT_COL]:.2f}€")
        lines.append(f"Stake {stake_text} -> *{row[SCALED_STAKE_COL]:.2f}€*")
        lines.append("")
    return "\n".join(lines)


def tipsters_to_editor_rows(tipsters: list[dict]) -> list[dict]:
    return [
        {
            "Tipster": str(t["name"]),
            BASE_UNIT_COL: float(t["base_unit"]),
            USUAL_STAKE_COL: float(t["usual_stake"]),
            CONFIDENCE_COL: float(t["confidence_eur"]),
        }
        for t in tipsters
    ]


def editor_rows_to_tipsters(rows: list[dict]) -> list[dict]:
    return [
        {
            "name": str(row["Tipster"]).strip(),
            "base_unit": float(row[BASE_UNIT_COL]),
            "usual_stake": float(row[USUAL_STAKE_COL]),
            "confidence_eur": float(row[CONFIDENCE_COL]),
        }
        for row in rows
    ]


def render_config_section(
    default_bank: float, default_percent: float, mobile_mode: bool
) -> tuple[float, float]:
    section_header(
        "1) Configuracion",
        "Define tu bank actual y el porcentaje maximo por apuesta. "
        "La app usa estos dos datos para calcular tu limite de riesgo.",
        icon="⚙️",
    )
    if mobile_mode:
        bank = st.number_input(
            "Bank actual (€)", min_value=1.0, value=float(default_bank), step=10.0
        )
        max_percent = st.number_input(
            "Maximo por apuesta (%)",
            min_value=0.1,
            value=float(default_percent),
            step=0.1,
        )
        if st.button("Aplicar configuracion", use_container_width=True):
            st.session_state.bank = float(bank)
            st.session_state.max_percent = float(max_percent)
            if not PUBLIC_APP_MODE:
                save_settings(bank, max_percent)
            st.success("Configuracion aplicada")
        return bank, max_percent

    c1, c2, c3 = st.columns([1.2, 1.2, 0.8])
    with c1:
        bank = st.number_input(
            "Bank actual (€)", min_value=1.0, value=float(default_bank), step=10.0
        )
    with c2:
        max_percent = st.number_input(
            "Maximo por apuesta (%)",
            min_value=0.1,
            value=float(default_percent),
            step=0.1,
        )
    with c3:
        st.write("")
        if st.button("Aplicar", use_container_width=True):
            st.session_state.bank = float(bank)
            st.session_state.max_percent = float(max_percent)
            if not PUBLIC_APP_MODE:
                save_settings(bank, max_percent)
            st.success("Configuracion aplicada")
    return bank, max_percent


def render_tipster_editor(
    tipsters: list[dict], mobile_mode: bool
) -> tuple[list[dict], bool, bool]:
    section_header(
        "2) Editar tipsters (opcional)",
        "Aqui puedes personalizar nombre, unidad base, stake habitual y confianza de cada tipster. "
        "Los cambios se guardan en tu archivo local. "
        "La tabla original es la misma que aparece en la pagina de SoloPicks.",
        icon="🛠️",
    )
    if PUBLIC_APP_MODE:
        st.info(
            "Modo publico: los cambios se aplican solo en tu sesion y no afectan a otros usuarios."
        )
    editor_rows = tipsters_to_editor_rows(tipsters)
    editor_container = st.expander("Editar tabla de tipsters", expanded=not mobile_mode)
    with editor_container:
        edited_rows = st.data_editor(
            editor_rows,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            column_config={
                "Tipster": st.column_config.TextColumn(required=True),
                BASE_UNIT_COL: st.column_config.NumberColumn(min_value=0.01, step=0.5),
                USUAL_STAKE_COL: st.column_config.NumberColumn(
                    min_value=0.01, step=0.25
                ),
                CONFIDENCE_COL: st.column_config.NumberColumn(min_value=0.01, step=0.5),
            },
        )
    b1, b2 = st.columns(2)
    with b1:
        save_changes = st.button("Aplicar cambios de tipsters", use_container_width=True)
    with b2:
        restore_defaults = st.button("Restaurar tabla original", use_container_width=True)
    return edited_rows, save_changes, restore_defaults


def render_summary_table(
    rows: list[dict], max_bet: float, scale_factor: float, mobile_mode: bool
) -> None:
    section_header(
        "3) Tabla de stakes escalados",
        "Esta tabla ya esta adaptada a tu bank: mantiene la jerarquia de confianza entre tipsters "
        "y aplica redondeo para que sea util al apostar.",
        icon="📊",
    )
    m1, m2, m3 = st.columns(3)
    m1.metric("Apuesta tope", f"{max_bet:.2f}€")
    m2.metric("Factor escala", f"x{scale_factor:.4f}")
    m3.metric("Tipsters", f"{len(rows)}")

    if mobile_mode:
        show_cols = ["Tipster", SCALED_UNIT_COL, SCALED_STAKE_COL, "Estado"]
    else:
        show_cols = [
            "Tipster",
            USUAL_STAKE_COL,
            SCALED_UNIT_COL,
            SCALED_STAKE_COL,
            "Estado",
        ]

    table_rows = [{col: row[col] for col in show_cols} for row in rows]
    st.table(table_rows)


def render_pick_section(rows: list[dict], max_bet: float) -> None:
    section_header(
        "4) Pick concreto",
        "Selecciona tipster y stake real del pick. "
        "La app calcula el importe recomendado y lo limita a tu tope de riesgo.",
        icon="🎯",
    )
    names = [row["Tipster"] for row in rows]
    selected_name = st.selectbox("Tipster", names, index=0)
    stake_pick = st.number_input("Stake del pick", min_value=0.1, value=1.0, step=0.25)
    selected = next(row for row in rows if row["Tipster"] == selected_name)
    amount = round_to_step(selected[SCALED_UNIT_COL] * stake_pick)
    suggested = round_to_step(min(amount, max_bet))
    st.write(f"Unidad escalada: **{selected[SCALED_UNIT_COL]:.2f}€**")
    st.write(f"Importe sugerido: **{suggested:.2f}€**")
    if amount > max_bet:
        st.warning("El stake supera tu limite y se ha capado al maximo permitido.")


def render_whatsapp_section(
    rows: list[dict], bank: float, max_percent: float, max_bet: float, mobile_mode: bool
) -> None:
    section_header(
        "5) Texto para copiar/pegar",
        "Genera un resumen en formato simple para compartir por WhatsApp o Telegram.",
        icon="💬",
    )
    wa = whatsapp_text(rows, bank, max_percent, max_bet)
    st.text_area("Copiar y pegar", value=wa, height=260 if mobile_mode else 420)


def main() -> None:
    st.set_page_config(page_title="Gestion Bank Apuestas", layout="wide")
    with st.sidebar:
        st.markdown("### Vista")
        mobile_mode = st.toggle("Modo movil compacto", value=True)
    inject_custom_styles(mobile_mode)
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-title">Gestion de Bank para Apuestas</div>
            <p class="hero-subtitle">
                Controla riesgo, escala stakes automaticamente y genera resumen listo para compartir.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tipsters_base = load_tipsters()
    default_bank, default_percent = load_saved_settings()
    ensure_session_state(tipsters_base, default_bank, default_percent)
    tipsters = st.session_state.tipsters_working
    bank = float(st.session_state.bank)
    max_percent = float(st.session_state.max_percent)
    bank, max_percent = render_config_section(bank, max_percent, mobile_mode)
    st.divider()

    edited_rows, save_changes, restore_defaults = render_tipster_editor(
        tipsters, mobile_mode
    )

    if save_changes:
        updated_tipsters = editor_rows_to_tipsters(edited_rows)
        valid, error_msg = validate_tipsters(updated_tipsters)
        if not valid:
            st.error(error_msg)
        else:
            st.session_state.tipsters_working = updated_tipsters
            if not PUBLIC_APP_MODE:
                save_tipsters(updated_tipsters)
            st.success("Tipsters aplicados correctamente.")
            st.rerun()

    if restore_defaults:
        original_tipsters = load_original_tipsters()
        valid, error_msg = validate_tipsters(original_tipsters)
        if not valid:
            st.error(
                "No se pudo restaurar la configuracion original. "
                f"Detalle: {error_msg or 'tipsters_original.json no disponible o invalido.'}"
            )
        else:
            st.session_state.tipsters_working = original_tipsters
            if not PUBLIC_APP_MODE:
                save_tipsters(original_tipsters)
            st.success("Tipsters restaurados a la tabla original.")
            st.rerun()

    rows, max_bet, scale_factor = build_rows(
        st.session_state.tipsters_working,
        float(st.session_state.bank),
        float(st.session_state.max_percent),
    )
    st.divider()

    render_summary_table(rows, max_bet, scale_factor, mobile_mode)
    st.divider()

    render_pick_section(rows, max_bet)
    st.divider()

    render_whatsapp_section(
        rows,
        float(st.session_state.bank),
        float(st.session_state.max_percent),
        max_bet,
        mobile_mode,
    )


if __name__ == "__main__":
    main()
